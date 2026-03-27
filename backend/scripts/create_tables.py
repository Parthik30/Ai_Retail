"""Quick script to create tables (fallback when Alembic not used)."""
from ..db import init_db

# Ensure models are imported so their Table objects are registered on Base.metadata
import backend.models  # noqa: F401


if __name__ == "__main__":
    init_db()
    print("Tables created (or updated schema where needed).")
