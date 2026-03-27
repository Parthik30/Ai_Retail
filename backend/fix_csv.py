"""
Fix products.csv: normalize all rows to comma-separated.
The file currently has:
  - rows 1-28  (header + 27 entries): comma delimited
  - rows 29+   (1500 entries):        tab delimited
This script reads all rows, normalises to CSV, removes the bad test
products (T001, Po27, MAHENDRA BAHUBALI) and writes a clean file.
"""
import csv
import os
import sys

SRC = os.path.join(os.path.dirname(__file__), "data", "products.csv")

EXPECTED_COLS = [
    "product_id", "product_name", "category", "cost_price",
    "selling_price", "discount", "stock", "monthly_sales",
    "demand_level", "rating", "supplier_lead_time",
]

# IDs / names to remove (test / malformed products found in rows 1-28)
REMOVE_IDS   = {"T001", "Po27"}
REMOVE_NAMES = {"MAHENDRA BAHUBALI"}

def detect_sep(line: str) -> str:
    """Return '\\t' if the line contains more tabs than commas, else ','."""
    return "\t" if line.count("\t") > line.count(",") else ","

def main():
    rows = []
    header = None

    with open(SRC, "r", newline="", encoding="utf-8") as fh:
        for i, raw in enumerate(fh):
            line = raw.rstrip("\r\n")
            if not line:
                continue
            sep = detect_sep(line)
            parts = next(csv.reader([line], delimiter=sep))

            if i == 0:
                # Normalise header
                header = [c.strip() for c in parts]
                if header != EXPECTED_COLS:
                    print(f"[WARN] Header differs from expected: {header}")
                continue

            # Pad / trim to match column count
            while len(parts) < len(EXPECTED_COLS):
                parts.append("")
            parts = parts[: len(EXPECTED_COLS)]
            parts = [p.strip() for p in parts]

            pid   = parts[0]
            pname = parts[1]

            # Skip bad/test rows
            if pid in REMOVE_IDS or pname in REMOVE_NAMES:
                print(f"  [REMOVE] {pid} – {pname}")
                continue

            rows.append(parts)

    print(f"\nClean rows to write: {len(rows)}")

    # Write clean comma-separated file (overwrite in-place)
    with open(SRC, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(EXPECTED_COLS)
        writer.writerows(rows)

    print(f"Done – {SRC} rewritten with {len(rows)} products.")

if __name__ == "__main__":
    main()
