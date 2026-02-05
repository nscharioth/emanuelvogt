#!/usr/bin/env python3
"""
Generate list of missing work numbers.
"""
import pandas as pd
from pathlib import Path

# Load data
df = pd.read_csv("data/file_inventory.csv")

# Filter Werke
werke = df[~df['filepath'].str.contains("/Psalmen/", case=False, na=False)]
unique_werke = werke['work_number']. unique()

def get_num(w):
    try:
        return int(''.join(filter(str.isdigit, str(w))))
    except:
        return -1

numeric_ids = sorted(list(set([get_num(w) for w in unique_werke if get_num(w) > 0])))
max_id = max(numeric_ids)
actual = set(numeric_ids)
expected = set(range(1, max_id + 1))
missing = sorted(list(expected - actual))

OUTPUT_FILE = "data/MISSING_WORKS_REPORT.txt"

with open(OUTPUT_FILE, "w") as f:
    f.write(f"Emanuel Vogt Archive - Missing Works Report\n")
    f.write(f"===========================================\n")
    f.write(f"Total Works Found: {len(numeric_ids)}\n")
    f.write(f"Max Work ID: {max_id}\n")
    f.write(f"Missing IDs Count: {len(missing)}\n")
    f.write(f"Completeness: {len(numeric_ids)/max_id*100:.1f}%\n\n")
    f.write("Missing Work Numbers:\n")
    f.write("---------------------\n")
    
    # Write somewhat compactly
    for i in range(0, len(missing), 10):
        chunk = missing[i:i+10]
        f.write(", ".join(map(str, chunk)) + "\n")

print(f"Generated {OUTPUT_FILE}")
