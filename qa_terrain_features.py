from pathlib import Path
import argparse
import pandas as pd

EXPECTED = [
    "elevation_m",
    "slope_deg",
    "aspect_deg",
    "curvature",
    "terrain_roughness",
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input)

    missing = [c for c in EXPECTED if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing terrain features: {missing}")

    print("ROWS:", len(df))
    for col in EXPECTED:
        values = pd.to_numeric(df[col], errors="coerce")
        print(
            f"{col}: valid={values.notna().sum()} "
            f"min={values.min():.4f} max={values.max():.4f} mean={values.mean():.4f}"
        )

    slope = pd.to_numeric(df["slope_deg"], errors="coerce")
    print("FLAG slope > 90:", int((slope > 90).sum()))
    print("FLAG slope < 0:", int((slope < 0).sum()))
    print("FLAG missing slope:", int(slope.isna().sum()))

if __name__ == "__main__":
    main()
