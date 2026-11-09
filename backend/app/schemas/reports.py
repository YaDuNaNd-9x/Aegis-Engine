from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ReportSection(BaseModel):
    model_config = ConfigDict(extra="allow")

    heading: str = Field(default="Section", max_length=200)
    content: Any = ""


class ReportEvidence(BaseModel):
    model_config = ConfigDict(extra="allow")

    finding: Optional[str] = None
    source: Optional[str] = None
    page: Optional[str | int] = None
    section: Optional[str] = None
    quote: Optional[str] = None
    citation: Optional[str] = None


class ReportContent(BaseModel):
    model_config = ConfigDict(extra="allow")

    summary: Optional[str] = None
    sections: list[ReportSection] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    evidence: list[ReportEvidence | str] = Field(default_factory=list)
    citations: list[dict[str, Any] | str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class ReportRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    report_type: str = Field(default="analysis", min_length=1, max_length=100)
    source_dataset: Optional[str] = Field(default=None, max_length=255)
    content: ReportContent