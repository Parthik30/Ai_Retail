from datetime import date
from typing import Optional, Tuple
import os


def calculate_final_price(price, discount):
    return round(price * (1 - discount / 100), 2)


def calculate_profit(price, cost, sales):
    return round((price - cost) * sales, 2)


# Festival configuration: approximate windows and extra discount %
FESTIVALS = {
    "diwali": {"months": [10, 11], "bonus": 10},          # Oct-Nov
    "black_friday": {"months": [11], "days": range(24, 30), "bonus": 20},
    "christmas": {"months": [12], "days": range(24, 27), "bonus": 15},
    "new_year": {"months": [12, 1], "days": range(30, 32), "bonus": 10},
    "summer_sale": {"months": [6, 7], "bonus": 5}
}


def _detect_festival(d: date) -> Optional[str]:
    """Return the festival name if the date falls within any configured festival window."""
    for name, cfg in FESTIVALS.items():
        months = cfg.get("months", [])
        days = cfg.get("days", None)
        if d.month in months:
            if days is None:
                return name
            if d.day in days:
                return name
    return None


def recommend_discount(stock: int, demand: str, on_date: Optional[date] = None, festival: Optional[str] = None) -> int:
    """
    Recommend discount percentage based on stock, demand and optional festival.

    Parameters:
    - stock: current stock level
    - demand: one of 'HIGH', 'MEDIUM', 'LOW'
    - on_date: optional date to check festival windows (defaults to today)
    - festival: optional explicit festival name to force bonus

    Returns: integer discount percentage
    """
    if on_date is None:
        on_date = date.today()

    # Base discount by demand and stock
    demand = (demand or "").upper()
    base = 0

    if demand == "LOW":
        # Clearance: large stock with low demand
        if stock > 150:
            base = 25
        elif stock > 100:
            base = 20
        elif stock > 50:
            base = 12
        else:
            base = 8
    elif demand == "MEDIUM":
        if stock > 150:
            base = 15
        elif stock > 100:
            base = 10
        elif stock > 50:
            base = 6
        else:
            base = 2
    elif demand == "HIGH":
        # High demand means low or no discount
        if stock > 200:
            base = 8  # overstock despite high demand
        else:
            base = 0
    else:
        # Unknown demand, fallback conservative
        if stock > 150:
            base = 10
        elif stock > 100:
            base = 6
        else:
            base = 0

    # Festival bonus
    festival_name = festival or _detect_festival(on_date)
    bonus = 0
    if festival_name and festival_name in FESTIVALS:
        bonus = FESTIVALS[festival_name].get("bonus", 0)

    # Final discount capped between 0 and 50
    discount = max(0, min(50, base + bonus))
    return int(discount)


def get_active_festival(on_date: Optional[date] = None) -> Optional[Tuple[str, int]]:
    """Return (festival_name, bonus%) if active on the given date, else None."""
    if on_date is None:
        on_date = date.today()
    name = _detect_festival(on_date)
    if name:
        return name, FESTIVALS[name].get("bonus", 0)
    return None


# ---------- AI Discount Recommendation ----------
from typing import Dict
import math


