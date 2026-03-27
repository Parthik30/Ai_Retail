from pathlib import Path
from backend.db import init_db, SessionLocal
from backend.models import Product, SalesHistory
from backend.services import dashboard_service
import datetime


def setup_module(module):
    # ensure DB and tables exist
    init_db()


def test_sales_history_db_integration(tmp_path):
    session = SessionLocal()
    try:
        # ensure idempotent: remove existing test data
        session.query(SalesHistory).filter(SalesHistory.product_name == "Test Product").delete()
        session.query(Product).filter(Product.product_id == "T001").delete()
        session.commit()
        # create a product
        p = Product(product_id="T001", product_name="Test Product", selling_price=100.0, cost_price=50.0, monthly_sales=10, stock=20)
        session.add(p)
        session.commit()
        # add sales history rows
        for i in range(6):
            sh = SalesHistory(product_name="Test Product", date=datetime.datetime(2023, i+1, 1), sales=10 + i)
            session.add(sh)
        session.commit()
    finally:
        session.close()

    dq = dashboard_service.compute_data_quality(Path("."))
    assert "sales_history.csv" in dq
    assert dq["sales_history.csv"]["exists"] is True
    assert dq["sales_history.csv"]["rows"] is not None


def test_get_demand_pattern_classification_uses_db(tmp_path):
    df = dashboard_service.get_demand_pattern_classification()
    # Our test product should be present
    assert any(df["product_name"] == "Test Product")
    row = df[df["product_name"] == "Test Product"].iloc[0]
    assert bool(row["sales_history_available"]) is True