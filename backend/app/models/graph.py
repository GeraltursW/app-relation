import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class CanonicalPage(Base):
    __tablename__ = "canonical_pages"

    canonical_page_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("apps.app_id"), index=True)
    canonical_page_key: Mapped[str] = mapped_column(String(255), index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    page_type: Mapped[str] = mapped_column(String(120), index=True)
    representative_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.asset_id"), nullable=True)
    primary_structure_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    primary_visual_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    primary_route_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    instance_count: Mapped[int] = mapped_column(Integer, default=0)
    review_status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class PageInstance(Base):
    __tablename__ = "page_instances"

    page_instance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scans.scan_id"), index=True)
    app_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("apps.app_id"), index=True)
    canonical_page_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical_pages.canonical_page_id"), nullable=True, index=True)
    page_title: Mapped[str] = mapped_column(String(255))
    page_type: Mapped[str] = mapped_column(String(120), index=True)
    screenshot_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.asset_id"), nullable=True)
    screenshot_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    visual_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    structure_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    route_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    inferred_purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    raw_ai_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    normalized_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PageWidget(Base):
    __tablename__ = "page_widgets"

    widget_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_instance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("page_instances.page_instance_id"), index=True)
    canonical_page_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical_pages.canonical_page_id"), nullable=True, index=True)
    widget_type: Mapped[str] = mapped_column(String(64), index=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    semantic_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    function_desc: Mapped[str | None] = mapped_column(Text, nullable=True)
    relative_position: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bbox_x: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_y: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clickable: Mapped[bool] = mapped_column(Boolean, default=True)
    expected_result: Mapped[str | None] = mapped_column(String(255), nullable=True)
    widget_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.asset_id"), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    raw_ai_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PageEdge(Base):
    __tablename__ = "page_edges"

    edge_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scans.scan_id"), index=True)
    app_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("apps.app_id"), index=True)
    from_page_instance_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("page_instances.page_instance_id"), nullable=True)
    to_page_instance_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("page_instances.page_instance_id"), nullable=True)
    from_canonical_page_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical_pages.canonical_page_id"), nullable=True, index=True)
    to_canonical_page_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical_pages.canonical_page_id"), nullable=True, index=True)
    widget_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("page_widgets.widget_id"), nullable=True)
    action_type: Mapped[str] = mapped_column(String(64), default="tap")
    label: Mapped[str] = mapped_column(String(255))
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="discovered")
    raw_action_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
