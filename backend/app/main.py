import json
import hashlib
import shutil
from pathlib import Path
from typing import Annotated, Any
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.api.routes import ai, assets, graph, imports, replay
from app.core.database import get_db
from app.models import App, CanonicalPage, EmbeddingRecord, PageEdge, PageInstance, PageWidget, Scan

app = FastAPI(title="App Relation Backend", version="0.1.0")
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "storage" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ACTION_KEYS = ("popupAction", "stateAction", "externalAction", "pageNaviAction")


def _empty_action() -> dict[str, list[dict[str, Any]]]:
    return {key: [] for key in ACTION_KEYS}


def _normalize_action(value: Any) -> dict[str, list[dict[str, Any]]]:
    if value is None:
        return _empty_action()
    if isinstance(value, list):
        normalized = _empty_action()
        legacy_groups = {
            "overlay": "popupAction",
            "popup": "popupAction",
            "state_change": "stateAction",
            "state": "stateAction",
            "external": "externalAction",
            "navigate": "pageNaviAction",
            "navigation": "pageNaviAction",
        }
        for item in value:
            if not isinstance(item, dict):
                raise ValueError("legacy page_actions must contain objects")
            group_key = legacy_groups.get(str(item.get("effect_type") or "").lower(), "stateAction")
            normalized[group_key].append(item)
        return normalized
    if not isinstance(value, dict):
        raise ValueError("action must be an object")
    unexpected = set(value) - set(ACTION_KEYS)
    if unexpected:
        raise ValueError(f"unsupported action fields: {', '.join(sorted(unexpected))}")
    normalized = _empty_action()
    for key in ACTION_KEYS:
        items = value.get(key, [])
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            raise ValueError(f"action.{key} must be an array of objects")
        normalized[key] = items
    return normalized

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
def query_app_graph(app_name: str, db: Session = Depends(get_db)) -> dict[str, list[dict[str, Any]]]:
    """Query page graph by app name, returns a recursive tree structure."""
    # Find the app by name
    stmt = select(App).where(func.lower(App.app_name) == app_name.lower())
    app_record = db.scalar(stmt)
    if not app_record:
        raise HTTPException(status_code=404, detail=f"App '{app_name}' not found")

    # Get all canonical pages for this app
    pages = list(db.scalars(
        select(CanonicalPage).where(CanonicalPage.app_id == app_record.app_id)
    ))

    if not pages:
        return {"roots": [], "orphan_pages": []}

    # Build page lookup with sequential IDs
    id_counter = [0]
    page_map: dict[str, dict[str, Any]] = {}
    for page in pages:
        id_counter[0] += 1
        page_map[str(page.canonical_page_id)] = {
            "id": id_counter[0],
            "page_id": page.page_hash_id,
            "page_title": page.display_name,
            "page_text": "",  # will be filled from page instances later
            "images": [],
            "page_url": "",
            "ai_recursive": False,  # default; will be filled from page instances
            "action": _empty_action(),
            "page_info": {
                "page_type": page.page_type,
                "structure_hash": page.primary_structure_hash,
                "review_status": page.review_status,
            },
            "children": [],
            "_canonical_id": str(page.canonical_page_id),
            "_has_persisted_action": False,
        }

    # Try to fill page_text and page_url from page instances
    instances = list(db.scalars(
        select(PageInstance).where(PageInstance.app_id == app_record.app_id)
    ))
    for inst in instances:
        cid = str(inst.canonical_page_id)
        if cid in page_map:
            if inst.ai_summary and not page_map[cid]["page_text"]:
                page_map[cid]["page_text"] = inst.ai_summary
            raw_payload = inst.raw_ai_payload or {}
            page_map[cid]["page_url"] = inst.page_url or raw_payload.get("page_url") or page_map[cid]["page_url"]
            page_map[cid]["images"] = list(inst.images or raw_payload.get("images") or [])
            page_map[cid]["ai_inference"] = inst.ai_inference or raw_payload.get("ai_inference") or {}
            stored_action = inst.action if inst.action is not None else (
                raw_payload.get("action")
                if raw_payload.get("action") is not None
                else raw_payload.get("page_actions")
            )
            if stored_action is not None:
                try:
                    page_map[cid]["action"] = _normalize_action(stored_action)
                    page_map[cid]["_has_persisted_action"] = True
                except ValueError:
                    page_map[cid]["action"] = _empty_action()
            page_map[cid]["page_info"].update(raw_payload.get("page_info") or {})
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
            if not page_map[parent_id]["_has_persisted_action"]:
                page_map[parent_id]["action"]["pageNaviAction"].append({
                    "id": str(edge.edge_id),
                    "label": edge.widget_description or edge.label,
                    "action_type": edge.action_type or "tap",
                    "description": edge.widget_description or edge.label,
                    "target_page_id": page_map[child_id]["page_id"],
                    "target_page_title": page_map[child_id]["page_title"],
                })

    # Find root nodes (pages that are not children of any other page)
    root_ids = [pid for pid in page_map if pid not in all_children]

    # Attach children
    for parent_id, child_ids in child_parent_map.items():
        if parent_id in page_map:
            page_map[parent_id]["children"] = [page_map[cid] for cid in child_ids if cid in page_map]

    # Build result tree from roots
    result = []
    orphan_pages = []
    for root_id in root_ids:
        node = page_map[root_id]
        node.pop("_canonical_id", None)
        if node.get("page_info", {}).get("is_orphan") or node.get("page_info", {}).get("page_type") == "orphan":
            orphan_pages.append(node)
        else:
            result.append(node)

    # Also clean up _canonical_id from all nodes (recursive)
    def clean_node(node):
        node.pop("_canonical_id", None)
        node.pop("_has_persisted_action", None)
        for child in node.get("children", []):
            clean_node(child)

    for node in [*result, *orphan_pages]:
        clean_node(node)

    return {"roots": result, "orphan_pages": orphan_pages}


