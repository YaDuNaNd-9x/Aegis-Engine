import asyncio
import hashlib
import re

import chromadb
from rank_bm25 import BM25Okapi

from backend.app.core.config import settings
from backend.app.rag.embeddings import embedding_service
from backend.app.rag.citations import format_citation


class HybridRetriever:

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY
        )

        self.collection = self.client.get_or_create_collection(
            name="industrial_knowledge",
            metadata={"hnsw:space": "cosine"},
        )

        self._bm25 = None
        self._bm25_records = []
        self._bm25_lock = asyncio.Lock()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text.lower())

    async def _rebuild_bm25(self):
        """
        Rebuild the BM25 index from ChromaDB.

        Store IDs, documents and metadata together so that keyword
        rankings cannot accidentally point to different records.
        """

        async with self._bm25_lock:
            records = await asyncio.to_thread(
                self.collection.get,
                include=["documents", "metadatas"],
            )

            ids = records.get("ids") or []
            documents = records.get("documents") or []
            metadatas = records.get("metadatas") or []

            if not documents:
                self._bm25 = None
                self._bm25_records = []
                return

            self._bm25_records = [
                {
                    "id": ids[index],
                    "text": documents[index],
                    "metadata": metadatas[index] or {},
                }
                for index in range(len(documents))
            ]

            tokenized_documents = [
                self._tokenize(document)
                for document in documents
            ]

            self._bm25 = (
                BM25Okapi(tokenized_documents)
                if any(tokenized_documents)
                else None
            )

    async def add_documents(self, chunks: list[dict]) -> int:
        """
        Embed and store document chunks in persistent ChromaDB.
        """

        if not chunks:
            return 0

        texts = [
            chunk["text"].strip()
            for chunk in chunks
            if chunk.get("text", "").strip()
        ]

        valid_chunks = [
            chunk
            for chunk in chunks
            if chunk.get("text", "").strip()
        ]

        if not texts:
            return 0

        vectors = await embedding_service.embed_documents(texts)

        ids = []
        metadatas = []

        for chunk in valid_chunks:
            metadata = chunk.get("metadata", {})

            source = str(metadata.get("source", "unknown"))
            page = metadata.get("page")
            chunk_index = metadata.get("chunk_index", 0)

            # Stable identity prevents duplicate chunks on re-upload.
            identity = (
                f"{source}|{page}|{chunk_index}|{chunk['text']}"
            )

            document_id = hashlib.sha256(
                identity.encode("utf-8")
            ).hexdigest()

            ids.append(document_id)

            stored_metadata = {
                str(key): (
                    str(value)
                    if value is not None
                    else ""
                )
                for key, value in metadata.items()
            }

            metadatas.append(stored_metadata)

        await asyncio.to_thread(
            self.collection.upsert,
            ids=ids,
            documents=texts,
            embeddings=vectors,
            metadatas=metadatas,
        )

        await self._rebuild_bm25()

        return len(texts)

    async def vector_search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:

        count = await asyncio.to_thread(self.collection.count)

        if count == 0:
            return []

        query_vector = await embedding_service.embed_query(query)

        results = await asyncio.to_thread(
            self.collection.query,
            query_embeddings=[query_vector],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )

        output = []

        result_ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for index, document in enumerate(documents):
            output.append({
                "id": result_ids[index],
                "text": document,
                "metadata": metadatas[index] or {},
                "distance": float(distances[index]),
            })

        return output

    async def keyword_search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:

        if self._bm25 is None:
            await self._rebuild_bm25()

        if self._bm25 is None:
            return []

        query_tokens = self._tokenize(query)

        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )

        output = []

        for index in ranked_indices[:top_k]:
            score = float(scores[index])

            if score <= 0:
                continue

            record = self._bm25_records[index]

            output.append({
                "id": record["id"],
                "text": record["text"],
                "metadata": record["metadata"],
                "score": score,
            })

        return output

    def rerank_results(
        self,
        query: str,
        results: list[dict],
    ) -> list[dict]:
        """
        Lightweight local reranking using query-term coverage.

        This is a deterministic lexical reranker, not a neural
        cross-encoder. It boosts passages that cover more of the
        important query terms after hybrid retrieval.
        """

        query_tokens = set(self._tokenize(query))

        if not query_tokens:
            return results

        for result in results:
            document_tokens = set(
                self._tokenize(result["text"])
            )

            overlap = len(query_tokens & document_tokens)

            coverage = overlap / len(query_tokens)

            original_score = float(result.get("score", 0.0))

            result["hybrid_score"] = original_score
            result["rerank_score"] = (
                original_score + (0.05 * coverage)
            )

        return sorted(
            results,
            key=lambda item: item["rerank_score"],
            reverse=True,
        )

    async def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Hybrid retrieval:
        1. Vector search.
        2. BM25 keyword search.
        3. Reciprocal Rank Fusion.
        4. Local lexical reranking.
        5. Citation formatting.
        """

        if not query or not query.strip():
            return []

        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        count = await asyncio.to_thread(self.collection.count)

        if count == 0:
            return []

        retrieval_k = min(max(top_k * 3, 10), count)

        vector_results, keyword_results = await asyncio.gather(
            self.vector_search(query, retrieval_k),
            self.keyword_search(query, retrieval_k),
        )

        combined = {}
        rrf_constant = 60

        for results in (vector_results, keyword_results):
            for rank, result in enumerate(results, start=1):
                key = result["id"]

                if key not in combined:
                    combined[key] = {
                        "id": key,
                        "text": result["text"],
                        "metadata": result["metadata"],
                        "score": 0.0,
                    }

                combined[key]["score"] += (
                    1.0 / (rrf_constant + rank)
                )

        ranked = sorted(
            combined.values(),
            key=lambda item: item["score"],
            reverse=True,
        )

        reranked = self.rerank_results(query, ranked)

        output = []

        for item in reranked[:top_k]:
            output.append({
                "text": item["text"],
                "citation": format_citation(item["metadata"]),
                "metadata": item["metadata"],
                "relevance_score": round(
                    item["rerank_score"],
                    6,
                ),
            })

        return output


# Shared retriever instance
retriever = HybridRetriever()