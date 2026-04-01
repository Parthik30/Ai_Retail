import sys
import os

# Add parent directory to path to import backend
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(BACKEND_DIR))

from backend.db import SessionLocal, init_db
from backend.models import User
from datetime import datetime

def create_superadmin():
    print("Checking for existing super_admin...")
    session = SessionLocal()
    try:
        # Check if super_admin exists
        existing = session.query(User).filter(User.role == "super_admin").first()
        if existing:
            print(f"Super admin already exists: {existing.username}")
            return

        print("Creating super_admin user...")
        admin = User(
            user_id="U0001",
            username="admin",
            email="admin@intellistock.com",
            password_hash="admin123", # Note: Real apps should hash password
            role="super_admin",
            is_active=True,
            created_at=datetime.utcnow()
        )
        session.add(admin)
        session.commit()
        print("✅ Super admin 'admin' created successfully with password 'admin123'")
    except Exception as e:
        print(f"❌ Error creating super admin: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    create_superadmin()
