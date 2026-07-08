from typing import Any

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routes import ai, assets, graph, imports, replay
from app.core.database import get_db
from app.models import App, CanonicalPage, PageEdge

app = FastAPI(title="App Relation Backend", version="0.1.0")

# Enable CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/queryAppGraph/{app_name}")
def query_app_graph(app_name: str, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Query page graph by app name, returns a recursive tree structure."""
    # Find the app by name
    stmt = select(App).where(App.app_name == app_name)
    app_record = db.scalar(stmt)
    if not app_record:
        raise HTTPException(status_code=404, detail=f"App '{app_name}' not found")

    # Get all canonical pages for this app
    pages = list(db.scalars(
        select(CanonicalPage).where(CanonicalPage.app_id == app_record.app_id)
    ))

    if not pages:
        return []

    # Build page lookup with sequential IDs
    id_counter = [0]
    page_map: dict[str, dict[str, Any]] = {}
    for page in pages:
        id_counter[0] += 1
        page_map[str(page.canonical_page_id)] = {
            "id": id_counter[0],
            "page_title": page.display_name,
            "page_text": "",  # will be filled from page instances later
            "image_url": "",
            "page_url": "",
            "ai_recursive": False,  # default; will be filled from page instances
            "page_info": {
                "page_type": page.page_type,
                "structure_hash": page.primary_structure_hash,
                "review_status": page.review_status,
            },
            "children": [],
            "_canonical_id": str(page.canonical_page_id),
        }

    # Try to fill page_text and page_url from page instances
    from app.models import PageInstance
    instances = list(db.scalars(
        select(PageInstance).where(PageInstance.app_id == app_record.app_id)
    ))
    for inst in instances:
        cid = str(inst.canonical_page_id)
        if cid in page_map:
            if inst.ai_summary and not page_map[cid]["page_text"]:
                page_map[cid]["page_text"] = inst.ai_summary
            if inst.page_title:
                page_map[cid]["page_url"] = f"/{inst.page_type}/{inst.page_title}"
            page_map[cid]["ai_recursive"] = bool(inst.ai_recursive)

    # Get edges to build the tree
    edges = list(db.scalars(
        select(PageEdge).where(
            PageEdge.app_id == app_record.app_id,
            PageEdge.from_canonical_page_id.is_not(None),
            PageEdge.to_canonical_page_id.is_not(None),
        )
    ))

    # Build children relationships with widget_description
    # widget_description is stored on each child node — it represents
    # the widget on the parent that was clicked to enter this child
    child_parent_map: dict[str, list[str]] = {}
    all_children: set[str] = set()
    for edge in edges:
        parent_id = str(edge.from_canonical_page_id)
        child_id = str(edge.to_canonical_page_id)
        if parent_id in page_map and child_id in page_map:
            child_parent_map.setdefault(parent_id, []).append(child_id)
            all_children.add(child_id)
            # Attach widget_description to the child node
            if edge.widget_description:
                page_map[child_id]["widget_description"] = edge.widget_description

    # Find root nodes (pages that are not children of any other page)
    root_ids = [pid for pid in page_map if pid not in all_children]

    # Attach children
    for parent_id, child_ids in child_parent_map.items():
        if parent_id in page_map:
            page_map[parent_id]["children"] = [page_map[cid] for cid in child_ids if cid in page_map]

    # Build result tree from roots
    result = []
    for root_id in root_ids:
        node = page_map[root_id]
        node.pop("_canonical_id", None)
        result.append(node)

    # Also clean up _canonical_id from all nodes (recursive)
    def clean_node(node):
        node.pop("_canonical_id", None)
        for child in node.get("children", []):
            clean_node(child)

    for node in result:
        clean_node(node)

    return result


app.include_router(imports.router, prefix="/api/imports", tags=["imports"])
app.include_router(graph.router, prefix="/api/graph", tags=["graph"])
app.include_router(assets.router, prefix="/api/assets", tags=["assets"])
app.include_router(replay.router, prefix="/api/replay", tags=["replay"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
