# RescueAI on GitHub Codespaces

### Backend
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
Open another terminal:
```bash
cd frontend
python -m http.server 5500 --bind 0.0.0.0
```

Open the forwarded **5500** port.

Port **8000** is only the API/Swagger service.

The frontend now automatically derives the Codespaces backend URL from the forwarded hostname. You no longer need to hard-code `127.0.0.1`.

### Verify
```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/risk-summary
curl http://127.0.0.1:8000/api/zones
```

In the browser dashboard, the top-right status should read:
`Backend Connected`

If it says `Backend Unreachable`, make sure port 8000 is running and forwarded.
