
def test_agent_module_imports():

    from backend.app.agents import graph
    from backend.app.agents import state
    from backend.app.agents import nodes

    assert graph is not None
    assert state is not None
    assert nodes is not None


def test_llm_client_module_imports():

    from backend.app.llm import ollama_client

    assert ollama_client is not None


def test_rag_modules_import():

    from backend.app.rag import (
        ingestion,
        chunking,
        embeddings,
        retriever,
        citations,
    )

    assert ingestion is not None
    assert chunking is not None
    assert embeddings is not None
    assert retriever is not None
    assert citations is not None


def test_analysis_service_imports():

    from backend.app.services.analysis_service import (
        analysis_service,
    )

    assert analysis_service is not None
