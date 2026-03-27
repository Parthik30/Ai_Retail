import sys, os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
from backend.db import SessionLocal
from backend.models import AIRecommendation
s = SessionLocal()
ai = s.query(AIRecommendation).filter(AIRecommendation.id=='5b917fc3-53a7-4da4-ada7-9379e0e8bb49').one_or_none()
print('Re-queried:', ai and (ai.id, ai.applied, ai.applied_at, ai.applied_by))
s.close()
