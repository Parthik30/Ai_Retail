from backend.data import products as PRODUCTS
from backend.services.inventory_service import calculate_inventory_status, inventory_turnover
from backend.services.pricing_service import calculate_final_price, calculate_profit
from backend.services.discount_service import recommend_discount, get_active_festival

import pandas as pd
import numpy as np
from pathlib import Path
import os
from datetime import date
from typing import Optional, Dict


def _load_csv_if_exists(base_dir: Path, filename: str) -> Optional[pd.DataFrame]:
    path = base_dir / "data" / filename
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def compute_data_quality(base_dir: Path) -> Dict[str, Dict]:
    """Return data quality metrics (percent missing, rows) for supported datasets.
    Prefer DB tables when available, otherwise fall back to CSV files."""
    datasets = ["products.csv", "sales_history.csv", "returns.csv", "supplier.csv"]
    out = {}
    try:
        from ..db import engine, SessionLocal
        from sqlalchemy import inspect
        from ..models import SalesHistory, ReturnRecord, Supplier, Product
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
    except Exception:
        inspector = None
        table_names = []

    for ds in datasets:
        # map dataset filename to expected table name
        mapping = {
            "products.csv": ("product", Product) if 'product' in table_names or 'products' in table_names else (None, None),
            "sales_history.csv": ("sales_history", SalesHistory) if "sales_history" in table_names else (None, None),
            "returns.csv": ("returns", ReturnRecord) if "returns" in table_names else (None, None),
            "supplier.csv": ("supplier", Supplier) if "supplier" in table_names else (None, None),
        }
        table_name, model = mapping.get(ds, (None, None))
        if table_name and model is not None:
            # compute rows and a crude missing_pct estimate
            try:
                session = SessionLocal()
                count = session.query(model).count()
                # attempt to estimate missing pct by sampling up to 100 rows
                sample = session.query(model).limit(100).all()
                if sample:
                    import pandas as _pd
                    df_sample = _pd.DataFrame([s.__dict__ for s in sample])
                    # remove SQLAlchemy internal keys
                    df_sample = df_sample.loc[:, ~df_sample.columns.str.startswith('_')]
                    total = df_sample.size if df_sample.size else 1
                    missing = int(df_sample.isnull().sum().sum())
                    pct = round((missing / total) * 100, 2)
                else:
                    pct = 0.0
                session.close()
                out[ds] = {"exists": True, "missing_pct": pct, "rows": count}
                continue
            except Exception:
                out[ds] = {"exists": True, "missing_pct": None, "rows": None}
                continue
        # fallback to CSV
        df = _load_csv_if_exists(base_dir, ds)
        if df is None:
            out[ds] = {"exists": False, "missing_pct": None, "rows": 0}
        else:
            total = df.size if df.size else 1
            missing = int(df.isnull().sum().sum())
            pct = round((missing / total) * 100, 2)
            out[ds] = {"exists": True, "missing_pct": pct, "rows": len(df)}
    return out


def _load_product_from_csv(product_name):
    # Try DB first
    try:
        from backend.db import SessionLocal
        from backend.models import Product
        session = SessionLocal()
        prod = session.query(Product).filter(Product.product_name == product_name).one_or_none()
        session.close()
        if prod:
            return {
                "price": prod.selling_price or prod.cost_price or 0.0,
                "cost": prod.cost_price or 0.0,
                "sales": int(prod.monthly_sales or 0),
                "stock": int(prod.stock or 0),
                "discount": float(prod.discount or 0.0)
            }
    except Exception:
        # DB not available or error -> fallback to CSV
        pass

    base_dir = Path(__file__).resolve().parents[1]
    csv_path = base_dir / "data" / "products.csv"
    if not csv_path.exists():
        return None
    df = pd.read_csv(csv_path)
    row = df[df["product_name"] == product_name]
    if row.empty:
        return None
    r = row.iloc[0].to_dict()
    # Normalize keys to expected structure
    return {
        "price": r.get("selling_price") or r.get("price") or r.get("selling_price"),
        "cost": r.get("cost_price") or r.get("cost"),
        "sales": int(r.get("monthly_sales") or r.get("sales") or 0),
        "stock": int(r.get("stock") or 0),
        "discount": float(r.get("discount") or 0)
    }


