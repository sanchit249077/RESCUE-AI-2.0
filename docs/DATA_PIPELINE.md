# RescueAI Data Pipeline

## Target feature table

One row = one spatial cell / road segment / administrative micro-area at a time t.

Columns:
- latitude, longitude
- rainfall_1h, rainfall_6h, rainfall_24h, rainfall_72h, rainfall_7d
- slope_deg
- elevation_m
- geology_class / geology_risk
- landcover_class / change_score
- distance_to_drainage_m
- distance_to_road_m
- historical_landslide_count
- target: landslide in future window (binary) or calibrated probability

## Label design
Use historical landslide dates/locations. For each event, create positive samples in an appropriate forecast window. Construct matched non-event samples while avoiding spatial and temporal leakage.

## Validation
Use:
- spatial holdout by district/grid
- temporal holdout
- class-balanced metrics
- calibration curve / Brier score
- false alarm rate
- missed-event rate

## Operational rule
A warning policy should be separate from the ML model:
model probability + uncertainty + exposure + policy thresholds -> alert level.
