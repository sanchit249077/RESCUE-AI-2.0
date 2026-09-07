from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "sources" / "sikkim_zenodo_8169506"

files = sorted(SRC.glob("Google_Earth_landslides_*.csv"))
if not files:
    raise SystemExit("No inventory CSVs found. Run download_sikkim_inventory.py first.")

for path in files:
    df = pd.read_csv(path)
    print("\n" + "="*80)
    print(path.name)
    print("Rows:", len(df))
    print("Columns:", list(df.columns))
    print(df.head(5).to_string(index=False))