def _load_sales_from_db(product_name: str):
    try:
        from ..db import SessionLocal
        from ..models import SalesHistory
        session = SessionLocal()
        rows = session.query(SalesHistory).filter(SalesHistory.product_name == product_name).order_by(SalesHistory.date).all()
        session.close()
        if not rows:
            return None
        import pandas as _pd
        df = _pd.DataFrame([{"date": r.date, "sales": r.sales} for r in rows])
        return df
    except Exception:
        return None


def _aggregate_sales_series(sales_df: pd.DataFrame, product_name: str):
    """Return a monthly sales series (list) for the last 12 months if available."""
    if sales_df is None or (hasattr(sales_df, 'empty') and sales_df.empty):
        # attempt DB fallback
        sales_df = _load_sales_from_db(product_name)
        if sales_df is None:
            return []

    # Support common schemas: 'product_name','year','month','sales' or 'date','sales'
    df = sales_df.copy()
    if "product_name" in df.columns:
        df = df[df["product_name"] == product_name]
    if df.empty:
        return []

    if "date" in df.columns:
        # try to parse date and extract year-month
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        df["ym"] = df["date"].dt.to_period("M")
        agg = df.groupby("ym")["sales"].sum().sort_index()
    elif "year" in df.columns and "month" in df.columns:
        df["ym"] = pd.to_datetime(df["year"].astype(int).astype(str) + "-" + df["month"].astype(int).astype(str) + "-01", errors="coerce")
        df = df.dropna(subset=["ym"])
        df["ym"] = df["ym"].dt.to_period("M")
        agg = df.groupby("ym")["sales"].sum().sort_index()
    else:
        # fallback: use any column named 'sales' aggregated by index order
        if "sales" in df.columns:
            agg = df["sales"].astype(float).reset_index(drop=True)
            return agg.tail(12).tolist()
        return []

    # Return last 12 months (most recent months)
    agg = agg.sort_index()
    last = agg.tail(12)
    return [float(x) for x in last.tolist()]


def _classify_abc(df_products: pd.DataFrame) -> Dict[str, str]:
    """Return mapping product_name -> ABC class based on revenue contribution."""
    if df_products is None or df_products.empty:
        return {}
    df = df_products.copy()
    df["revenue"] = (df["selling_price"].fillna(0) * df["monthly_sales"].fillna(0)).astype(float)
    df = df.sort_values("revenue", ascending=False)
    total = df["revenue"].sum() if df["revenue"].sum() else 1
    df["cum_pct"] = df["revenue"].cumsum() / total * 100

    mapping = {}
    for _, r in df.iterrows():
        pct = r["cum_pct"]
        if pct <= 20:
            mapping[r["product_name"]] = "A"
        elif pct <= 50:
            mapping[r["product_name"]] = "B"
        else:
            mapping[r["product_name"]] = "C"
    return mapping


def _classify_xyz(sales_series: list) -> Dict:
    """Return XYZ label and stats based on coefficient of variation and seasonality heuristics."""
    if not sales_series:
        return {"xyz": "X", "cv": 0.0, "seasonality": "REGULAR"}
    arr = np.array(sales_series)
    mu = arr.mean()
    std = arr.std()
    cv = float(std / (abs(mu) + 1e-9))

    if cv <= 0.25:
        xyz = "X"  # stable
    elif cv <= 0.6:
        xyz = "Y"  # seasonal/medium
    else:
        xyz = "Z"  # irregular

    # Simple seasonality detection: check if some months have spikes relative to monthly mean
    # We consider seasonal if max month > mean + 2*std
    seasonality = "REGULAR"
    if arr.size >= 3:
        if arr.max() > mu + 2 * std:
            seasonality = "SEASONAL"
    return {"xyz": xyz, "cv": round(cv, 3), "seasonality": seasonality}


