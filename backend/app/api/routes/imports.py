from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models  # noqa: F401
from app.core.config import get_settings
from app.core.database import Base, engine, get_db
from app.schemas.imports import FolderImportRequest, FolderImportResult, InitDbResult
from app.services.importer import AiFolderImporter

router = APIRouter()


@router.post("/init-db", response_model=InitDbResult)
def init_db() -> InitDbResult:
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    except Exception:
        pass  # pgvector not installed on server, skip
    Base.metadata.create_all(bind=engine)
    return InitDbResult(status="ok", message="Database schema is ready.")


@router.post("/scan-folder", response_model=FolderImportResult)
def import_scan_folder(request: FolderImportRequest, db: Session = Depends(get_db)) -> FolderImportResult:
    settings = get_settings()
    folder = Path(request.folder) if request.folder else settings.import_inbox_dir
    importer = AiFolderImporter(db=db, inbox_dir=settings.import_inbox_dir)
    return importer.import_folder(folder)

