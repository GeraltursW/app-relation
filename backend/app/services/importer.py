import json
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import App, Asset, CanonicalPage, PageEdge, PageInstance, PageWidget, Scan
from app.schemas.imports import FolderImportResult
from app.services.hash import sha256_file, structure_hash_for_page


class AiFolderImporter:
    def __init__(self, db: Session, inbox_dir: Path) -> None:
        self.db = db
        self.inbox_dir = inbox_dir

    def import_folder(self, folder: Path | None = None) -> FolderImportResult:
        source_dir = (folder or self.inbox_dir).resolve()
        result = FolderImportResult(imported_files=0)
        if not source_dir.exists():
            result.errors.append(f"Folder does not exist: {source_dir}")
            return result

        for json_path in sorted(source_dir.glob("*.json")):
            try:
                imported = self.import_file(json_path)
                result.imported_files += 1
                result.app_id = imported["app_id"]
                result.scan_ids.append(imported["scan_id"])
                result.canonical_pages += imported["canonical_pages"]
                result.page_instances += imported["page_instances"]
                result.edges += imported["edges"]
            except Exception as exc:  # noqa: BLE001
                result.errors.append(f"{json_path.name}: {exc}")
        self.db.commit()
        return result

    def import_file(self, json_path: Path) -> dict[str, Any]:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        app_data = payload.get("app") or {}
        scan_data = payload.get("scan") or {}

        app = self._get_or_create_app(app_data)
        scan = Scan(
            app_id=app.app_id,
            app_version=app_data.get("app_version"),
            device_id=scan_data.get("device_id"),
            platform=app_data.get("platform") or "android",
            os_version=scan_data.get("os_version"),
            script_version=scan_data.get("script_version"),
            ai_model=scan_data.get("ai_model"),
            status="completed",
            scan_config=scan_data.get("scan_config"),
        )
        self.db.add(scan)
        self.db.flush()

        page_lookup: dict[str, PageInstance] = {}
        canonical_count = 0
        for page in payload.get("pages", []):
            page_instance, created_canonical = self._import_page(app.app_id, scan.scan_id, page, json_path.parent)
            page_key = str(page.get("page_key") or page.get("page_title") or page_instance.page_instance_id)
            page_lookup[page_key] = page_instance
            canonical_count += int(created_canonical)

        edge_count = 0
        for edge in payload.get("edges", []):
            created = self._import_edge(app.app_id, scan.scan_id, edge, page_lookup)
            edge_count += int(created)

        return {
            "app_id": app.app_id,
            "scan_id": scan.scan_id,
            "canonical_pages": canonical_count,
            "page_instances": len(page_lookup),
            "edges": edge_count,
        }

    def _get_or_create_app(self, app_data: dict[str, Any]) -> App:
        package_name = app_data.get("package_name") or "unknown.package"
        app = self.db.scalar(select(App).where(App.package_name == package_name))
        if app:
            return app
        app = App(
            package_name=package_name,
            app_name=app_data.get("app_name") or package_name,
            market_rank=app_data.get("market_rank"),
            category=app_data.get("category"),
            platform=app_data.get("platform") or "android",
            vendor=app_data.get("vendor"),
        )
        self.db.add(app)
        self.db.flush()
        return app

    def _import_page(
        self,
        app_id: UUID,
        scan_id: UUID,
        page: dict[str, Any],
        base_dir: Path,
    ) -> tuple[PageInstance, bool]:
        structure_hash = page.get("structure_hash") or structure_hash_for_page(page)
        screenshot_asset = self._create_asset(app_id, scan_id, page.get("screenshot"), base_dir)
        screenshot_hash = screenshot_asset.sha256 if screenshot_asset else None

        canonical = self.db.scalar(
            select(CanonicalPage).where(
                CanonicalPage.app_id == app_id,
                CanonicalPage.primary_structure_hash == structure_hash,
            )
        )
        created_canonical = False
        if not canonical:
            page_key = page.get("page_key") or structure_hash[:12]
            canonical = CanonicalPage(
                app_id=app_id,
                canonical_page_key=page_key,
                display_name=page.get("page_title") or page_key,
                page_type=page.get("page_type") or "unknown",
                representative_asset_id=screenshot_asset.asset_id if screenshot_asset else None,
                primary_structure_hash=structure_hash,
                primary_visual_hash=page.get("visual_hash"),
                primary_route_hash=page.get("route_hash"),
                instance_count=0,
            )
            self.db.add(canonical)
            self.db.flush()
            created_canonical = True

        canonical.instance_count += 1
        instance = PageInstance(
            scan_id=scan_id,
            app_id=app_id,
            canonical_page_id=canonical.canonical_page_id,
            page_title=page.get("page_title") or canonical.display_name,
            page_type=page.get("page_type") or canonical.page_type,
            screenshot_asset_id=screenshot_asset.asset_id if screenshot_asset else None,
            screenshot_hash=screenshot_hash,
            visual_hash=page.get("visual_hash"),
            structure_hash=structure_hash,
            route_hash=page.get("route_hash"),
            ocr_text=page.get("ocr_text"),
            ai_summary=page.get("ai_summary"),
            inferred_purpose=page.get("inferred_purpose"),
            confidence=page.get("confidence"),
            raw_ai_payload=page,
            normalized_payload=page.get("normalized_payload"),
        )
        self.db.add(instance)
        self.db.flush()

        widget_lookup: dict[str, PageWidget] = {}
        for widget in page.get("widgets", []):
            page_widget = self._create_widget(instance, canonical.canonical_page_id, widget)
            widget_key = widget.get("widget_key")
            if widget_key:
                widget_lookup[str(widget_key)] = page_widget
        instance.raw_ai_payload = {**page, "_widget_id_by_key": {key: str(value.widget_id) for key, value in widget_lookup.items()}}
        return instance, created_canonical

    def _create_asset(self, app_id: UUID, scan_id: UUID, screenshot: str | None, base_dir: Path) -> Asset | None:
        if not screenshot:
            return None
        path = Path(screenshot)
        if not path.is_absolute():
            path = base_dir / path
        if not path.exists():
            return None
        digest = sha256_file(path)
        existing = self.db.scalar(select(Asset).where(Asset.sha256 == digest))
        if existing:
            return existing
        asset = Asset(
            scan_id=scan_id,
            app_id=app_id,
            asset_type="screenshot",
            local_path=str(path),
            sha256=digest,
            mime_type=_guess_mime(path),
        )
        self.db.add(asset)
        self.db.flush()
        return asset

    def _create_widget(self, instance: PageInstance, canonical_page_id: UUID, widget: dict[str, Any]) -> PageWidget:
        bbox = widget.get("bbox") or {}
        page_widget = PageWidget(
            page_instance_id=instance.page_instance_id,
            canonical_page_id=canonical_page_id,
            widget_type=widget.get("widget_type") or "unknown",
            text=widget.get("text"),
            semantic_name=widget.get("semantic_name"),
            function_desc=widget.get("function_desc"),
            relative_position=widget.get("relative_position"),
            bbox_x=bbox.get("x"),
            bbox_y=bbox.get("y"),
            bbox_width=bbox.get("width"),
            bbox_height=bbox.get("height"),
            clickable=widget.get("clickable", True),
            expected_result=widget.get("expected_result"),
            confidence=widget.get("confidence"),
            raw_ai_payload=widget,
        )
        self.db.add(page_widget)
        self.db.flush()
        return page_widget

    def _import_edge(
        self,
        app_id: UUID,
        scan_id: UUID,
        edge: dict[str, Any],
        page_lookup: dict[str, PageInstance],
    ) -> bool:
        from_page = page_lookup.get(str(edge.get("from_page_key")))
        to_page = page_lookup.get(str(edge.get("to_page_key")))
        if not from_page or not to_page:
            return False
        page_edge = PageEdge(
            scan_id=scan_id,
            app_id=app_id,
            from_page_instance_id=from_page.page_instance_id,
            to_page_instance_id=to_page.page_instance_id,
            from_canonical_page_id=from_page.canonical_page_id,
            to_canonical_page_id=to_page.canonical_page_id,
            action_type=edge.get("action_type") or "tap",
            label=edge.get("label") or edge.get("action_type") or "tap",
            confidence=edge.get("confidence"),
            raw_action_payload=edge,
        )
        self.db.add(page_edge)
        return True


def _guess_mime(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    return "application/octet-stream"

