from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# ── Database URL resolution ─────────────────────────────────────────────────
# Priority:
#  1. DATABASE_URL env var (PostgreSQL on Heroku/Railway/Neon/etc.)
#  2. SQLite fallback – works on Hugging Face Spaces (no external DB needed)
_raw_url = os.getenv("DATABASE_URL", "")

if _raw_url:
    # Heroku/Railway sometimes give 'postgres://' which SQLAlchemy 2.x requires
    # to be 'postgresql://'
    if _raw_url.startswith("postgres://"):
        _raw_url = _raw_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL = _raw_url
    _db_kwargs = {}
else:
    # SQLite fallback – persisted inside /app/data/ so it survives container restarts
    _db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(_db_dir, exist_ok=True)
    DATABASE_URL = f"sqlite:///{os.path.join(_db_dir, 'intellistock.db')}"
    _db_kwargs = {"connect_args": {"check_same_thread": False}}

engine = create_engine(DATABASE_URL, echo=False, **_db_kwargs)
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
        if dsn.startswith("postgres://"):
            dsn = dsn.replace("postgres://", "postgresql://", 1)
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

    from .models import User
    import datetime

    # Seeding: Create default user if none exists
    session = SessionLocal()
    try:
        if session.query(User).count() == 0:
            default_user = User(
                user_id="U0001",
                username="Parthik",
                email="parthikgohel754@gmail.com",
                password_hash="Parth@$1023",
                role="Admin",
                is_active=True,
                created_at=datetime.datetime.utcnow()
            )
            session.add(default_user)
            session.commit()
            print("Default user 'Parthik' seeded.")
    except Exception as e:
        print(f"Seeding failed: {e}")
        session.rollback()
    finally:
        session.close()

    # development convenience: add registration_id to users if missing
    # (SQLite doesn't support IF NOT EXISTS on ALTER, so guard carefully)
    try:
        insp = inspect(engine)
        if "users" in insp.get_table_names():
            cols = [c["name"] for c in insp.get_columns("users")]
            if "registration_id" not in cols:
                with engine.connect() as conn:
                    if DATABASE_URL.startswith("sqlite"):
                        conn.execute(text("ALTER TABLE users ADD COLUMN registration_id VARCHAR"))
                    else:
                        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS registration_id VARCHAR"))
                    conn.commit()
    except Exception:
        # ignore any errors here; create_tables.py or migrations should handle it
        pass


if __name__ == "__main__":
    init_db()
    print("Database tables created (if not present).")
