
from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):

    instruction: str = Field(
        ...,
        min_length=5,
        max_length=3000
    )


class AnalysisResponse(BaseModel):

    status: str

    result: dict | None = None

    error: str | None = None

    explanation: str | None = None

    execution_steps: list[str] = Field(
        default_factory=list
    )
