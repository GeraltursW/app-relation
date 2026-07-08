from uuid import UUID

from pydantic import BaseModel


class GraphNode(BaseModel):
    id: UUID
    key: str
    label: str
    page_type: str
    instance_count: int
    structure_hash: str | None = None
    screenshot_asset_id: UUID | None = None


class GraphEdge(BaseModel):
    id: UUID
    source: UUID
    target: UUID
    label: str
    action_type: str
    confidence: float | None = None
    widget_description: str | None = None


class AppGraphResponse(BaseModel):
    app_id: UUID
    nodes: list[GraphNode]
    edges: list[GraphEdge]
