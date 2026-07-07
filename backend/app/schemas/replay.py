from pydantic import BaseModel, Field


class ReplayAnalyzeRequest(BaseModel):
    urls: list[str] = Field(default_factory=list)


class ReplayStep(BaseModel):
    url: str
    matched_keywords: list[str]
    possible_page_types: list[str]
    confidence: float


class ReplayAnalyzeResponse(BaseModel):
    steps: list[ReplayStep]
    summary: str

