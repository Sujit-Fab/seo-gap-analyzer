"""Pydantic models — the request/response contracts for the API."""

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """What a client sends us to analyze."""

    content: str = Field(..., min_length=20, description="The page/article content to analyze")
    target_keyword: str = Field(..., min_length=2, description="The keyword this content should rank for")


class ContentGap(BaseModel):
    """A single identified gap between the content and what ranks well for the keyword."""

    topic: str = Field(..., description="The missing subtopic or angle")
    why_it_matters: str = Field(..., description="Why covering this would help rankings/relevance")
    priority: str = Field(..., description="high | medium | low")


class AnalyzeResponse(BaseModel):
    """What we return after analysis."""

    target_keyword: str
    overall_assessment: str
    gaps: list[ContentGap]
    suggested_additions: list[str]
    analysis_id: str