def ai_predict_classification(product_row: pd.Series, sales_series: list) -> Dict:
    """Provide a simple AI-style prediction for value_class (A/B/C) and demand_pattern (X/Y/Z).

    This is a heuristic placeholder that simulates an AI prediction and returns confidence.
    """
    # Use available signals: revenue rank, coefficient of variation, and history availability
    # Compute revenue metric
    try:
        revenue = float(product_row.get("selling_price", 0)) * float(product_row.get("monthly_sales", 0))
    except Exception:
        revenue = 0.0

    history_len = len(sales_series) if sales_series is not None else 0
    xyz_info = _classify_xyz(sales_series) if history_len else {"xyz": "X", "cv": 0.0, "seasonality": "REGULAR"}

    # Value class prediction by revenue bucket (relative ranking not available here; use thresholds)
    if revenue > 200000:
        pred_value = "A"
    elif revenue > 50000:
        pred_value = "B"
    else:
        pred_value = "C"

    # Demand pattern prediction from cv
    cv = xyz_info.get("cv", 0.0)
    if cv <= 0.25:
        pred_pattern = "X"
    elif cv <= 0.6:
        pred_pattern = "Y"
    else:
        pred_pattern = "Z"

    # Confidence: higher if history exists and revenue is sizeable and CV is clearly in a bucket
    conf = 0.3
    if history_len >= 6:
        conf += 0.4
    if revenue > 100000:
        conf += 0.2
    # penalize near-boundary CV values
    if 0.22 < cv < 0.28 or 0.55 < cv < 0.65:
        conf -= 0.15
    conf = max(0.05, min(0.99, round(conf, 2)))

    return {"ai_value": pred_value, "ai_pattern": pred_pattern, "ai_confidence": conf}


def get_demand_pattern_classification(base_dir: Path = None, product_name: str = None) -> pd.DataFrame:
    """Return a DataFrame with value_class/demand_pattern/seasonality classifications.
    If product_name is provided, only processes and returns that single product for efficiency.
    """
    base_dir = Path(__file__).resolve().parents[1] if base_dir is None else Path(base_dir)

    # Merge DB and CSV products to ensure catalog is always full
    prods_list = []
    try:
        from ..db import SessionLocal
        from ..models import Product
        session = SessionLocal()
        db_prods = session.query(Product).all()
        session.close()
        if db_prods:
            prods_list = [{
                "product_name": p.product_name,
                "selling_price": float(p.selling_price or 0),
                "cost_price": float(p.cost_price or 0),
                "monthly_sales": int(p.monthly_sales or 0),
                "stock": int(p.stock or 0),
                "category": p.category or "Other"
            } for p in db_prods]
    except Exception:
        pass

    csv_df = _load_csv_if_exists(base_dir, "products.csv")
    if csv_df is not None:
        csv_list = csv_df.to_dict('records')
        # Combine lists, preferring DB if same name
        seen_names = {p['product_name'] for p in prods_list}
        for cp in csv_list:
            if cp['product_name'] not in seen_names:
                prods_list.append(cp)
    
    prod_df = pd.DataFrame(prods_list)

    sales_df = _load_csv_if_exists(base_dir, "sales_history.csv")

    if prod_df is None:
        return pd.DataFrame(columns=["product_name", "value_class", "demand_pattern", "seasonality", "cv", "sales_history_available", "ai_value", "ai_pattern", "ai_confidence"])

    abc_map = _classify_abc(prod_df)

    rows = []
    # If product_name is provided, filter the prod_df loop
    target_prods = prod_df[prod_df["product_name"] == product_name] if product_name else prod_df
    
    for _, r in target_prods.iterrows():
        name = r["product_name"]
        sales_series = _aggregate_sales_series(sales_df, name)
        xyz_info = _classify_xyz(sales_series)
        ai = ai_predict_classification(r, sales_series)
        rows.append({
            "product_name": name,
            "value_class": abc_map.get(name, "C"),
            "demand_pattern": xyz_info["xyz"],
            "seasonality": xyz_info["seasonality"],
            "cv": xyz_info["cv"],
            "sales_history_available": bool(len(sales_series) > 0),
            "ai_value": ai.get("ai_value"),
            "ai_pattern": ai.get("ai_pattern"),
            "ai_confidence": ai.get("ai_confidence")
        })

    df = pd.DataFrame(rows)
    # Normalize column order for consumers
    cols = ["product_name", "value_class", "ai_value", "ai_confidence", "demand_pattern", "seasonality", "cv", "sales_history_available", "ai_pattern"]
    if not df.empty:
        # ensure ai_confidence is float
        df["ai_confidence"] = df["ai_confidence"].astype(float)
        return df[cols]
    return df


