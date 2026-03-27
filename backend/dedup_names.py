import pandas as pd
import os

backend_dir = r"c:\Users\HP\Desktop\New Folder\backend"
csv_path = os.path.join(backend_dir, "data", "products.csv")

df = pd.read_csv(csv_path)

# Find duplicate names
name_counts = df["product_name"].value_counts()
duplicates = name_counts[name_counts > 1].index

# For duplicate names, append the product_id to make them unique
def make_unique(row):
    if row["product_name"] in duplicates:
        return f"{row['product_name']} ({row['product_id']})"
    return row["product_name"]

df["product_name"] = df.apply(make_unique, axis=1)

# Save back to CSV
df.to_csv(csv_path, index=False)
print("Product names disambiguated successfully!")
