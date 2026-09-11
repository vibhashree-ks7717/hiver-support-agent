import pandas as pd
from collections import Counter

FILE = "twcs/twcs.csv"

brand_counts = Counter()
total_rows = 0
customer_rows = 0
brand_rows = 0

print("Reading dataset in chunks...")
print("This may take a little while.\n")

for chunk in pd.read_csv(
    FILE,
    usecols=["author_id", "inbound"],
    chunksize=100000
):
    total_rows += len(chunk)

    customer = chunk[chunk["inbound"] == True]
    brand = chunk[chunk["inbound"] == False]

    customer_rows += len(customer)
    brand_rows += len(brand)

    brand_counts.update(brand["author_id"].dropna().astype(str))

print("\n========== DATASET SUMMARY ==========")
print("Total tweets:", total_rows)
print("Customer tweets:", customer_rows)
print("Brand/support tweets:", brand_rows)

print("\n========== TOP BRAND ACCOUNTS ==========")

for brand, count in brand_counts.most_common(30):
    print(f"{brand:30} {count:,}")