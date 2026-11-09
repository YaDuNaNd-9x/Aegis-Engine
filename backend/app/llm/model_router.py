from backend.app.core.config import settings


class ModelRouter:
    """
    Routes requests between configured local models.

    Uses lightweight keyword and query-length heuristics.
    This is rule-based routing, not a trained classifier.
    """

    REASONING_KEYWORDS = [
        "analyse",
        "analyze",
        "investigate",
        "compare",
        "evaluate",
        "diagnose",
        "root cause",
        "maintenance history",
        "detailed report",
        "complex",
        "reason",
        "explain why",
        "risk assessment",
        "trend analysis",
        "anomaly",
        "correlation",
        "recommendation",
        "failure analysis",
        "predict",
        "forecast",
    ]

    def select_model(self, query: str) -> str:
        """
        Select the fast or reasoning model based on query complexity.
        """

        if not isinstance(query, str):
            raise TypeError("Query must be a string.")

        normalized_query = " ".join(query.lower().split())

        reasoning_score = sum(
            1
            for keyword in self.REASONING_KEYWORDS
            if keyword in normalized_query
        )

        if len(normalized_query.split()) > 80:
            reasoning_score += 1

        if reasoning_score >= 1:
            return settings.REASONING_MODEL

        return settings.FAST_MODEL

    def get_model_type(self, model_name: str) -> str:
        """Return the configured model category."""

        if model_name == settings.REASONING_MODEL:
            return "reasoning"

        if model_name == settings.FAST_MODEL:
            return "fast"

        if model_name == settings.EMBEDDING_MODEL:
            return "embedding"

        return "custom"

    def get_routing_details(self, query: str) -> dict:
        """Return the selected model and routing explanation."""

        selected_model = self.select_model(query)
        model_type = self.get_model_type(selected_model)

        return {
            "selected_model": selected_model,
            "model_type": model_type,
            "reason": (
                "Query matched reasoning criteria."
                if model_type == "reasoning"
                else "Query routed to the fast model."
            ),
        }


# Shared router instance
model_router = ModelRouter()