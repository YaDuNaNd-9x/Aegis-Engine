from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
    )


class ChatResponse(BaseModel):
    response: str | None = None

    selected_model: str | None = None
    model_type: str | None = None

    status: str = "unknown"
    error: str | None = None

    execution_steps: list[str] = Field(default_factory=list)
    citations: list[dict] = Field(default_factory=list)