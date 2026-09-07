import json, urllib.request

BASE = "http://127.0.0.1:8000"

def get(path):
    with urllib.request.urlopen(BASE + path, timeout=5) as r:
        assert r.status == 200
        return json.loads(r.read())

health = get("/api/health")
assert health["status"] == "ok"

summary = get("/api/risk-summary")
assert summary["total_zones"] > 0

zones = get("/api/zones?min_score=80")
assert isinstance(zones, list)

sources = get("/api/sources")
assert len(sources["sources"]) >= 3

print("Smoke tests passed.")
