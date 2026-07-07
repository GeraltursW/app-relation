import hashlib
import json
from pathlib import Path
from typing import Any


STRUCTURE_WIDGET_KEYS = (
    "widget_type",
    "semantic_name",
    "function_desc",
    "relative_position",
    "clickable",
    "expected_result",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def normalize_widget(widget: dict[str, Any]) -> dict[str, Any]:
    normalized = {key: widget.get(key) for key in STRUCTURE_WIDGET_KEYS if key in widget}
    bbox = widget.get("bbox") or {}
    if bbox:
        normalized["bbox_bucket"] = {
            "x": _bucket(bbox.get("x")),
            "y": _bucket(bbox.get("y")),
            "width": _bucket(bbox.get("width")),
            "height": _bucket(bbox.get("height")),
        }
    return normalized


def normalize_page_structure(page: dict[str, Any]) -> dict[str, Any]:
    payload = page.get("normalized_payload") or {}
    widgets = page.get("widgets") or payload.get("widgets") or []
    return {
        "page_type": page.get("page_type"),
        "layout_type": payload.get("layout_type"),
        "regions": payload.get("regions", []),
        "widgets": [normalize_widget(widget) for widget in widgets],
    }


def structure_hash_for_page(page: dict[str, Any]) -> str:
    normalized = normalize_page_structure(page)
    return sha256_bytes(canonical_json(normalized).encode("utf-8"))


def _bucket(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return round(float(value) / 16)
    except (TypeError, ValueError):
        return None