def ai_recommend_discount(product: Dict, max_discount: int = 30, objective: str = "profit") -> Dict:
    """Recommend a discount using a simple elasticity-based simulated search.

    Parameters:
    - product: mapping or pandas Series containing keys: 'selling_price', 'cost_price' or 'cost', 'monthly_sales', 'stock', 'demand_level'
    - max_discount: maximum discount percent to consider
    - objective: 'profit' or 'revenue' to optimise for

    Returns a dict with: recommended_discount, expected_units, expected_revenue, expected_profit, confidence
    """
    # Extract product data with safe defaults
    price = float(product.get("selling_price", product.get("price", 0.0)))
    cost = float(product.get("cost_price", product.get("cost", 0.0)))
    monthly_sales = float(product.get("monthly_sales", 0.0))
    stock = float(product.get("stock", 0.0))
    demand = (product.get("demand_level", "MEDIUM") or "MEDIUM").upper()

    # Basic elasticity assumptions by demand level (units change % per 1% price change)
    elasticity_map = {
        "HIGH": 0.5,    # inelastic (lower responsiveness)
        "MEDIUM": 1.0,
        "LOW": 1.6      # very price sensitive
    }
    elasticity = elasticity_map.get(demand, 1.0)

    # Festival uplift (if any) — use bonus% as additional uplift applied to baseline demand
    fest = get_active_festival()
    festival_uplift = 0.0
    if fest:
        festival_uplift = fest[1] / 100.0

    # Safety guards
    if price <= 0 or monthly_sales < 0:
        return {
            "recommended_discount": 0,
            "expected_units": monthly_sales,
            "expected_revenue": monthly_sales * price,
            "expected_profit": monthly_sales * (price - cost),
            "confidence": 0.0,
        }

    best = {
        "discount": 0,
        "revenue": monthly_sales * price,
        "profit": monthly_sales * (price - cost),
        "units": monthly_sales
    }

    # Evaluate candidate discounts from 0..max_discount
    for d in range(0, max_discount + 1):
        # percent price reduction
        price_after = price * (1 - d/100.0)
        if price_after < cost * 0.9:
            # don't consider discounts that go too far below cost (90% cost floor)
            continue

        # demand uplift from discount: approximate percent increase in quantity
        # using elasticity: %ΔQ = elasticity * %ΔP (but %ΔP is negative for price reduction)
        pct_price_change = -d  # negative percent
        pct_qty_change = elasticity * (-pct_price_change) / 100.0  # positive factor

        projected_units = monthly_sales * (1 + pct_qty_change + festival_uplift)

        # If stock is limited, cap units to available stock as we cannot sell more than stock in short term
        projected_units = min(projected_units, stock + monthly_sales * 0.5)  # allow partial restock effect

        projected_revenue = projected_units * price_after
        projected_profit = projected_units * (price_after - cost)

        if objective == "revenue":
            score = projected_revenue
        else:
            # prefer profit by default; penalize strategies that produce negative profit
            score = projected_profit

        # Replace if better
        key = "revenue" if objective == "revenue" else "profit"
        if score > best[key]:
            best = {"discount": d, "revenue": projected_revenue, "profit": projected_profit, "units": projected_units}

    # Confidence heuristic: higher when monthly_sales and stock are sizable
    conf = min(0.99, 0.1 + (min(monthly_sales, max(1.0, stock)) / (max(1.0, monthly_sales) + 50.0)))
    conf = round(conf, 2)

    rec = {
        "recommended_discount": int(best["discount"]),
        "expected_units": int(round(best["units"])),
        "expected_revenue": round(best["revenue"], 2),
        "expected_profit": round(best["profit"], 2),
        "confidence": conf,
    }

    # Return recommendation; logging is done by caller (UI) when user saves or applies
    return rec


# ---------- Recommendation logging / undo ----------
import uuid
import pandas as pd
from datetime import datetime

RECO_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ai_recommendations.csv")


def _ensure_reco_file():
    if not os.path.exists(RECO_FILE):
        os.makedirs(os.path.dirname(RECO_FILE), exist_ok=True)
        df = pd.DataFrame(columns=["id","timestamp","product","objective","suggested_discount","expected_units","expected_revenue","expected_profit","confidence","applied","applied_at","applied_by","prev_discount","prev_price","note"])
        df.to_csv(RECO_FILE, index=False)


