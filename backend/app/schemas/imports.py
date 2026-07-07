from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, Field


class FolderImportRequest(BaseModel):
    folder: Path | None = Field(default=None, description="Folder containing AI JSON files.")


class FolderImportResult(BaseModel):
    imported_files: int
    app_id: UUID | None = None
    scan_ids: list[UUID] = []
    canonical_pages: int = 0
    page_instances: int = 0
    edges: int = 0
    errors: list[str] = []


class InitDbResult(BaseModel):
    status: str
    message: str