def get_dashboard_data(product, on_date: date = None):
    # Prefer CSV first, then in-memory PRODUCTS dict as fallback
    if on_date is None:
        on_date = date.today()

    base_dir = Path(__file__).resolve().parents[1]

    p = _load_product_from_csv(product)
    if p is None:
        if product in PRODUCTS:
            p = PRODUCTS[product]
        else:
            raise ValueError(f"Product '{product}' not found in data sources")

    # Compute data quality summary
    dq = compute_data_quality(base_dir)
    # Aggregate a simple data health score: 100 - average missing % across existing datasets
    missing_vals = [v["missing_pct"] for v in dq.values() if v["exists"] and v["missing_pct"] is not None]
    avg_missing = float(np.mean(missing_vals)) if missing_vals else 0.0
    data_health_score = round(max(0.0, min(100.0, 100.0 - avg_missing)), 1)

    demand = "HIGH" if p["sales"] > 150 else "MEDIUM"
    discount = recommend_discount(p["stock"], demand, on_date=on_date)
    active_fest = get_active_festival(on_date)

    final_price = calculate_final_price(p["price"], discount)
    profit = calculate_profit(final_price, p["cost"], p["sales"])
    inventory = calculate_inventory_status(p["sales"], p["stock"])

    result = {
        "sales": p["sales"],
        "stock": p["stock"],
        "price": p["price"],
        "discount": discount,
        "final_price": final_price,
        "profit": profit,
        "inventory_status": inventory["status"],
        "reorder_qty": inventory["reorder_qty"],
        "turnover": inventory_turnover(p["sales"], p["stock"]),
        "data_health_score": data_health_score,
        "data_quality": dq
    }

    if active_fest:
        result["festival"] = active_fest[0]
        result["festival_bonus"] = active_fest[1]

    # Demand pattern classification for selected product (ABC/XYZ/seasonality)
    try:
        patterns = get_demand_pattern_classification(base_dir, product_name=product)
        row = patterns[patterns["product_name"] == product]
        if not row.empty:
            row = row.iloc[0]
            result["value_class"] = row["value_class"]
            result["demand_pattern"] = row["demand_pattern"]
            result["seasonality"] = row["seasonality"]
            result["cv"] = float(row["cv"])
            result["sales_history_available"] = bool(row["sales_history_available"])
            result["ai_value"] = row.get("ai_value")
            result["ai_pattern"] = row.get("ai_pattern")
            result["ai_confidence"] = float(row.get("ai_confidence") or 0.0)
        else:
            result["value_class"] = "C"
            result["demand_pattern"] = "X"
            result["seasonality"] = "REGULAR"
            result["cv"] = 0.0
            result["sales_history_available"] = False
            result["ai_value"] = None
            result["ai_pattern"] = None
            result["ai_confidence"] = 0.0
    except Exception:
        result["value_class"] = "C"
        result["demand_pattern"] = "X"
        result["seasonality"] = "REGULAR"
        result["cv"] = 0.0
        result["sales_history_available"] = False
        result["ai_value"] = None
        result["ai_pattern"] = None
        result["ai_confidence"] = 0.0

    return result
