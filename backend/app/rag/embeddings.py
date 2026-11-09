import math

from backend.app.llm.ollama_client import ollama_client


class EmbeddingService:
    """
    Generate local document and query embeddings using Ollama.
    """

    @staticmethod
    def _validate_vectors(vectors, expected_count: int):
        if not isinstance(vectors, list):
            raise ValueError("Embedding service returned invalid data.")

        if len(vectors) != expected_count:
            raise ValueError(
                "Embedding count does not match input count."
            )

        for vector in vectors:
            if not isinstance(vector, list) or not vector:
                raise ValueError("An embedding vector is empty or invalid.")

            if not all(
                isinstance(value, (int, float))
                and math.isfinite(value)
                for value in vector
            ):
                raise ValueError("Embedding contains invalid numeric values.")

    async def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        if not texts:
            return []

        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError("Document texts cannot be empty.")

        vectors = await ollama_client.embed(texts)

        self._validate_vectors(vectors, len(texts))

        return vectors

    async def embed_query(
        self,
        query: str,
    ) -> list[float]:

        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        vectors = await ollama_client.embed(query)

        self._validate_vectors(vectors, 1)

        return vectors[0]


embedding_service = EmbeddingService()