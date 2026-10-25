"""Database helpers: build a SQLAlchemy engine from environment variables."""
import os

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine


def get_engine() -> Engine:
    """Create a SQLAlchemy engine using settings from .env."""
    load_dotenv()
    url = (
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@localhost:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    return create_engine(url)


if __name__ == "__main__":
    from sqlalchemy import text

    with get_engine().connect() as conn:
        print(conn.execute(text("SELECT count(*) FROM dw.dim_defect")).scalar())