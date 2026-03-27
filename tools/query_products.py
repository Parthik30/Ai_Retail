"""Query the `products` table and print results.

Usage:
  python tools/query_products.py            # print all rows (may be large)
  python tools/query_products.py --limit 10 # print first 10 rows
"""
from dotenv import load_dotenv
load_dotenv()

import sys
import argparse
import pandas as pd

try:
    from backend.db import engine
except Exception as exc:
    print("Failed to import database engine from backend.db:", exc, file=sys.stderr)
    print("Make sure .env exists and contains a valid DATABASE_URL and your venv has the required packages.")
    raise


def main(limit: int | None):
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query("SELECT * FROM products", conn)
    except Exception as err:
        print("Error querying database:", err, file=sys.stderr)
        sys.exit(1)

    if df.empty:
        print("No products found in the database.")
        return

    if limit:
        print(df.head(limit).to_string(index=False))
    else:
        print(df.to_string(index=False))

    print(f"\nTotal products: {len(df)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query products table and print results")
    parser.add_argument("--limit", "-n", type=int, help="Limit number of rows to display")
    args = parser.parse_args()
    main(args.limit)
