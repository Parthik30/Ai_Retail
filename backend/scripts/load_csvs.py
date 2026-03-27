"""Idempotent CSV loader: reads CSVs in backend/data and inserts/updates DB rows."""
import os
import pandas as pd
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from ..db import SessionLocal, engine, init_db
from ..models import Product, Reorder, DiscountAudit, AIRecommendation, SalesHistory, ReturnRecord, Supplier

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_products(session):
    path = os.path.join(DATA_DIR, "products.csv")
    df = pd.read_csv(path)
    for _, row in df.iterrows():
        pid = str(row.get("product_id"))
        product = session.get(Product, pid)
        if product:
            # update
            product.product_name = row.get("product_name")
            product.category = row.get("category")
            product.cost_price = float(row.get("cost_price")) if not pd.isna(row.get("cost_price")) else None
            product.selling_price = float(row.get("selling_price")) if not pd.isna(row.get("selling_price")) else None
            product.discount = float(row.get("discount")) if not pd.isna(row.get("discount")) else None
            product.stock = int(row.get("stock")) if not pd.isna(row.get("stock")) else None
            product.monthly_sales = int(row.get("monthly_sales")) if not pd.isna(row.get("monthly_sales")) else None
            product.demand_level = row.get("demand_level")
            product.rating = float(row.get("rating")) if not pd.isna(row.get("rating")) else None
            product.supplier_lead_time = int(row.get("supplier_lead_time")) if not pd.isna(row.get("supplier_lead_time")) else None
        else:
            product = Product(
                product_id=pid,
                product_name=row.get("product_name"),
                category=row.get("category"),
                cost_price=float(row.get("cost_price")) if not pd.isna(row.get("cost_price")) else None,
                selling_price=float(row.get("selling_price")) if not pd.isna(row.get("selling_price")) else None,
                discount=float(row.get("discount")) if not pd.isna(row.get("discount")) else None,
                stock=int(row.get("stock")) if not pd.isna(row.get("stock")) else None,
                monthly_sales=int(row.get("monthly_sales")) if not pd.isna(row.get("monthly_sales")) else None,
                demand_level=row.get("demand_level"),
                rating=float(row.get("rating")) if not pd.isna(row.get("rating")) else None,
                supplier_lead_time=int(row.get("supplier_lead_time")) if not pd.isna(row.get("supplier_lead_time")) else None,
            )
            session.add(product)
    session.commit()
    print("Products loaded/updated")


def parse_datetime(x):
    if pd.isna(x):
        return None
    try:
        return pd.to_datetime(x)
    except Exception:
        return None


def load_reorders(session):
    path = os.path.join(DATA_DIR, "reorders.csv")
    if not os.path.exists(path):
        print("reorders.csv not found, skipping")
        return
    df = pd.read_csv(path)

    for _, row in df.iterrows():
        # convert various timestamp fields
        ts = parse_datetime(row.get("timestamp") or row.get("ordered_at"))
        expected = parse_datetime(row.get("expected_delivery"))
        completed = parse_datetime(row.get("completed_at"))

        # gather values with fallbacks to legacy names
        pid = row.get("product_id") or row.get("product_name") or row.get("product")
        qty_ord = (int(row.get("quantity_ordered")) if not pd.isna(row.get("quantity_ordered")) else
                   (int(row.get("reorder_qty")) if not pd.isna(row.get("reorder_qty")) else
                    (int(row.get("quantity")) if not pd.isna(row.get("quantity")) else None)))
        reorder_pt = int(row.get("reorder_point")) if not pd.isna(row.get("reorder_point")) else None
        max_st = int(row.get("max_stock")) if not pd.isna(row.get("max_stock")) else None
        min_st = int(row.get("min_stock")) if not pd.isna(row.get("min_stock")) else None
        status = row.get("status")
        eta_month = int(row.get("eta_month")) if not pd.isna(row.get("eta_month")) else None
        arrive_mon = int(row.get("arrival_month")) if not pd.isna(row.get("arrival_month")) else None
        placed_by = row.get("placed_by")

        # dedupe based on key fields depending on schema version
        query = session.query(Reorder)
        if pid and qty_ord is not None:
            query = query.filter_by(product_id=pid) if hasattr(Reorder, 'product_id') else query.filter_by(product=pid)
            if hasattr(Reorder, 'quantity_ordered'):
                query = query.filter_by(quantity_ordered=qty_ord)
            else:
                query = query.filter_by(quantity=qty_ord)
        exists = query.first()
        if exists:
            # update timestamps/status if new data
            if ts and (not getattr(exists, 'ordered_at', None) or ts > getattr(exists, 'ordered_at', None)):
                exists.ordered_at = ts
            if status:
                exists.status = status
            continue

        # build Reorder object with whichever attrs available
        kwargs = {}
        if 'reorder_id' in df.columns:
            kwargs['reorder_id'] = row.get('reorder_id')
        if pid is not None:
            kwargs['product_id'] = pid
        if qty_ord is not None:
            kwargs['quantity_ordered'] = qty_ord
        if reorder_pt is not None:
            kwargs['reorder_point'] = reorder_pt
        if max_st is not None:
            kwargs['max_stock'] = max_st
        if min_st is not None:
            kwargs['min_stock'] = min_st
        if status is not None:
            kwargs['status'] = status
        if ts is not None:
            kwargs['ordered_at'] = ts
        if expected is not None:
            kwargs['expected_delivery'] = expected
        if completed is not None:
            kwargs['completed_at'] = completed
        # legacy
        kwargs['product'] = pid
        kwargs['quantity'] = qty_ord
        kwargs['eta_month'] = arrive_mon
        kwargs['placed_by'] = placed_by
        kwargs['created_at'] = ts

        r = Reorder(**kwargs)
        session.add(r)
    session.commit()
    print("Reorders loaded")


