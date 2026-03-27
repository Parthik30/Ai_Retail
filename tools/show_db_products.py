"""Show products from DB using psycopg2 and SQLAlchemy engine"""
from dotenv import load_dotenv
load_dotenv()

import sys
from backend.db import get_connection, engine
import pandas as pd


def show_with_psycopg2(limit=10):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT product_id, product_name, category, stock, selling_price FROM products LIMIT %s', (limit,))
                rows = cur.fetchall()
                print('\n-- psycopg2 results --')
                for r in rows:
                    print(r)
    except Exception as e:
        print('psycopg2 query failed:', e, file=sys.stderr)


def show_with_sqlalchemy(limit=10):
    try:
        df = pd.read_sql_query('SELECT product_id, product_name, category, stock, selling_price FROM products LIMIT %s' % limit, con=engine)
        print('\n-- sqlalchemy results --')
        print(df)
    except Exception as e:
        print('sqlalchemy query failed:', e, file=sys.stderr)


if __name__ == '__main__':
    show_with_psycopg2(10)
    show_with_sqlalchemy(10)