def log_ai_recommendation(product_name: str, objective: str, rec: Dict, prev_discount: int, prev_price: float, note: str = "") -> str:
    """Log a recommendation and return its id.

    Attempts to write to the database first; falls back to CSV file when DB is unavailable.
    """
    rid = str(uuid.uuid4())
    ts = datetime.utcnow()

    # Try DB first
    try:
        from ..db import SessionLocal
        from ..models import AIRecommendation
        session = SessionLocal()
        ai = AIRecommendation(
            id=rid,
            timestamp=ts,
            product=product_name,
            objective=objective,
            suggested_discount=int(rec.get("recommended_discount", 0)),
            expected_units=int(rec.get("expected_units", 0)),
            expected_revenue=float(rec.get("expected_revenue", 0.0)),
            expected_profit=float(rec.get("expected_profit", 0.0)),
            confidence=float(rec.get("confidence", 0.0)),
            applied=False,
            applied_at=None,
            applied_by=None,
            prev_discount=int(prev_discount),
            prev_price=float(prev_price),
            note=note,
        )
        session.add(ai)
        session.commit()
        session.close()
        return rid
    except Exception:
        # fallback to CSV
        _ensure_reco_file()
        row = {
            "id": rid,
            "timestamp": ts.isoformat(),
            "product": product_name,
            "objective": objective,
            "suggested_discount": int(rec.get("recommended_discount", 0)),
            "expected_units": int(rec.get("expected_units", 0)),
            "expected_revenue": float(rec.get("expected_revenue", 0.0)),
            "expected_profit": float(rec.get("expected_profit", 0.0)),
            "confidence": float(rec.get("confidence", 0.0)),
            "applied": False,
            "applied_at": "",
            "applied_by": "",
            "prev_discount": int(prev_discount),
            "prev_price": float(prev_price),
            "note": note
        }
        df = pd.read_csv(RECO_FILE)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_csv(RECO_FILE, index=False)
        return rid


def mark_recommendation_applied(rid: str, applied_by: str = "AI") -> bool:
    """Mark the recommendation as applied. Tries DB first, falls back to CSV."""
    try:
        from ..db import SessionLocal
        from ..models import AIRecommendation
        session = SessionLocal()
        ai = session.query(AIRecommendation).filter(AIRecommendation.id == rid).one_or_none()
        if ai is None:
            session.close()
            # fallback to CSV
            raise LookupError("not found in DB")
        ai.applied = True
        ai.applied_at = datetime.utcnow()
        ai.applied_by = applied_by
        session.add(ai)
        session.commit()
        session.close()
        return True
    except Exception:
        # fallback to CSV
        _ensure_reco_file()
        df = pd.read_csv(RECO_FILE)
        idx = df.index[df["id"] == rid]
        if len(idx) == 0:
            return False
        i = idx[0]
        df.at[i, "applied"] = True
        df.at[i, "applied_at"] = datetime.utcnow().isoformat()
        df.at[i, "applied_by"] = applied_by
        df.to_csv(RECO_FILE, index=False)
        return True


def undo_recommendation(rid: str, user: str = "user") -> bool:
    """Undo an applied recommendation by restoring previous discount & price.

    Returns True if undone, False on failure. Uses DB when available and falls back to CSV.
    """
    try:
        from ..db import SessionLocal
        from ..models import AIRecommendation, Product
        session = SessionLocal()
        ai = session.query(AIRecommendation).filter(AIRecommendation.id == rid).one_or_none()
        if ai is None or not ai.applied:
            session.close()
            return False

        product_name = ai.product
        prev_discount = int(ai.prev_discount or 0)
        prev_price = float(ai.prev_price or 0.0)

        # restore product in DB
        prod = session.query(Product).filter(Product.product_name == product_name).one_or_none()
        if prod is None:
            # cannot restore product not in DB
            session.close()
            return False
        prod.discount = prev_discount
        prod.selling_price = prev_price
        # mark recommendation undone
        ai.applied = False
        ai.applied_at = None
        ai.applied_by = f"undone_by:{user}:{datetime.utcnow().isoformat()}"
        ai.note = (str(ai.note) or "") + " | undone"
        session.add(prod)
        session.add(ai)
        session.commit()
        session.close()
        return True
    except Exception:
        # fallback to CSV implementation
        _ensure_reco_file()
        df = pd.read_csv(RECO_FILE)
        idx = df.index[df["id"] == rid]
        if len(idx) == 0:
            return False
        i = idx[0]
        if not df.at[i, "applied"]:
            return False

        product = df.at[i, "product"]
        prev_discount = int(df.at[i, "prev_discount"])
        prev_price = float(df.at[i, "prev_price"])

        # restore CSV
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "products.csv")
        if not os.path.exists(csv_path):
            return False
        csv_df = pd.read_csv(csv_path)
        mask = csv_df["product_name"] == product
        if not mask.any():
            return False
        csv_df.loc[mask, "discount"] = prev_discount
        csv_df.loc[mask, "selling_price"] = prev_price
        csv_df.to_csv(csv_path, index=False)

        # mark undone (applied -> False and add note)
        df.at[i, "applied"] = False
        df.at[i, "applied_at"] = ""
        df.at[i, "applied_by"] = f"undone_by:{user}:{datetime.utcnow().isoformat()}"
        df.at[i, "note"] = (str(df.at[i, "note"]) or "") + " | undone"
        df.to_csv(RECO_FILE, index=False)
        return True


