from pathlib import Path
import argparse
import geopandas as gpd
import numpy as np
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--landslides", required=True)
    ap.add_argument("--cell-m", type=float, default=1000.0)
    ap.add_argument("--output", default=str(ROOT/"data"/"processed"/"sikkim_grid.gpkg"))
    args = ap.parse_args()

    ls = gpd.read_file(args.landslides)
    if ls.empty:
        raise ValueError("Landslide layer is empty.")
    if ls.crs is None:
        raise ValueError("Input layer has no CRS.")

    # Work in UTM 45N for metric geometry in Sikkim.
    local = ls.to_crs(32645)
    minx, miny, maxx, maxy = local.total_bounds
    size = float(args.cell_m)

    cells = []
    x = minx
    while x < maxx:
        y = miny
        while y < maxy:
            cells.append(box(x, y, x+size, y+size))
            y += size
        x += size

    grid = gpd.GeoDataFrame({"cell_id": np.arange(1, len(cells)+1)}, geometry=cells, crs=32645)
    grid = grid[grid.intersects(local.unary_union)].copy()
    grid["area_km2"] = grid.geometry.area / 1e6

    # Positive historical label: at least one mapped landslide in/overlapping cell.
    joined = gpd.sjoin(grid, local[["geometry"]], predicate="intersects", how="left")
    positive_ids = set(joined.loc[joined["index_right"].notna(), "cell_id"].tolist())
    grid["historical_landslide"] = grid["cell_id"].isin(positive_ids).astype(int)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    grid.to_file(out, layer="sikkim_grid", driver="GPKG")

    print("Grid cells:", len(grid))
    print("Positive cells:", int(grid["historical_landslide"].sum()))
    print("Saved:", out)

if __name__ == "__main__":
    main()