@app.get("/app_list")
def app_list(db: Session = Depends(get_db)) -> dict[str, Any]:
    """List available applications and their canonical graph node counts."""
    rows = db.execute(
        select(App.app_name, func.count(CanonicalPage.canonical_page_id))
        .outerjoin(CanonicalPage, CanonicalPage.app_id == App.app_id)
        .group_by(App.app_id, App.app_name, App.market_rank)
        .order_by(App.market_rank.asc().nullslast(), App.app_name.asc())
    ).all()
    return {
        "statue": "success",
        "apps": [
            {"app_name": app_name, "count": int(page_count)}
            for app_name, page_count in rows
        ],
    }


class CreateOrphanNodeRequest(BaseModel):
    app_name: str
    page_url: str


class MoveNodeRequest(BaseModel):
    page_id: str
    new_parent_id: str | None = None
    new_paremy_id: str | None = None


class DeleteNodeRequest(BaseModel):
    id: str


@app.post("/delete_node")
def delete_node(
    request: DeleteNodeRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    page_id = request.id.strip()
    if not page_id:
        raise HTTPException(status_code=422, detail="id is required")

    page = db.scalar(select(CanonicalPage).where(CanonicalPage.page_hash_id == page_id))
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    instance_ids = list(
        db.scalars(
            select(PageInstance.page_instance_id).where(
                PageInstance.canonical_page_id == page.canonical_page_id
            )
        )
    )
    edge_filters = [
        PageEdge.from_canonical_page_id == page.canonical_page_id,
        PageEdge.to_canonical_page_id == page.canonical_page_id,
    ]
    if instance_ids:
        edge_filters.extend(
            [
                PageEdge.from_page_instance_id.in_(instance_ids),
                PageEdge.to_page_instance_id.in_(instance_ids),
            ]
        )
    db.execute(delete(PageEdge).where(or_(*edge_filters)))
    db.execute(delete(PageWidget).where(PageWidget.canonical_page_id == page.canonical_page_id))
    if instance_ids:
        db.execute(delete(PageWidget).where(PageWidget.page_instance_id.in_(instance_ids)))
    db.execute(
        delete(EmbeddingRecord).where(
            EmbeddingRecord.owner_id.in_([page.canonical_page_id, *instance_ids])
        )
    )
    db.execute(delete(PageInstance).where(PageInstance.canonical_page_id == page.canonical_page_id))
    db.delete(page)
    db.commit()
    return {"statue": "success", "deleted": True, "page_id": page_id}


@app.post("/move_node")
def move_node(
    request: MoveNodeRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    new_parent_page_id = request.new_parent_id or request.new_paremy_id
    if not new_parent_page_id:
        raise HTTPException(status_code=422, detail="new_parent_id is required")

    page = db.scalar(select(CanonicalPage).where(CanonicalPage.page_hash_id == request.page_id))
    new_parent = db.scalar(
        select(CanonicalPage).where(CanonicalPage.page_hash_id == new_parent_page_id)
    )
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    if not new_parent:
        raise HTTPException(status_code=404, detail="New parent page not found")
    if page.canonical_page_id == new_parent.canonical_page_id:
        raise HTTPException(status_code=409, detail="A node cannot be its own parent")
    if page.app_id != new_parent.app_id:
        raise HTTPException(status_code=409, detail="Nodes must belong to the same app")
    if _is_descendant(db, page, new_parent):
        raise HTTPException(status_code=409, detail="Cannot move a node under its descendant")

    incoming_edges = list(
        db.scalars(select(PageEdge).where(PageEdge.to_canonical_page_id == page.canonical_page_id))
    )
    if any(edge.from_canonical_page_id == new_parent.canonical_page_id for edge in incoming_edges):
        return {
            "statue": "success",
            "moved": False,
            "page_id": page.page_hash_id,
            "new_parent_id": new_parent.page_hash_id,
        }

    for edge in incoming_edges:
        db.delete(edge)

    scan = db.scalar(
        select(Scan).where(Scan.app_id == page.app_id).order_by(Scan.started_at.desc())
    )
    if not scan:
        raise HTTPException(status_code=409, detail="No scan record is available for this app")

    db.add(
        PageEdge(
            scan_id=scan.scan_id,
            app_id=page.app_id,
            from_canonical_page_id=new_parent.canonical_page_id,
            to_canonical_page_id=page.canonical_page_id,
            action_type="navigate",
            label="人工调整归类",
            widget_description="人工调整归类",
            status="confirmed",
            raw_action_payload={"source": "manual_drag"},
        )
    )
    page.review_status = "edited"
    db.commit()
    return {
        "statue": "success",
        "moved": True,
        "page_id": page.page_hash_id,
        "new_parent_id": new_parent.page_hash_id,
    }


def _is_descendant(db: Session, page: CanonicalPage, candidate_parent: CanonicalPage) -> bool:
    edges = list(
        db.scalars(
            select(PageEdge).where(
                PageEdge.app_id == page.app_id,
                PageEdge.from_canonical_page_id.is_not(None),
                PageEdge.to_canonical_page_id.is_not(None),
            )
        )
    )
    children: dict[Any, list[Any]] = {}
    for edge in edges:
        children.setdefault(edge.from_canonical_page_id, []).append(edge.to_canonical_page_id)

    pending = list(children.get(page.canonical_page_id, []))
    visited = set()
    while pending:
        node_id = pending.pop()
        if node_id == candidate_parent.canonical_page_id:
            return True
        if node_id in visited:
            continue
        visited.add(node_id)
        pending.extend(children.get(node_id, []))
    return False


@app.post("/create_orphan_node")
def create_orphan_node(
    request: CreateOrphanNodeRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    app_name = request.app_name.strip()
    page_url = request.page_url.strip()
    if not app_name or not page_url:
        raise HTTPException(status_code=422, detail="app_name and page_url are required")

    app_record = db.scalar(select(App).where(func.lower(App.app_name) == app_name.lower()))
    if not app_record:
        raise HTTPException(status_code=404, detail=f"App '{app_name}' not found")

    existing_instance = db.scalar(
        select(PageInstance)
        .where(PageInstance.app_id == app_record.app_id, PageInstance.page_url == page_url)
        .order_by(PageInstance.created_at.desc())
    )
    if existing_instance and existing_instance.canonical_page_id:
        existing_page = db.get(CanonicalPage, existing_instance.canonical_page_id)
        if existing_page and existing_page.page_type == "orphan":
            return {
                "statue": "success",
                "created": False,
                "node": _orphan_node_payload(existing_page, existing_instance),
            }
        if existing_page:
            raise HTTPException(status_code=409, detail="This URL already belongs to the main graph")

    digest = hashlib.sha256(f"orphan:{app_record.app_id}:{page_url}".encode("utf-8")).hexdigest()
    canonical = CanonicalPage(
        app_id=app_record.app_id,
        canonical_page_key=f"orphan-{digest[:12]}",
        page_hash_id=digest[:32],
        display_name="待探索页面",
        page_type="orphan",
        primary_route_hash=hashlib.sha256(page_url.encode("utf-8")).hexdigest(),
        instance_count=1,
        review_status="draft",
    )
    db.add(canonical)
    db.flush()

    scan = db.scalar(
        select(Scan)
        .where(Scan.app_id == app_record.app_id)
        .order_by(Scan.started_at.desc())
    )
    if not scan:
        scan = Scan(
            app_id=app_record.app_id,
            platform=app_record.platform or "android",
            status="manual",
            script_version="manual-orphan-create",
            scan_config={"source": "create_orphan_node"},
        )
        db.add(scan)
        db.flush()

    page_info = {
        "page_type": "orphan",
        "is_orphan": True,
        "source": "manual",
        "review_status": "draft",
    }
    instance = PageInstance(
        scan_id=scan.scan_id,
        app_id=app_record.app_id,
        canonical_page_id=canonical.canonical_page_id,
        page_title=canonical.display_name,
        page_type="orphan",
        ai_summary="人工创建的游离 URL 页面，等待 AI 探索和截图识别。",
        inferred_purpose="等待 AI 探索",
        page_url=page_url,
        images=[],
        ai_inference={"label": "待探索", "reason": "该 URL 尚未归入主图谱。"},
        ai_recursive=False,
        raw_ai_payload={"page_url": page_url, "images": [], "page_info": page_info},
        normalized_payload={"page_info": page_info},
    )
    db.add(instance)
    db.commit()
    db.refresh(canonical)
    db.refresh(instance)
    return {
        "statue": "success",
        "created": True,
        "node": _orphan_node_payload(canonical, instance),
    }


def _orphan_node_payload(canonical: CanonicalPage, instance: PageInstance) -> dict[str, Any]:
    page_info = dict((instance.raw_ai_payload or {}).get("page_info") or {})
    page_info.update({"page_type": "orphan", "is_orphan": True, "review_status": canonical.review_status})
    return {
        "id": str(canonical.canonical_page_id),
        "page_id": canonical.page_hash_id,
        "page_title": canonical.display_name,
        "page_text": instance.ai_summary or "",
        "images": list(instance.images or []),
        "page_url": instance.page_url or "",
        "page_info": page_info,
        "ai_inference": instance.ai_inference or {},
        "ai_recursive": bool(instance.ai_recursive),
        "children": [],
    }


@app.get("/image/{image_name}")
def get_uploaded_image(image_name: str) -> FileResponse:
    safe_name = Path(image_name).name
    image_path = UPLOAD_DIR / safe_name
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path)


@app.post("/update_node")
def update_node(
    page_id: Annotated[str, Form(...)],
    page_title: Annotated[str, Form(...)],
    page_text: Annotated[str, Form(...)],
    page_url: Annotated[str, Form(...)],
    widget_description: Annotated[str, Form(...)],
    keep_images: Annotated[str | None, Form()] = None,
    ai_inference: Annotated[str | None, Form()] = None,
    action: Annotated[str | None, Form()] = None,
    ai_recursive: Annotated[bool | None, Form()] = None,
    new_images: Annotated[list[UploadFile] | None, File()] = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    canonical = db.scalar(select(CanonicalPage).where(CanonicalPage.page_hash_id == page_id))
    if not canonical:
        raise HTTPException(status_code=404, detail="Page not found")

    try:
        retained = json.loads(keep_images or "[]")
        inference = json.loads(ai_inference or "{}")
        parsed_action = _normalize_action(json.loads(action or "{}"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid JSON form field: {exc.msg}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not isinstance(retained, list) or not isinstance(inference, dict):
        raise HTTPException(status_code=422, detail="keep_images must be an array and ai_inference an object")

    final_images = [Path(str(name)).name for name in retained if str(name).strip()]
    for upload in new_images or []:
        original_name = Path(upload.filename or "image.bin").name
        stored_name = f"{page_id[:10]}_{uuid4().hex[:8]}_{original_name}"
        with (UPLOAD_DIR / stored_name).open("wb") as target:
            shutil.copyfileobj(upload.file, target)
        final_images.append(stored_name)

    canonical.display_name = page_title.strip() or canonical.display_name
    canonical.review_status = "edited"
    instance = db.scalar(
        select(PageInstance)
        .where(PageInstance.canonical_page_id == canonical.canonical_page_id)
        .order_by(PageInstance.created_at.desc())
    )
    if not instance:
        raise HTTPException(status_code=404, detail="Page instance not found")
    instance.page_title = canonical.display_name
    instance.ai_summary = page_text
    instance.page_url = page_url
    instance.images = final_images
    instance.ai_inference = inference
    instance.action = parsed_action
    if ai_recursive is not None:
        instance.ai_recursive = ai_recursive
    instance.inferred_purpose = str(inference.get("reason") or instance.inferred_purpose or "")

    incoming_edges = db.scalars(
        select(PageEdge).where(PageEdge.to_canonical_page_id == canonical.canonical_page_id)
    )
    for edge in incoming_edges:
        edge.widget_description = widget_description
    db.commit()

    return {
        "statue": "success",
        "node": {
            "page_id": page_id,
            "page_title": canonical.display_name,
            "page_text": page_text,
            "page_url": page_url,
            "widget_description": widget_description,
            "images": final_images,
            "ai_inference": inference,
            "action": parsed_action,
            "ai_recursive": instance.ai_recursive,
        },
    }


app.include_router(imports.router, prefix="/api/imports", tags=["imports"])
app.include_router(graph.router, prefix="/api/graph", tags=["graph"])
app.include_router(assets.router, prefix="/api/assets", tags=["assets"])
app.include_router(replay.router, prefix="/api/replay", tags=["replay"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
