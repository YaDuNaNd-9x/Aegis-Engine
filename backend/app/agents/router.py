from backend.app.llm.model_router import model_router


ANALYSIS_KEYWORDS = (
    "analyze",
    "analysis",
    "analyse",
    "calculate",
    "calculation",
    "csv",
    "spreadsheet",
    "dataset",
    "data file",
    "machine readings",
    "sensor readings",
    "average",
    "maximum",
    "minimum",
    "correlation",
    "statistics",
    "statistical",
    "trend",
    "outlier",
)

RAG_KEYWORDS = (
    "according to the documents",
    "according to the manual",
    "according to the sop",
    "uploaded document",
    "knowledge base",
    "maintenance procedure",
    "maintenance sop",
    "safety procedure",
    "what does the manual say",
    "what do the documents say",
    "document evidence",
    "in the uploaded files",
    "from the documents",
    "from the manual",
)


class AgentRouter:

    def classify(self, query: str, has_csv: bool = False) -> dict:
        normalized_query = query.lower().strip()

        if has_csv:
            task_type = "analysis"
        elif any(keyword in normalized_query for keyword in ANALYSIS_KEYWORDS):
            task_type = "analysis"
        elif any(keyword in normalized_query for keyword in RAG_KEYWORDS):
            task_type = "document_question"
        else:
            task_type = "general"

        selected_model = model_router.select_model(query)

        model_type = (
            model_router.get_model_type(selected_model)
            if hasattr(model_router, "get_model_type")
            else "reasoning"
        )

        return {
            "task_type": task_type,
            "requires_rag": task_type == "document_question",
            "requires_analysis": task_type == "analysis",
            "selected_model": selected_model,
            "model_type": model_type,
        }


agent_router = AgentRouter()