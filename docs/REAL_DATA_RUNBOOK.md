# RescueAI real-data build runbook

## Step 0 — Keep raw data immutable
Put downloaded source files in `data/sources/` and write provenance in `metadata.json`.

## Step 1 — Landslide inventory
Use a validated inventory from GSI/ISRO. GSI's Bhusanket portal currently exposes a field-validated inventory and state susceptibility resources. ISRO's Landslide Atlas documents an approximately 80,000-landslide inventory for 1998–2022.

## Step 2 — DEM and terrain
Provide a DEM GeoTIFF covering the chosen NER pilot region. `build_training_table.py` samples elevation and derives a prototype slope raster.

## Step 3 — Rainfall alignment
Create a CSV with:
- lat
- lon
- rainfall_24h_mm
- rainfall_7d_mm

For real training, rainfall must be aligned to the landslide event date/time and location, not simply joined spatially.

## Step 4 — Build feature table

```powershell
python ml\build_training_table.py `
  --landslides data\sources\landslides.gpkg `
  --dem data\sources\dem.tif `
  --rainfall data\sources\rainfall.csv `
  --output data\processed\training_table.csv
```

## Step 5 — Train baseline

```powershell
python ml\train_real_model.py
```

## Step 6 — Scientific validation
Do NOT rely on random train/test splitting for the final model. Use:
- spatial holdout by district/grid
- temporal holdout
- class imbalance controls
- probability calibration
- false-alarm rate
- missed-event rate

## Step 7 — Expand features
Add:
- geology/lithology
- soil
- aspect/curvature
- land-cover change
- distance to drainage
- distance to roads / cut slopes
- antecedent rainfall windows
- forecast rainfall

## Step 8 — Connect the validated model to the API
Only after the model has been evaluated and calibrated.

## Known data-access caveat
Bhusanket/Bhuvan provide web-accessible information, but the exact download/API mechanism and reuse terms vary by layer. Verify the portal's current access and terms before automating downloads or redistribution.
