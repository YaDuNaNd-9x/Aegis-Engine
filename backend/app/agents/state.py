from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    user_query: str

    task_type: str
    selected_model: str
    model_type: str

    requires_rag: bool
    requires_analysis: bool

    csv_bytes: bytes
    csv_filename: str

    retrieved_documents: list[dict[str, Any]]
    citations: list[dict[str, Any]]

    response: str
    analysis_result: dict[str, Any]
    analysis_explanation: str

    status: str
    error: str | None

    execution_steps: list[str]