from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import CanonicalPage, PageEdge, PageInstance
from app.schemas.graph import AppGraphResponse, GraphEdge, GraphNode

router = APIRouter()


class PageReviewRequest(BaseModel):
    backend_id: int | str | None = None
    node_id: str = ""
    page_title: str = ""
    page_text: str = ""
    page_url: str = ""
    image_url: str = ""
    image_urls: list[str] = Field(default_factory=list)
    ai_inference: dict[str, Any] = Field(default_factory=dict)
    ai_recursive: bool = False
    widget_description: str = ""
    review_status: str = "edited"
    review_note: str = ""


@router.get("/{app_id}", response_model=AppGraphResponse)
def get_app_graph(app_id: UUID, db: Session = Depends(get_db)) -> AppGraphResponse:
    pages = list(db.scalars(select(CanonicalPage).where(CanonicalPage.app_id == app_id)))
    if not pages:
        raise HTTPException(status_code=404, detail="No graph data found for app.")

    edges = list(
        db.scalars(
            select(PageEdge).where(
                PageEdge.app_id == app_id,
                PageEdge.from_canonical_page_id.is_not(None),
                PageEdge.to_canonical_page_id.is_not(None),
            )
        )
    )
    nodes = [
        GraphNode(
            id=page.canonical_page_id,
            key=page.canonical_page_key,
            label=page.display_name,
            page_type=page.page_type,
            instance_count=page.instance_count,
            structure_hash=page.primary_structure_hash,
            screenshot_asset_id=page.representative_asset_id,
        )
        for page in pages
    ]
    graph_edges = [
        GraphEdge(
            id=edge.edge_id,
            source=edge.from_canonical_page_id,
            target=edge.to_canonical_page_id,
            label=edge.label,
            action_type=edge.action_type,
            confidence=float(edge.confidence) if edge.confidence is not None else None,
            widget_description=edge.widget_description,
        )
        for edge in edges
        if edge.from_canonical_page_id and edge.to_canonical_page_id
    ]
    return AppGraphResponse(app_id=app_id, nodes=nodes, edges=graph_edges)


@router.post("/pages/review")
@router.post("/page-review")
def save_page_review(request: PageReviewRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Save human review edits for a graph page.

    Demo graph nodes may use numeric ids, while persisted pages use UUIDs.
    If no database page can be resolved, the endpoint still returns normalized
    review data so the frontend can preserve the edit locally for demo review.
    """
    canonical_page = _find_canonical_page(request, db)
    if canonical_page:
        if request.page_title:
            canonical_page.display_name = request.page_title
        canonical_page.review_status = request.review_status or "edited"

        latest_instance = db.scalar(
            select(PageInstance)
            .where(PageInstance.canonical_page_id == canonical_page.canonical_page_id)
            .order_by(PageInstance.created_at.desc())
        )
        if latest_instance:
            latest_instance.page_title = request.page_title or latest_instance.page_title
            latest_instance.ai_summary = request.page_text
            latest_instance.inferred_purpose = request.ai_inference.get("reason") or latest_instance.inferred_purpose
            latest_instance.ai_recursive = request.ai_recursive
            raw_payload = latest_instance.raw_ai_payload or {}
            raw_payload["human_review"] = {
                "ai_inference": request.ai_inference,
                "image_urls": request.image_urls,
                "review_note": request.review_note,
                "review_status": request.review_status,
                "widget_description": request.widget_description,
            }
            latest_instance.raw_ai_payload = raw_payload
        db.commit()

    image_urls = _dedupe_images(request.image_url, request.image_urls)
    return {
        "nodeId": request.node_id,
        "backend_id": request.backend_id,
        "page_title": request.page_title,
        "page_text": request.page_text,
        "page_url": request.page_url,
        "image_url": image_urls[0] if image_urls else "",
        "image_urls": image_urls,
        "ai_inference": request.ai_inference,
        "ai_recursive": request.ai_recursive,
        "widget_description": request.widget_description,
        "review_status": request.review_status or "edited",
        "review_note": request.review_note,
        "persisted": bool(canonical_page),
    }


def _find_canonical_page(request: PageReviewRequest, db: Session) -> CanonicalPage | None:
    candidates = [
        request.backend_id,
        request.node_id.replace("page-", "") if request.node_id.startswith("page-") else "",
    ]
    for value in candidates:
        try:
            page_id = UUID(str(value))
        except (TypeError, ValueError):
            continue
        page = db.get(CanonicalPage, page_id)
        if page:
            return page
    return None


def _dedupe_images(image_url: str, image_urls: list[str]) -> list[str]:
    values = [image_url, *image_urls]
    return list(dict.fromkeys([str(value).strip() for value in values if str(value).strip()]))
