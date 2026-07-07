from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import CanonicalPage, PageEdge
from app.schemas.graph import AppGraphResponse, GraphEdge, GraphNode

router = APIRouter()


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
        )
        for edge in edges
        if edge.from_canonical_page_id and edge.to_canonical_page_id
    ]
    return AppGraphResponse(app_id=app_id, nodes=nodes, edges=graph_edges)