def load_discount_audit(session):
    path = os.path.join(DATA_DIR, "discount_audit.csv")
    if not os.path.exists(path):
        print("discount_audit.csv not found, skipping")
        return
    df = pd.read_csv(path)

    # Detect available columns in target table to avoid inserting missing columns
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        cols = {c['name'] for c in inspector.get_columns('discount_audit')}
    except Exception:
        cols = set()

    for _, row in df.iterrows():
        ts = parse_datetime(row.get("timestamp"))
        # Query only the primary key to avoid selecting missing columns in older schemas
        try:
            exists = session.query(DiscountAudit.id).filter_by(timestamp=ts, product=row.get("product"), old_discount=row.get("old_discount"), new_discount=row.get("new_discount")).first()
        except Exception:
            exists = None
        if exists:
            continue

        # Prepare insert params based on columns that actually exist
        params = {
            'timestamp': ts,
            'product': row.get('product'),
            'old_discount': float(row.get('old_discount')) if not pd.isna(row.get('old_discount')) else None,
            'new_discount': float(row.get('new_discount')) if not pd.isna(row.get('new_discount')) else None,
        }
        if 'user' in cols and 'user' in df.columns:
            params['user'] = row.get('user')
        if 'note' in cols and 'note' in df.columns:
            params['note'] = row.get('note')

        if cols:
            # build SQL dynamically with only the available columns
            column_list = ', '.join(params.keys())
            placeholder_list = ', '.join([f':{k}' for k in params.keys()])
            sql = text(f"INSERT INTO discount_audit ({column_list}) VALUES ({placeholder_list})")
            try:
                session.execute(sql, params)
            except Exception:
                # fallback to SQLAlchemy object add if raw insert fails
                try:
                    d = DiscountAudit(**{k: v for k, v in params.items() if k in DiscountAudit.__table__.columns.keys()})
                    session.add(d)
                except Exception as e:
                    print("Skipping discount audit row due to insert error:", e)
                    continue
        else:
            # If we couldn't detect columns, fall back to SQLAlchemy model insert and catch errors
            try:
                d = DiscountAudit(
                    timestamp=ts,
                    product=row.get('product'),
                    old_discount=float(row.get('old_discount')) if not pd.isna(row.get('old_discount')) else None,
                    new_discount=float(row.get('new_discount')) if not pd.isna(row.get('new_discount')) else None,
                    user=row.get('user') if 'user' in df.columns else None,
                    note=row.get('note') if 'note' in df.columns else None,
                )
                session.add(d)
            except Exception as e:
                print("Skipping discount audit row due to insert error:", e)
                continue
    session.commit()
    print("Discount audit loaded")


def load_ai_recommendations(session):
    path = os.path.join(DATA_DIR, "ai_recommendations.csv")
    if not os.path.exists(path):
        print("ai_recommendations.csv not found, skipping")
        return
    df = pd.read_csv(path)
    for _, row in df.iterrows():
        rid = str(row.get("id"))
        exists = session.get(AIRecommendation, rid)
        if exists:
            # update applied flag / timestamps if needed
            exists.applied = bool(row.get("applied"))
            exists.applied_at = parse_datetime(row.get("applied_at"))
            exists.applied_by = row.get("applied_by")
        else:
            a = AIRecommendation(
                id=rid,
                timestamp=parse_datetime(row.get("timestamp")),
                product=row.get("product"),
                objective=row.get("objective"),
                suggested_discount=float(row.get("suggested_discount")) if not pd.isna(row.get("suggested_discount")) else None,
                expected_units=int(row.get("expected_units")) if not pd.isna(row.get("expected_units")) else None,
                expected_revenue=float(row.get("expected_revenue")) if not pd.isna(row.get("expected_revenue")) else None,
                expected_profit=float(row.get("expected_profit")) if not pd.isna(row.get("expected_profit")) else None,
                confidence=float(row.get("confidence")) if not pd.isna(row.get("confidence")) else None,
                applied=bool(row.get("applied")),
                applied_at=parse_datetime(row.get("applied_at")),
                applied_by=row.get("applied_by"),
                prev_discount=float(row.get("prev_discount")) if not pd.isna(row.get("prev_discount")) else None,
                prev_price=float(row.get("prev_price")) if not pd.isna(row.get("prev_price")) else None,
                note=row.get("note"),
            )
            session.add(a)
    session.commit()
    print("AI recommendations loaded")


