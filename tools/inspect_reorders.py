from sqlalchemy import text
from backend.db import engine

with engine.connect() as conn:
    cols = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='reorders' ORDER BY ordinal_position")).fetchall()
    print('reorders columns:')
    for c in cols:
        print(c)