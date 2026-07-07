import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class App(Base):
    __tablename__ = "apps"

    app_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    app_name: Mapped[str] = mapped_column(String(255))
    market_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    platform: Mapped[str] = mapped_column(String(32), default="android")
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    scans = relationship("Scan", back_populates="app")


class Scan(Base):
    __tablename__ = "scans"

    scan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("apps.app_id"), index=True)
    app_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    platform: Mapped[str] = mapped_column(String(32), default="android")
    os_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    script_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="running", index=True)
    started_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    scan_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    app = relationship("App", back_populates="scans")