def get_recent_recommendations(limit: int = 20) -> pd.DataFrame:
    """Return recent recommendations as a DataFrame. Prefer DB when available."""
    try:
        from ..db import SessionLocal
        from ..models import AIRecommendation
        session = SessionLocal()
        rows = session.query(AIRecommendation).order_by(AIRecommendation.timestamp.desc()).limit(limit).all()
        session.close()
        if not rows:
            return pd.DataFrame()
        data = []
        for r in rows:
            data.append({
                "id": r.id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                "product": r.product,
                "objective": r.objective,
                "suggested_discount": int(r.suggested_discount or 0),
                "expected_units": int(r.expected_units or 0),
                "expected_revenue": float(r.expected_revenue or 0.0),
                "expected_profit": float(r.expected_profit or 0.0),
                "confidence": float(r.confidence or 0.0),
                "applied": bool(r.applied),
                "applied_at": r.applied_at.isoformat() if r.applied_at else "",
                "applied_by": r.applied_by or "",
                "prev_discount": int(r.prev_discount or 0),
                "prev_price": float(r.prev_price or 0.0),
                "note": r.note or ""
            })
        return pd.DataFrame(data)
    except Exception:
        _ensure_reco_file()
        df = pd.read_csv(RECO_FILE)
        if df.empty:
            return df
        df = df.sort_values("timestamp", ascending=False).head(limit)
        return df


# ---------------- Audit logging ----------------
import csv


def log_discount_change(product: str, old_discount: int, new_discount: int, user: Optional[str] = None, note: Optional[str] = None, audit_path: Optional[str] = None):
    """Append an audit record for a discount change.

    Uses DB when available; otherwise falls back to CSV audit file.
    Fields: timestamp, product, old_discount, new_discount, user, note
    """
    ts = datetime.utcnow()
    try:
        from ..db import SessionLocal
        from ..models import DiscountAudit
        session = SessionLocal()
        audit = DiscountAudit(
            timestamp=ts,
            product=product,
            old_discount=old_discount,
            new_discount=new_discount,
            user=user or "",
            note=note or ""
        )
        session.add(audit)
        session.commit()
        session.close()
        return
    except Exception:
        # fallback to CSV audit file
        ts_s = date.today().isoformat()
        if audit_path is None:
            # default audit path under backend/data
            audit_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "discount_audit.csv")

        header = ["timestamp", "product", "old_discount", "new_discount", "user", "note"]
        row = [ts_s, product, old_discount, new_discount, user or "", note or ""]

        write_header = not os.path.exists(audit_path)
        os.makedirs(os.path.dirname(audit_path), exist_ok=True)
        with open(audit_path, "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(header)
            writer.writerow(row)


def log_price_change(product: str, old_price: float, new_price: float, user: Optional[str] = None, note: Optional[str] = None, audit_path: Optional[str] = None):
    """Append an audit record for a price change.

    Uses DB when available; otherwise falls back to CSV audit file.
    Fields: timestamp, product, old_price, new_price, user, note
    """
    ts = datetime.utcnow()
    try:
        from ..db import SessionLocal
        from ..models import PriceAudit
        session = SessionLocal()
        audit = PriceAudit(
            timestamp=ts,
            product=product,
            old_price=old_price,
            new_price=new_price,
            user=user or "",
            note=note or ""
        )
        session.add(audit)
        session.commit()
        session.close()
        return
    except Exception:
        # fallback to CSV audit file
        ts_s = date.today().isoformat()
        if audit_path is None:
            # default audit path under backend/data
            audit_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "price_audit.csv")

        header = ["timestamp", "product", "old_price", "new_price", "user", "note"]
        row = [ts_s, product, old_price, new_price, user or "", note or ""]

        write_header = not os.path.exists(audit_path)
        os.makedirs(os.path.dirname(audit_path), exist_ok=True)
        with open(audit_path, "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(header)
            writer.writerow(row)
