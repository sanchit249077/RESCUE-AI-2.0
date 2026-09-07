# RescueAI — Stage 4: Real Sikkim dataset

## Goal
Move from sample/demo risk zones to a real Sikkim landslide inventory and a repeatable geospatial feature pipeline.

## Step A — Acquire
Run:
```bash
python ml/download_sikkim_inventory.py
```

The downloader targets the two public CSV components documented on Zenodo record 8169506.

## Step B — Inspect
```bash
python ml/inspect_sikkim_inventory.py
```

## Step C — Normalize
First use the polygon inventory when geographic polygons are available:
```bash
python ml/normalize_sikkim_inventory.py \
  --input data/sources/sikkim_zenodo_8169506/Google_Earth_landslides_polygon_21Dec2021.csv
```

If the published CSV has no discoverable latitude/longitude columns, use the corresponding shapefile instead and add a geometry-based normalizer. Do not invent coordinates.

## Step D — Build spatial grid
The grid builder works in UTM 45N so spatial operations use metres:
```bash
python ml/build_sikkim_grid.py \
  --landslides data/sources/sikkim_zenodo_8169506/Google_Earth_landslides_polygon_21Dec2021.shp
```

## What this produces
A Sikkim grid with:
- cell_id
- area_km2
- historical_landslide (0/1)

## Next after this
1. Add DEM-derived elevation/slope/aspect/curvature.
2. Add geology and land-cover.
3. Add time-aligned rainfall before each historical event.
4. Construct non-event samples.
5. Train RF/XGBoost.
6. Perform spatial + temporal validation.
7. Connect the calibrated model to the dashboard.

## Scientific guardrails
- The mapped inventory is not a complete observation of every landslide.
- A historical presence label is not the same as probability of a future landslide.
- Do not use random train/test splitting as the only final evaluation.
- Do not claim operational warnings until the trigger data and validation are sound.
