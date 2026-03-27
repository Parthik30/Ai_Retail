"""Seed sample Returns and Supplier rows for local testing (idempotent).

This script is safe to run multiple times; it removes previously inserted seed rows and reinserts them.
"""
from backend.db import SessionLocal, init_db
from backend.models import ReturnRecord, Supplier
import datetime


def seed():
    init_db()
    session = SessionLocal()
    try:
        # Remove previous seed rows (identified by reason/supplier_name prefix)
        session.query(ReturnRecord).filter(ReturnRecord.reason.like('SEED:%')).delete(synchronize_session=False)
        session.query(Supplier).filter(Supplier.supplier_name.like('SEED:%')).delete(synchronize_session=False)
        session.commit()

        # Insert sample returns
        r1 = ReturnRecord(
            product_name='Test Product',
            date=datetime.datetime(2023, 6, 15),
            quantity=2,
            reason='SEED: defective packaging'
        )
        r2 = ReturnRecord(
            product_name='Laptop Dell i5',
            date=datetime.datetime(2023, 12, 1),
            quantity=1,
            reason='SEED: customer return - changed mind'
        )
        session.add_all([r1, r2])

        # Insert sample suppliers
        s1 = Supplier(
            supplier_name='SEED: ACME Supplies',
            product_name='Test Product',
            lead_time_days=7
        )
        s2 = Supplier(
            supplier_name='SEED: Laptop Supplier Inc',
            product_name='Laptop Dell i5',
            lead_time_days=14
        )
        session.add_all([s1, s2])

        session.commit()
        print('Seed rows inserted successfully')
    finally:
        session.close()


if __name__ == '__main__':
    seed()
