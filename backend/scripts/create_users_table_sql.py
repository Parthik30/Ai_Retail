"""Create the `users` table using raw SQL (idempotent)."""
from backend.db import engine
from sqlalchemy import text

SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    last_login TIMESTAMP
);
"""


def create_table():
    with engine.begin() as conn:
        conn.execute(text(SQL))
    print("Ensured users table exists (CREATE TABLE IF NOT EXISTS executed).")


if __name__ == "__main__":
    create_table()
