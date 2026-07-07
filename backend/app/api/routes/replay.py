from fastapi import APIRouter

from app.schemas.replay import ReplayAnalyzeRequest, ReplayAnalyzeResponse
from app.services.replay import analyze_urls

router = APIRouter()


@router.post("/analyze", response_model=ReplayAnalyzeResponse)
def analyze_replay(request: ReplayAnalyzeRequest) -> ReplayAnalyzeResponse:
    steps, summary = analyze_urls(request.urls)
    return ReplayAnalyzeResponse(steps=steps, summary=summary)

