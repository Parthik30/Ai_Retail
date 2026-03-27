"""Seed an initial user into the database if it doesn't exist.

This script uses the project's `engine` to run a simple INSERT ... ON CONFLICT
so we don't re-import model classes (avoids SQLAlchemy duplicate-table errors
in some execution contexts).
"""
from backend.db import engine
from sqlalchemy import text
import datetime


def seed_user():
    now = datetime.datetime.utcnow()
    user = {
        "user_id": "U01",
        "username": "Parthik",
        "email": "parthikgohel754@gmail.com",
        "password_hash": "Parth@$1023",
        "role": "Admin",
        "is_active": True,
        "created_at": now,
        "last_login": None,
    }

    sql = text(
        """
        INSERT INTO users (user_id, username, email, password_hash, role, is_active, created_at, last_login)
        VALUES (:user_id, :username, :email, :password_hash, :role, :is_active, :created_at, :last_login)
        ON CONFLICT (user_id) DO NOTHING
        """
    )

    with engine.begin() as conn:
        result = conn.execute(sql, user)
        # result.rowcount may be 0 if user already existed
        if result.rowcount and result.rowcount > 0:
            print("Seeded user Parthik (U01) into users table.")
        else:
            print("User already exists or was not inserted.")


if __name__ == "__main__":
    seed_user()
