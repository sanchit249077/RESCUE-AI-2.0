from pathlib import Path
import argparse
import numpy as np
import geopandas as gpd
import rasterio
from scipy.ndimage import gaussian_filter

ROOT = Path(__file__).resolve().parents[1]

def derive_features(dem_path: Path):
    with rasterio.open(dem_path) as src:
        dem = src.read(1, masked=True).astype("float64")
        transform = src.transform
        crs = src.crs
        if crs is None:
            raise ValueError("DEM must have a CRS.")
        xres = abs(transform.a)
        yres = abs(transform.e)

        arr = dem.filled(np.nan)
        fill_value = float(np.nanmedian(arr))
        smooth = gaussian_filter(np.nan_to_num(arr, nan=fill_value), sigma=1)

        dz_dy, dz_dx = np.gradient(smooth, yres, xres)
        slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
        slope_deg = np.degrees(slope_rad)

        aspect = (np.degrees(np.arctan2(-dz_dx, dz_dy)) + 360) % 360

        d2z_dx2 = np.gradient(dz_dx, xres, axis=1)
        d2z_dy2 = np.gradient(dz_dy, yres, axis=0)
        curvature = d2z_dx2 + d2z_dy2
        roughness = np.sqrt(dz_dx**2 + dz_dy**2)

        return crs, {
            "elevation_m": smooth,
            "slope_deg": slope_deg,
            "aspect_deg": aspect,
            "curvature": curvature,
            "terrain_roughness": roughness,
        }

def main():
    parser = argparse.ArgumentParser(
        description="Create DEM-derived terrain features for RescueAI."
    )
    parser.add_argument("--grid", required=True)
    parser.add_argument("--dem", required=True)
    parser.add_argument(
        "--output",
        default=str(ROOT / "data" / "processed" / "sikkim_terrain_features.gpkg"),
    )
    args = parser.parse_args()

    grid = gpd.read_file(args.grid)
    if grid.empty:
        raise ValueError("Grid is empty.")
    if grid.crs is None:
        raise ValueError("Grid has no CRS.")

    dem_crs, arrays = derive_features(Path(args.dem))

    points = grid.copy()
    points.geometry = points.geometry.centroid
    points = points.to_crs(dem_crs)

    with rasterio.open(args.dem) as src:
        for name, arr in arrays.items():
            values = []
            for geom in points.geometry:
                try:
                    row, col = src.index(geom.x, geom.y)
                    value = arr[row, col]
                    values.append(float(value) if np.isfinite(value) else np.nan)
                except (IndexError, ValueError):
                    values.append(np.nan)
            grid[name] = values

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    grid.to_file(output, layer="terrain_features", driver="GPKG")
    grid.drop(columns="geometry").to_csv(output.with_suffix(".csv"), index=False)

    print("Terrain features created successfully.")
    print("Rows:", len(grid))
    print("Features:", ", ".join(arrays.keys()))
    print("GeoPackage:", output)
    print("CSV:", output.with_suffix(".csv"))

if __name__ == "__main__":
    main()
