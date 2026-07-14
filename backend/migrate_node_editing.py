"""Add stable page IDs and editable node fields to the local PostgreSQL schema."""
from sqlalchemy import text

from app.core.database import engine


STATEMENTS = [
    "ALTER TABLE canonical_pages ADD COLUMN IF NOT EXISTS page_hash_id VARCHAR(64)",
    """
    UPDATE canonical_pages
    SET page_hash_id = substr(md5(canonical_page_id::text || ':' || app_id::text), 1, 32)
    WHERE page_hash_id IS NULL
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_canonical_pages_page_hash_id ON canonical_pages(page_hash_id)",
    "ALTER TABLE page_instances ADD COLUMN IF NOT EXISTS page_url TEXT",
    "ALTER TABLE page_instances ADD COLUMN IF NOT EXISTS images JSONB NOT NULL DEFAULT '[]'::jsonb",
    "ALTER TABLE page_instances ADD COLUMN IF NOT EXISTS ai_inference JSONB NOT NULL DEFAULT '{}'::jsonb",
    """
    UPDATE page_instances
    SET page_url = COALESCE(page_url, raw_ai_payload->>'page_url'),
        images = CASE
            WHEN images = '[]'::jsonb AND jsonb_typeof(raw_ai_payload->'images') = 'array'
            THEN raw_ai_payload->'images'
            ELSE images
        END,
        ai_inference = CASE
            WHEN ai_inference = '{}'::jsonb AND jsonb_typeof(raw_ai_payload->'ai_inference') = 'object'
            THEN raw_ai_payload->'ai_inference'
            ELSE ai_inference
        END
    """,
]


def main() -> None:
    with engine.begin() as connection:
        for statement in STATEMENTS:
            connection.execute(text(statement))
    print("Node editing schema migration complete.")


if __name__ == "__main__":
    main()

