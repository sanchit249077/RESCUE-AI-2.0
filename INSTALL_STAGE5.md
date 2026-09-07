# Stage 5 patch

Copy the two Python files into the repository `ml/` directory.

Then run:

```bash
python ml/build_terrain_features.py --help
```

The command should display the script help instead of "file not found".

Required input files:
- `data/processed/sikkim_grid.gpkg`
- `data/sources/sikkim_dem.tif`

Only after both exist run the feature-generation command.
