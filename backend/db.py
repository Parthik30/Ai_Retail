from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Prefer DATABASE_URL from environment, fall back to a sensible default for local dev
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:123@localhost:5432/intellistock_db")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Optional psycopg2 helper to obtain a raw connection (reads credentials from env)
def get_connection():
    """Return a psycopg2 connection using DATABASE_URL or individual env vars.

    Usage:
        from backend.db import get_connection
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
                print(cur.fetchone())
    """
    try:
        import psycopg2
    except Exception as exc:
        raise RuntimeError("psycopg2 is required for get_connection() but is not installed") from exc

    # If DATABASE_URL is set, let psycopg2 parse the DSN
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        # psycopg2 accepts URLs directly
        return psycopg2.connect(dsn)

    # otherwise read components
    host = os.getenv("DB_HOST", "localhost")
    db = os.getenv("DB_NAME", "intellistock_db")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASS", "123")
    port = os.getenv("DB_PORT", "5432")

    return psycopg2.connect(host=host, dbname=db, user=user, password=password, port=port)


from sqlalchemy import inspect, text

def init_db():
    """Create tables using SQLAlchemy metadata. Useful for quick setup or as a fallback to Alembic.

    Also performs lightweight schema adjustments to keep development databases in sync
    with the current model definitions. In particular, if the `users` table exists but
    lacks the `registration_id` column (added later), an ALTER statement will be run.
    """
    Base.metadata.create_all(bind=engine)

    # development convenience: add registration_id to users if missing
    try:
        insp = inspect(engine)
        if "users" in insp.get_table_names():
            cols = [c["name"] for c in insp.get_columns("users")]
            if "registration_id" not in cols:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS registration_id VARCHAR"))
                    conn.commit()
    except Exception:
        # ignore any errors here; create_tables.py or migrations should handle it
        pass


if __name__ == "__main__":
    init_db()
    print("Database tables created (if not present).")
