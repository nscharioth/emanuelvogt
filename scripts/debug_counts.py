import pandas as pd
from pathlib import Path

csv_path = "data/file_inventory.csv"
df = pd.read_csv(csv_path)

print(f"Total rows in CSV: {len(df)}")

# Helper function
def get_num(w):
    try:
        return int(''.join(filter(str.isdigit, str(w))))
    except:
        return -1

# Analyze 'work_number' uniqueness
unique_works = df['work_number'].unique()
print(f"Unique work_numbers found: {len(unique_works)}")

# Check for Psalmen using filepath
psalmen = df[df['filepath'].str.contains("/Psalmen/", case=False, na=False)]
print(f"Rows in 'Psalmen' filepaths: {len(psalmen)}")
unique_psalmen = psalmen['work_number'].unique()
print(f"Unique Psalmen work_numbers: {len(unique_psalmen)}")

# Check for Werke (everything else)
werke = df[~df['filepath'].str.contains("/Psalmen/", case=False, na=False)]
print(f"Rows in 'Werke' filepaths: {len(werke)}")
unique_werke = werke['work_number'].unique()
print(f"Unique Werke work_numbers: {len(unique_werke)}")

# Identify gaps in Werke sequence (1 to 2036)
numeric_ids = sorted(list(set([get_num(w) for w in unique_werke if get_num(w) > 0])))

if not numeric_ids:
    print("No numeric IDs found!")
else:
    max_id = max(numeric_ids)
    expected_range = set(range(1, max_id + 1))
    actual_range = set(numeric_ids)
    gaps = sorted(list(expected_range - actual_range))

    print(f"\nMax Werke ID: {max_id}")
    print(f"Missing numeric IDs (Gaps): {len(gaps)}")
    if len(gaps) < 50:
        print(f"Gaps: {gaps}")
    else:
        print(f"First 20 gaps: {gaps[:20]}")
        print(f"Last 20 gaps: {gaps[-20:]}")

# Look for 'a', 'b' suffixes
sample_suffixes = [w for w in unique_werke if isinstance(w, str) and w[-1].isalpha() and w[:-1].isdigit()]
print(f"\nSample works with suffixes: {sample_suffixes[:10]}")
