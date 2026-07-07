from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Asset

router = APIRouter()


@router.get("/{asset_id}")
def get_asset(asset_id: UUID, db: Session = Depends(get_db)) -> FileResponse:
    asset = db.get(Asset, asset_id)
    if not asset or not asset.local_path:
        raise HTTPException(status_code=404, detail="Asset not found.")
    return FileResponse(asset.local_path, media_type=asset.mime_type)

