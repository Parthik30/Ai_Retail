"""Robust DB connectivity check: verifies DATABASE_URL, tries to import engine with fallback,
and runs `SELECT 1` with retries and helpful diagnostics.

Usage:
  python -m tools.check_db        # quick check
  python -m tools.check_db -r 5   # retry up to 5 times
  python -m tools.check_db -r 5 -w 2  # wait 2 seconds between attempts
"""
from dotenv import load_dotenv
load_dotenv()

import sys
import os
import time
import argparse
from sqlalchemy import text
from sqlalchemy.exc import OperationalError


def mask_url(url: str) -> str:
    if not url:
        return "<empty>"
    # mask password if present
    try:
        prefix, rest = url.split("//", 1)
        creds, host = rest.split("@", 1)
        if ":" in creds:
            user, _pass = creds.split(":", 1)
            return f"{prefix}//{user}:***@{host}"
    except Exception:
        pass
    return url


def import_engine_fallback():
    """Try to import engine from backend.db. If it fails, add project root to sys.path and retry."""
    try:
        from backend.db import engine  # type: ignore
        return engine
    except Exception as exc:
        # Attempt to add project root to sys.path
        project_root = os.getcwd()
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        try:
            from backend.db import engine  # type: ignore
            return engine
        except Exception as exc2:
            print("Failed to import engine from backend.db:", exc2, file=sys.stderr)
            print("Ensure you run this as a module from project root: `python -m tools.check_db` and that `backend/__init__.py` exists.")
            sys.exit(2)


def main(retries: int, wait: float, verbose: bool):
    database_url = os.getenv("DATABASE_URL")
    print("DATABASE_URL:", mask_url(database_url))
    engine = import_engine_fallback()

    attempt = 0
    while True:
        attempt += 1
        try:
            if verbose:
                print(f"Attempt {attempt}: connecting to DB...")
            with engine.connect() as conn:
                res = conn.execute(text("SELECT 1"))
                val = res.scalar()
                if val == 1:
                    print("DB connection successful: SELECT 1 returned 1")
                    sys.exit(0)
                else:
                    print("DB connected but unexpected SELECT 1 result:", val)
                    sys.exit(3)
        except OperationalError as oe:
            msg = str(oe)
            print(f"OperationalError on attempt {attempt}: {msg}", file=sys.stderr)
            # Helpful hints
            if "password authentication failed" in msg.lower():
                print("Hint: authentication failed — check DATABASE_URL credentials and Postgres user/password.", file=sys.stderr)
            if "could not connect to server" in msg.lower() or "connection refused" in msg.lower():
                print("Hint: DB is not reachable — ensure Postgres is running and host/port are correct (docker/psql).", file=sys.stderr)
        except Exception as e:
            print(f"Unexpected error on attempt {attempt}: {e}", file=sys.stderr)

        if attempt >= retries:
            print(f"DB check failed after {attempt} attempts.", file=sys.stderr)
            sys.exit(1)

        if verbose:
            print(f"Waiting {wait} seconds before retry...")
        time.sleep(wait)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DB connectivity check with retries and diagnostics")
    parser.add_argument("-r", "--retries", type=int, default=1, help="Number of attempts (default: 1)")
    parser.add_argument("-w", "--wait", type=float, default=1.0, help="Seconds to wait between attempts")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()
    main(args.retries, args.wait, args.verbose)
