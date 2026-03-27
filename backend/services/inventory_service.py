"""
Inventory Service
Handles inventory status, reorder logic, and risk detection
"""

def calculate_reorder_point(sales, lead_time_days=5):
    """
    Calculate reorder point based on average demand
    """
    avg_daily_demand = sales / 30  # assume 30-day period
    return int(avg_daily_demand * lead_time_days)


def calculate_inventory_status(sales, stock):
    """
    Determine inventory risk and reorder quantity
    """
    reorder_point = calculate_reorder_point(sales)

    if stock <= reorder_point:
        return {
            "status": "STOCK_OUT_RISK",
            "reorder_qty": reorder_point * 2,
            "health": "Critical"
        }

    elif stock >= reorder_point * 4:
        return {
            "status": "OVERSTOCK_RISK",
            "reorder_qty": 0,
            "health": "Excess"
        }

    else:
        return {
            "status": "SAFE",
            "reorder_qty": 0,
            "health": "Good"
        }


def calculate_inventory_status(sales, stock):
    reorder_point = sales // 6

    if stock < reorder_point:
        return {"status": "STOCK_OUT_RISK", "reorder_qty": reorder_point * 2}
    elif stock > reorder_point * 4:
        return {"status": "OVERSTOCK_RISK", "reorder_qty": 0}
    else:
        return {"status": "SAFE", "reorder_qty": 0}


def inventory_turnover(sales, stock):
    if stock == 0:
        return 0
    return round(sales / stock, 2)


def predict_stock(current_stock, monthly_sales, months=1, demand_level='MEDIUM', lead_time_days=7):
    """
    Predict stock level after 'months' months using a simple rule-based model.

    - monthly_sales: current average monthly sales
    - months: how many months ahead to predict
    - demand_level: 'LOW', 'MEDIUM', 'HIGH' to model expected demand change
    - lead_time_days: used to estimate reorder quantity if stockouts are predicted

    This function returns the predicted stock level after the given months (int).
    """
    series_info = predict_stock_series(current_stock, monthly_sales, months, demand_level, lead_time_days)
    return series_info["series"][-1]


def predict_stock_series(current_stock, monthly_sales, months=1, demand_level='MEDIUM', lead_time_days=7, safety_stock_pct=0.2, target_cover_months=None):
    """
    Return a month-by-month predicted stock series and diagnostics.

    Improvements over the previous simple model:
    - Simulate deliveries arriving after lead time (in months granularity)
    - Place reorder quantities large enough to cover lead time demand + safety buffer
    - Count stockout months when stock is negative at month-end

    Parameters:
    - safety_stock_pct: fraction of monthly demand to hold as safety stock (e.g., 0.2 for 20%)
    - target_cover_months: if provided, use this many months as target coverage for reorder; otherwise use lead_months + 1

    Returns: {"series": [...], "stockout_months": int, "min_stock": int, "pending_deliveries": dict, "recommended_reorders": list}
    """
    import math
    import os
    from datetime import datetime

    growth_factors = {'HIGH': 1.10, 'MEDIUM': 1.0, 'LOW': 0.95}
    factor = growth_factors.get(demand_level, 1.0)

    series = []
    stock = float(current_stock or 0.0)
    monthly = float(monthly_sales or 0.0)
    stockout_months = 0

    # pending deliveries: map month_index -> qty
    pending = {}

    # list of recommended reorders placed during simulation
    recommended_reorders = []

    # convert lead_time_days to months (ceil). At least 0 (same month) if lead_time small
    lead_months = int(math.ceil(lead_time_days / 30.0))

    # base reorder point (daily avg * lead days)
    base_reorder_point = calculate_reorder_point(int(monthly_sales or 0), lead_time_days)

    # dynamic safety stock based on configured pct
    safety_stock = max(1, int(round(safety_stock_pct * monthly)))

    for m in range(1, months + 1):
        # receive any pending deliveries due this month
        if m in pending:
            stock += pending.pop(m)

        # demand for this month (before growth for next month)
        demand = monthly
        stock -= demand

        # apply growth to the 'monthly' forecast for next month
        monthly = monthly * factor

        # Determine if we should place an order while considering lead time
        # Place order when stock at end of month <= base_reorder_point + safety_stock
        if stock <= (base_reorder_point + safety_stock):
            # compute reorder qty to cover desired target months
            projected_cover = target_cover_months if (target_cover_months and target_cover_months > 0) else max(1, lead_months + 1)
            projected_demand = projected_cover * monthly
            reorder_qty = max(int(round(projected_demand)), base_reorder_point * 3, int(round(monthly * 1.5)))

            arrival_month = m + lead_months
            pending[arrival_month] = pending.get(arrival_month, 0) + reorder_qty

            # record recommendation event
            recommended_reorders.append({
                "place_month": m,
                "arrival_month": arrival_month,
                "reorder_qty": int(reorder_qty),
                "projected_cover_months": int(projected_cover)
            })

        # track stockouts (month ended negative)
        if stock < 0:
            stockout_months += 1

        series.append(int(round(stock)))

    min_stock = int(min(series) if series else int(round(stock)))
    return {
        "series": series,
        "stockout_months": stockout_months,
        "min_stock": min_stock,
        "pending_deliveries": pending,
        "recommended_reorders": recommended_reorders
    }


def log_reorder(product_name, reorder_qty, arrival_month, placed_by="system", note=None):
    """Record a reorder.

    Tries to insert into the `reorders` DB table first; falls back to appending CSV for compatibility.
    """
    from datetime import datetime
    try:
        # DB path
        from ..db import SessionLocal
        from ..models import Reorder
        session = SessionLocal()
        r = Reorder(product=product_name, quantity=int(reorder_qty), eta_month=int(arrival_month), placed_by=placed_by)
        session.add(r)
        session.commit()
        session.close()
        return True
    except Exception:
        # fallback to CSV
        import os
        import csv
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(data_dir, exist_ok=True)
        csv_path = os.path.join(data_dir, "reorders.csv")
        fieldnames = ["timestamp", "product_name", "reorder_qty", "arrival_month", "placed_by", "note", "status"]

        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "product_name": product_name,
            "reorder_qty": reorder_qty,
            "arrival_month": arrival_month,
            "placed_by": placed_by,
            "note": note or "",
            "status": "PLACED"
        }

        write_header = not os.path.exists(csv_path)
        try:
            with open(csv_path, "a", newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if write_header:
                    writer.writeheader()
                writer.writerow(record)
            return True
        except Exception:
            return False


