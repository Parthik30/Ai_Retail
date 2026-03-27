import csv
from data import products

def generate_inventory_report():
    with open("inventory_report.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Product", "Price", "Discount", "Stock"])
        for k, v in products.items():
            writer.writerow([k, v["price"], v["discount"], v["stock"]])
    return "inventory_report.csv generated"
