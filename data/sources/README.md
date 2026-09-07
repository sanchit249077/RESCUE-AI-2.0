# RescueAI real-data ingestion

Place source files here after downloading them from their authoritative source.

Recommended source roles:
- `landslides.*` → GSI / ISRO / validated inventory
- `ner_boundary.*` → administrative boundary
- `dem.tif` → Digital Elevation Model
- `rainfall.csv` → dated rainfall observations or gridded extraction
- `roads.*` → road network
- `settlements.*` → villages / population locations

Never overwrite raw source files. Keep the original file and metadata.
Use `metadata.json` to record URL, access date, license/terms, date range and transformations.