def load_forecasts(session):
    path = os.path.join(DATA_DIR, "forecasts.csv")
    if not os.path.exists(path):
        print("forecasts.csv not found, skipping")
        return
    df = pd.read_csv(path)
    for _, row in df.iterrows():
        fid = row.get("forecast_id")
        exists = session.query(Forecast).get(fid) if fid else None
        if exists:
            continue
        f = Forecast(
            forecast_id=fid,
            product_id=row.get("product_id"),
            model_type=row.get("model_type"),
            forecast_period=parse_datetime(row.get("forecast_period")),
            predicted_sales=int(row.get("predicted_sales")) if not pd.isna(row.get("predicted_sales")) else None,
            confidence_lower=float(row.get("confidence_lower")) if not pd.isna(row.get("confidence_lower")) else None,
            confidence_upper=float(row.get("confidence_upper")) if not pd.isna(row.get("confidence_upper")) else None,
            mae=float(row.get("mae")) if not pd.isna(row.get("mae")) else None,
            rmse=float(row.get("rmse")) if not pd.isna(row.get("rmse")) else None,
            created_at=parse_datetime(row.get("created_at")),
        )
        session.add(f)
    session.commit()
    print("Forecasts loaded")


def load_alerts(session):
    path = os.path.join(DATA_DIR, "alerts.csv")
    if not os.path.exists(path):
        print("alerts.csv not found, skipping")
        return
    df = pd.read_csv(path)
    for _, row in df.iterrows():
        aid = row.get("alert_id")
        exists = session.query(Alert).get(aid) if aid else None
        if exists:
            continue
        a = Alert(
            alert_id=aid,
            product_id=row.get("product_id"),
            alert_type=row.get("alert_type"),
            severity=row.get("severity"),
            message=row.get("message"),
            is_resolved=bool(row.get("is_resolved")),
            resolved_by=row.get("resolved_by"),
            created_at=parse_datetime(row.get("created_at")),
            resolved_at=parse_datetime(row.get("resolved_at")),
        )
        session.add(a)
    session.commit()
    print("Alerts loaded")


def load_users(session):
    path = os.path.join(DATA_DIR, "users.csv")
    if not os.path.exists(path):
        print("users.csv not found, skipping")
        return
    df = pd.read_csv(path)
    for _, row in df.iterrows():
        uid = row.get("user_id")
        exists = session.query(User).get(uid) if uid else None
        if exists:
            continue
        u = User(
            user_id=uid,
            username=row.get("username"),
            email=row.get("email"),
            password_hash=row.get("password_hash"),
            role=row.get("role"),
            is_active=bool(row.get("is_active")),
            created_at=parse_datetime(row.get("created_at")),
            last_login=parse_datetime(row.get("last_login")),
        )
        session.add(u)
    session.commit()
    print("Users loaded")


def load_sales_history(session):
    path = os.path.join(DATA_DIR, "sales_history.csv")
    if not os.path.exists(path):
        print("sales_history.csv not found, skipping")
        return
    df = pd.read_csv(path)
    for _, row in df.iterrows():
        dt = parse_datetime(row.get("date"))
        sh = SalesHistory(
            product_name=row.get("product_name") or row.get("product"),
            date=dt,
            sales=float(row.get("sales")) if not pd.isna(row.get("sales")) else None,
        )
        session.add(sh)
    session.commit()
    print("Sales history loaded")


def load_returns(session):
    path = os.path.join(DATA_DIR, "returns.csv")
    if not os.path.exists(path):
        print("returns.csv not found, skipping")
        return
    df = pd.read_csv(path)
    for _, row in df.iterrows():
        dt = parse_datetime(row.get("date"))
        r = ReturnRecord(
            product_name=row.get("product_name") or row.get("product"),
            date=dt,
            quantity=int(row.get("quantity")) if not pd.isna(row.get("quantity")) else None,
            reason=row.get("reason"),
        )
        session.add(r)
    session.commit()
    print("Returns loaded")


def load_suppliers(session):
    path = os.path.join(DATA_DIR, "supplier.csv")
    if not os.path.exists(path):
        print("supplier.csv not found, skipping")
        return
    df = pd.read_csv(path)
    for _, row in df.iterrows():
        s = Supplier(
            supplier_name=row.get("supplier_name"),
            product_name=row.get("product_name"),
            lead_time_days=int(row.get("lead_time_days")) if not pd.isna(row.get("lead_time_days")) else None,
        )
        session.add(s)
    session.commit()
    print("Suppliers loaded")


def main():
    # ensure tables exist
    init_db()
    session = SessionLocal()
    try:
        load_products(session)
        load_reorders(session)
        load_discount_audit(session)
        load_ai_recommendations(session)
        load_forecasts(session)
        load_alerts(session)
        load_users(session)
        load_sales_history(session)
        load_returns(session)
        load_suppliers(session)
    finally:
        session.close()


if __name__ == "__main__":
    main()
