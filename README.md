# AslipureCare API

A lightweight Python Flask microservice that exposes skincare product data via a REST API.

---

## Endpoints

| Method | Path        | Description                        |
|--------|-------------|------------------------------------|
| GET    | `/`         | Liveness check                     |
| GET    | `/health`   | Detailed health status             |
| GET    | `/products` | List all skincare products         |
| POST   | `/products` | Create a new product               |

### POST `/products` — request body

```json
{
  "name":        "Product name",
  "price":       19.99,
  "description": "Short description"
}
```

---

## Running locally

### Option 1 — Python directly

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the development server
python app.py
```

The API is now available at `http://localhost:5000`.

### Option 2 — Docker Compose (recommended)

```bash
# Build image and start the container
docker compose up --build

# Run in the background
docker compose up -d --build

# Stop
docker compose down
```

### Option 3 — Docker directly

```bash
docker build -t aslipurecare-api .
docker run -p 5000:5000 aslipurecare-api
```

---

## Quick smoke test

```bash
# Liveness
curl http://localhost:5000/

# Health
curl http://localhost:5000/health

# List products
curl http://localhost:5000/products

# Create a product
curl -X POST http://localhost:5000/products \
     -H "Content-Type: application/json" \
     -d '{"name":"Retinol Night Cream","price":39.99,"description":"0.3% retinol with ceramides"}'
```

---

## CI/CD Pipeline

The GitHub Actions workflow lives in `.github/workflows/deploy.yml` and runs on every push to `main`.

```
push to main
     │
     ▼
┌─────────────────────────────────────┐
│  Job 1 — build                      │
│  • Checkout code                    │
│  • Set up Python 3.11               │
│  • pip install -r requirements.txt  │
│  • Start Flask app (background)     │
│  • curl / and /health smoke tests   │
│  • Assert /products returns 200     │
└────────────────┬────────────────────┘
                 │ on success
                 ▼
┌─────────────────────────────────────┐
│  Job 2 — docker                     │
│  • Checkout code                    │
│  • Set up Docker Buildx             │
│  • Build Docker image               │
│  • Verify image exists              │
│  (optional: push to Docker Hub)     │
└─────────────────────────────────────┘
```

### Pushing to Docker Hub

1. Add `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` as repository secrets in GitHub.
2. Uncomment the **Log in** and **Push image** steps inside `deploy.yml`.

---

## Project structure

```
aslipurecare-api/
├── app.py                        # Flask application
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Local orchestration
├── .github/
│   └── workflows/
│       └── deploy.yml            # CI/CD pipeline
└── README.md
```

---

## Logging

Every request is logged to stdout in structured format:

```
2026-04-14T18:00:00+0000 [INFO] aslipurecare - REQUEST  | ... | GET /health | ip=172.17.0.1
2026-04-14T18:00:00+0000 [INFO] aslipurecare - RESPONSE | ... | GET /health | status=200
```

When running via Docker / gunicorn, gunicorn's own access log is also streamed to stdout.
