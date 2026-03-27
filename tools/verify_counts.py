"""Verify row counts for key tables and print samples."""
from sqlalchemy import text
from backend.db import engine

with engine.connect() as conn:
    for tbl in ["products", "reorders", "discount_audit", "ai_recommendations"]:
        try:
            cnt = conn.execute(text(f"SELECT count(*) FROM {tbl}")).scalar()
        except Exception as e:
            cnt = f"ERROR: {e}"
        print(f"{tbl}: {cnt}")

    print("\nProducts sample:")
    rows = conn.execute(text("SELECT product_id, product_name, stock FROM products ORDER BY product_id LIMIT 5")).fetchall()
    for r in rows:
        print(r)
