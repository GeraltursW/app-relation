from sqlalchemy import text

from app.core.database import engine


def main() -> None:
    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE page_instances ADD COLUMN IF NOT EXISTS action JSONB")
        )
    print("page_instances.action is ready")


if __name__ == "__main__":
    main()
