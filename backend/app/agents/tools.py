from backend.app.services.analysis_service import analysis_service
from backend.app.rag.retriever import retriever


async def retrieve_documents(
    query: str,
    top_k: int = 5,
) -> list[dict]:
    """
    Retrieve relevant documents from the existing hybrid RAG system.
    """
    results = await retriever.search(query, top_k=top_k)
    return results or []


async def analyze_csv(
    instruction: str,
    csv_bytes: bytes,
) -> dict:
    """
    Execute CSV analysis through the existing restricted Docker sandbox.
    """
    if not csv_bytes:
        raise ValueError("No CSV file was provided.")

    result = await analysis_service.analyze(
        instruction=instruction,
        csv_bytes=csv_bytes,
    )

    if result.get("status") != "success":
        raise RuntimeError(
            result.get("error") or "CSV analysis failed."
        )

    return result