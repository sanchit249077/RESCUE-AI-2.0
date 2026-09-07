# First real-data milestone

Run in GitHub Codespaces:

```bash
pip install -r backend/requirements.txt
python ml/download_sikkim_inventory.py
python ml/inspect_sikkim_inventory.py
```

This downloads two documented public CSV components from Zenodo record 8169506 and verifies their published MD5 checksums.

After that, the next code milestone is:
1. validate and clean geometry/coordinates
2. create the Sikkim pilot spatial grid
3. attach terrain variables
4. attach historical landslide labels
5. obtain time-aligned rainfall
6. construct positive/negative event windows
7. train RF/XGBoost
8. evaluate spatially and temporally
