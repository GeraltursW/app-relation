import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


# Use Text fallback when pgvector extension is not installed on the PG server.
# The Python pgvector package is still loaded for type registration if available.
_VECTOR_COLUMN_TYPE = Text
try:
    from pgvector.sqlalchemy import Vector  # noqa: F401
except ImportError:
    pass


class EmbeddingRecord(Base):
    __tablename__ = "embedding_records"

    embedding_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("apps.app_id"), index=True)
    owner_type: Mapped[str] = mapped_column(String(32), index=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    embedding_model: Mapped[str] = mapped_column(String(120))
    embedding_text: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(_VECTOR_COLUMN_TYPE, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
