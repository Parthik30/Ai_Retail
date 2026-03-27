import sys
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from backend.services import discount_service as ds
from backend.db import SessionLocal
from backend.models import Product, AIRecommendation

# pick a product
session = SessionLocal()
prod = session.query(Product).filter(Product.product_id == 'P001').one()
session.close()

print('Product sample:', prod.product_name, prod.selling_price, prod.discount)

# create a recommendation
product_info = {
    'selling_price': prod.selling_price,
    'cost_price': prod.cost_price,
    'monthly_sales': prod.monthly_sales,
    'stock': prod.stock,
    'demand_level': prod.demand_level
}
rec = ds.ai_recommend_discount(product_info)
print('AI recommendation:', rec)

rid = ds.log_ai_recommendation(prod.product_name, 'profit', rec, int(prod.discount or 0), float(prod.selling_price or 0.0), note='simulated')
print('Saved rec id:', rid)

# verify DB entry
session = SessionLocal()
ai = session.query(AIRecommendation).filter(AIRecommendation.id == rid).one_or_none()
if ai:
    print('DB saved rec:', ai.id, ai.product, ai.suggested_discount, ai.applied)
else:
    print('Rec not found in DB; likely CSV fallback was used')
session.close()

# mark applied
ok = ds.mark_recommendation_applied(rid, applied_by='simulator')
print('Marked applied:', ok)

# re-query to verify
session = SessionLocal()
ai = session.query(AIRecommendation).filter(AIRecommendation.id == rid).one_or_none()
print('After apply - applied:', ai.applied, 'applied_at:', ai.applied_at, 'applied_by:', ai.applied_by)
session.close()

# undo
undone = ds.undo_recommendation(rid, user='simulator')
print('Undo result:', undone)

# re-query again
session = SessionLocal()
ai = session.query(AIRecommendation).filter(AIRecommendation.id == rid).one_or_none()
print('After undo - applied:', ai.applied, 'applied_at:', ai.applied_at, 'applied_by:', ai.applied_by)
session.close()
