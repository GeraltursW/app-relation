import uuid

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


def uuid_pk():
    return UUID(as_uuid=True), {"primary_key": True, "default": uuid.uuid4}


def timestamp_column():
    return DateTime(timezone=True), {"server_default": func.now(), "nullable": False}
