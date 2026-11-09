from pathlib import Path

from backend.app.rag.ingestion import extract_document
from backend.app.rag.chunking import chunk_document
from backend.app.rag.retriever import retriever


class DocumentService:

    async def process_document(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> dict:
        """
        Complete document ingestion pipeline:
        extraction -> cleaning -> chunking -> embeddings -> indexing.
        """

        filename = Path(filename).name

        if not filename:
            raise ValueError("A valid filename is required.")

        pages = extract_document(
            file_bytes,
            filename,
        )

        chunks = chunk_document(
            pages,
            filename,
            chunk_size=1200,
            overlap=200,
        )

        if not chunks:
            raise ValueError(
                "Document did not produce any searchable text."
            )

        stored_count = await retriever.add_documents(chunks)

        if stored_count == 0:
            raise ValueError(
                "No document chunks could be stored."
            )

        page_numbers = {
            page.get("page")
            for page in pages
            if page.get("page") is not None
        }

        extraction_methods = sorted({
            page.get("extraction_method", "native")
            for page in pages
        })

        return {
            "filename": filename,
            "pages_extracted": len(page_numbers) or len(pages),
            "chunks_created": len(chunks),
            "chunks_stored": stored_count,
            "extraction_methods": extraction_methods,
            "status": "indexed",
        }


document_service = DocumentService()