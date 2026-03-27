from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
)
from .db import Base
import datetime


class Product(Base):
    __tablename__ = "products"

    product_id = Column(String, primary_key=True, index=True)
    product_name = Column(String, unique=True, nullable=False)
    category = Column(String)
    cost_price = Column(Float)
    selling_price = Column(Float)
    discount = Column(Float)
    stock = Column(Integer)
    monthly_sales = Column(Integer)
    demand_level = Column(String)
    rating = Column(Float)
    supplier_lead_time = Column(Integer)


class Reorder(Base):
    __tablename__ = "reorders"

    # new schema fields (match provided photo spec)
    reorder_id = Column(String, primary_key=True, index=True)
    product_id = Column(String, index=True)   # foreign key to products.product_id
    quantity_ordered = Column(Integer)
    reorder_point = Column(Integer)
    max_stock = Column(Integer)
    min_stock = Column(Integer)
    status = Column(String)
    ordered_at = Column(DateTime)
    expected_delivery = Column(DateTime)
    completed_at = Column(DateTime)

    # legacy columns kept for backwards compatibility with existing code
    id = Column(Integer, autoincrement=True, unique=True)
    product = Column(String, index=True)
    quantity = Column(Integer)
    eta_month = Column(Integer)
    placed_by = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class DiscountAudit(Base):
    __tablename__ = "discount_audit"

    # new schema columns
    audit_id = Column(String, primary_key=True, index=True)
    product_id = Column(String, index=True)
    user_id = Column(String, index=True)
    old_discount = Column(Float)
    new_discount = Column(Float)
    optimization_goal = Column(String)
    expected_revenue = Column(Float)
    expected_profit = Column(Float)
    confidence_score = Column(Float)
    changed_at = Column(DateTime)

    # legacy fields kept for compatibility
    id = Column(Integer, autoincrement=True, unique=True)
    timestamp = Column(DateTime)
    product = Column(String)
    user = Column(String)
    note = Column(Text)


class PriceAudit(Base):
    __tablename__ = "price_audit"

    audit_id = Column(String, primary_key=True, index=True)
    product_id = Column(String, index=True)
    user_id = Column(String, index=True)
    old_price = Column(Float)
    new_price = Column(Float)
    reason = Column(Text)
    changed_at = Column(DateTime)

    # legacy compatibility
    id = Column(Integer, autoincrement=True, unique=True)
    timestamp = Column(DateTime)
    product = Column(String)
    user = Column(String)
    note = Column(Text)


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime)
    product = Column(String)
    objective = Column(String)
    suggested_discount = Column(Float)
    expected_units = Column(Integer)
    expected_revenue = Column(Float)
    expected_profit = Column(Float)
    confidence = Column(Float)
    applied = Column(Boolean, default=False)
    applied_at = Column(DateTime, nullable=True)
    applied_by = Column(String, nullable=True)
    prev_discount = Column(Float)
    prev_price = Column(Float)
    note = Column(Text)


class SalesHistory(Base):
    __tablename__ = "sales_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_name = Column(String, index=True)
    date = Column(DateTime, index=True)
    sales = Column(Float)


class ReturnRecord(Base):
    __tablename__ = "returns"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_name = Column(String, index=True)
    date = Column(DateTime, index=True)
    quantity = Column(Integer)
    reason = Column(String)


class Supplier(Base):
    __tablename__ = "supplier"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supplier_name = Column(String)
    product_name = Column(String, index=True)
    lead_time_days = Column(Integer)


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    # link to registrations (optional)
    registration_id = Column(String, nullable=True)
# additional tables from provided schema


class Forecast(Base):
    __tablename__ = "forecasts"

    forecast_id = Column(String, primary_key=True, index=True)
    product_id = Column(String, index=True)
    model_type = Column(String)
    forecast_period = Column(DateTime)  # stored as date
    predicted_sales = Column(Integer)
    confidence_lower = Column(Float)
    confidence_upper = Column(Float)
    mae = Column(Float)
    rmse = Column(Float)
    created_at = Column(DateTime)


class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    mobileno = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class OTP(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, index=True)
    code = Column(String(10), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    channel = Column(String(20))  # 'email' or 'sms'



class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(String, primary_key=True, index=True)
    product_id = Column(String, index=True)
    alert_type = Column(String)
    severity = Column(String)
    message = Column(Text)
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String)
    created_at = Column(DateTime)
    resolved_at = Column(DateTime)


# second User class removed; consolidated above
