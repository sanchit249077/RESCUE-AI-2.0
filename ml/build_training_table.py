from pathlib import Path
import argparse
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.sample import sample_gen
from shapely.geometry import Point

warnings.filterwarnings("ignore", category=UserWarning)

ROOT = Path(__file__).resolve().parents[1]


def read_landslides(path: Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    if gdf.empty:
        raise ValueError("Landslide source is empty.")
    if gdf.crs is None:
        raise ValueError("Landslide layer has no CRS. Define its CRS before continuing.")
    gdf = gdf.to_crs(4326)

    # Normalize common coordinate fields when geometry is absent in tabular sources.
    if "geometry" not in gdf:
        raise ValueError("Landslide file must contain geometry.")
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf["event_id"] = np.arange(1, len(gdf) + 1)
    return gdf


def make_grid(bounds, cell_size_deg=0.01):
    minx, miny, maxx, maxy = bounds
    xs = np.arange(minx, maxx, cell_size_deg)
    ys = np.arange(miny, maxy, cell_size_deg)
    geometries = [Point(float(x + cell_size_deg/2), float(y + cell_size_deg/2))
                  for x in xs for y in ys
                  if x + cell_size_deg <= maxx and y + cell_size_deg <= maxy]
    return gpd.GeoDataFrame({"geometry": geometries}, crs=4326)


def raster_values(points, raster_path: Path):
    coords = [(geom.x, geom.y) for geom in points.geometry]
    with rasterio.open(raster_path) as src:
        pts = list(src.sample(coords))
        vals = [float(v[0]) if len(v) else np.nan for v in pts]
    return np.array(vals)


def derive_local_slope(dem_path: Path, points: gpd.GeoDataFrame):
    # Simple placeholder-compatible slope derivation:
    # For production, derive slope from the complete DEM tile using a geospatial
    # terrain tool (e.g. GDAL/QGIS) rather than point-by-point differences.
    with rasterio.open(dem_path) as src:
        dem = src.read(1, masked=True).astype("float64")
        transform = src.transform
        px_x = abs(transform.a)
        px_y = abs(transform.e)

        gy, gx = np.gradient(dem.filled(np.nan), px_y, px_x)
        slope_rad = np.arctan(np.sqrt(gx**2 + gy**2))
        slope_deg = np.degrees(slope_rad)

        samples = []
        for geom in points.geometry:
            try:
                row, col = src.index(geom.x, geom.y)
                samples.append(float(slope_deg[row, col]))
            except Exception:
                samples.append(np.nan)
    return np.array(samples)


def mark_positive_cells(grid, landslides, buffer_deg=0.003):
    # A positive sample means an historical landslide lies within the local buffer.
    # Buffer is in degrees only for this development prototype; production should use
    # a projected CRS and a metric buffer.
    positives = landslides.copy()
    positives["geometry"] = positives.geometry.buffer(buffer_deg)
    joined = gpd.sjoin(grid, positives[["event_id", "geometry"]], predicate="within", how="left")
    return joined.groupby(joined.index).event_id.transform(lambda s: int(s.notna().any())).astype(int).to_numpy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--landslides", required=True, help="GeoJSON/GPKG/Shapefile with landslide geometries")
    ap.add_argument("--dem", required=True, help="DEM GeoTIFF")
    ap.add_argument("--rainfall", required=False, help="CSV with lat,lon,rainfall_24h_mm,rainfall_7d_mm")
    ap.add_argument("--output", default=str(ROOT / "data" / "processed" / "training_table.csv"))
    ap.add_argument("--cell-size", type=float, default=0.02)
    args = ap.parse_args()

    landslides = read_landslides(Path(args.landslides))
    grid = make_grid(landslides.total_bounds, args.cell_size)

    grid["elevation_m"] = raster_values(grid, Path(args.dem))
    grid["slope_deg"] = derive_local_slope(Path(args.dem), grid)
    grid["historical_landslide"] = mark_positive_cells(grid, landslides)

    if args.rainfall:
        rain = pd.read_csv(args.rainfall)
        required = {"lat", "lon", "rainfall_24h_mm", "rainfall_7d_mm"}
        missing = required - set(rain.columns)
        if missing:
            raise ValueError(f"Rainfall CSV missing columns: {sorted(missing)}")
        rg = gpd.GeoDataFrame(
            rain,
            geometry=gpd.points_from_xy(rain.lon, rain.lat),
            crs=4326,
        )
        # nearest spatial join for prototype; production should use time-aware matching.
        grid = gpd.sjoin_nearest(
            grid,
            rg[["rainfall_24h_mm","rainfall_7d_mm","geometry"]],
            how="left",
            distance_col="rain_join_distance_deg"
        ).drop(columns=["index_right"], errors="ignore")
    else:
        grid["rainfall_24h_mm"] = np.nan
        grid["rainfall_7d_mm"] = np.nan

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    grid.drop(columns=["geometry"]).to_csv(out, index=False)
    grid.to_file(out.with_suffix(".gpkg"), layer="training_grid", driver="GPKG")
    print(f"Saved: {out}")
    print(f"Rows: {len(grid):,}")
    print("WARNING: This is a feature-table builder, not a scientifically validated forecast model.")
    print("Production work still requires real historical rainfall alignment, geological/land-cover layers,")
    print("projected-distance joins, event-time labels, leakage-safe spatial/temporal validation, and calibration.")


if __name__ == "__main__":
    main()
