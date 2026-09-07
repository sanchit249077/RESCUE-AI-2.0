from pathlib import Path
import argparse
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

LAT_CANDIDATES = ["lat", "latitude", "Latitude", "LATITUDE", "y"]
LON_CANDIDATES = ["lon", "longitude", "Longitude", "LONGITUDE", "x"]
YEAR_CANDIDATES = ["year", "Year", "YEAR"]

def pick(cols, candidates):
    for c in candidates:
        if c in cols:
            return c
    return None

def main():
    ap = argparse.ArgumentParser(description="Normalize the downloaded Sikkim landslide CSV inventory.")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", default=str(ROOT/"data"/"processed"/"sikkim_landslides_normalized.csv"))
    args = ap.parse_args()

    df = pd.read_csv(args.input)

    lat = pick(df.columns, LAT_CANDIDATES)
    lon = pick(df.columns, LON_CANDIDATES)
    year = pick(df.columns, YEAR_CANDIDATES)

    if not lat or not lon:
        raise ValueError(
            "Could not identify latitude/longitude columns. "
            f"Columns present: {list(df.columns)}"
        )

    out = pd.DataFrame()
    out["latitude"] = pd.to_numeric(df[lat], errors="coerce")
    out["longitude"] = pd.to_numeric(df[lon], errors="coerce")
    out["year"] = pd.to_numeric(df[year], errors="coerce") if year else np.nan

    # Keep all original attributes for auditability.
    out = pd.concat([out, df.add_prefix("src_")], axis=1)

    before = len(out)
    out = out.dropna(subset=["latitude","longitude"])
    out = out[
        out["latitude"].between(-90,90) &
        out["longitude"].between(-180,180)
    ]

    out["record_id"] = np.arange(1, len(out)+1)
    out["region"] = "Sikkim"

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)

    print(f"Input rows: {before}")
    print(f"Valid coordinate rows: {len(out)}")
    print(f"Removed rows: {before-len(out)}")
    print(f"Saved: {args.output}")

if __name__ == "__main__":
    main()
