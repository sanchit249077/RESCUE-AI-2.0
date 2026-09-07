from pathlib import Path
import hashlib
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "sources" / "sikkim_zenodo_8169506"
OUT.mkdir(parents=True, exist_ok=True)

FILES = [
    ("Google_Earth_landslides_point_21Dec2021.csv",
     "https://zenodo.org/records/8169506/files/Google_Earth_landslides_point_21Dec2021.csv?download=1",
     "a30ecdd5866ec9a257113d2ee6d59333"),
    ("Google_Earth_landslides_polygon_21Dec2021.csv",
     "https://zenodo.org/records/8169506/files/Google_Earth_landslides_polygon_21Dec2021.csv?download=1",
     "8127c503662331ebe2b1ac1578ebc170"),
]

def checksum(path):
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

for name, url, expected in FILES:
    path = OUT / name
    print(f"Downloading {name} ...")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with path.open("wb") as f:
            for chunk in r.iter_content(1024*1024):
                if chunk:
                    f.write(chunk)
    got = checksum(path)
    print(f"MD5 {got}")
    if expected and got != expected:
        raise RuntimeError(f"Checksum mismatch for {name}: expected {expected}, got {got}")

print("Sikkim inventory download complete.")
