# AslipureCare API

A Python Flask microservice that exposes skincare product data via a REST API. Version 2.0.0 adds SQLite persistence, JWT authentication, input validation, and an operational metrics endpoint.

---

## Endpoints

| Method | Path                  | Auth required | Description                        |
|--------|-----------------------|---------------|------------------------------------|
| GET    | `/`                   | No            | Liveness check                     |
| GET    | `/health`             | No            | Detailed health status             |
| GET    | `/metrics`            | No            | Uptime, request counts, DB stats   |
| POST   | `/auth/token`         | No            | Get a JWT access token             |
| GET    | `/products`           | No            | List all skincare products         |
| GET    | `/products/<id>`      | No            | Get a single product by ID         |
| POST   | `/products`           | Yes (JWT)     | Create a new product               |

---

## Authentication

`POST /products` requires a JWT token in the `Authorization` header.

### 1. Get a token

```bash
curl -X POST http://localhost:5000/auth/token \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"aslipure2024"}'
```

Response:
```json
{ "access_token": "<jwt>" }
```

### 2. Use the token

```bash
curl -X POST http://localhost:5000/products \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <jwt>" \
     -d '{"name":"Retinol Night Cream","price":39.99,"description":"0.3% retinol with ceramides"}'
```

---

## Database

Version 2.0.0 uses **SQLite** via Flask-SQLAlchemy. The database file (`products.db`) is created automatically on first start and seeded with three products.

- Local runs: `products.db` lives in the project directory
- Docker: mounted as a volume (see `docker-compose.yml`)
- Render: ephemeral on the free tier — data reseeds on each restart

To use a different database, set the `DATABASE_URL` environment variable (e.g. a PostgreSQL connection string).

---

## Environment Variables

| Variable        | Required | Default                            | Description                        |
|-----------------|----------|------------------------------------|------------------------------------|
| `JWT_SECRET_KEY`| Yes      | `dev-secret-key-change-in-prod!!`  | Secret used to sign JWT tokens     |
| `ADMIN_USER`    | No       | `admin`                            | Username for token endpoint        |
| `ADMIN_PASS`    | No       | `aslipure2024`                     | Password for token endpoint        |
| `DATABASE_URL`  | No       | `sqlite:///products.db`            | SQLAlchemy database URI            |
| `PORT`          | No       | `5000`                             | Port (set automatically on Render) |

Copy `.env.example` to `.env` and fill in production values before deploying.

---

## Running locally

### Option 1 — Python directly

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Option 2 — Docker Compose (recommended)

```bash
docker compose up --build
docker compose up -d --build   # background
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

# Metrics
curl http://localhost:5000/metrics

# List products
curl http://localhost:5000/products

# Single product
curl http://localhost:5000/products/1

# Get a token then create a product
TOKEN=$(curl -s -X POST http://localhost:5000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"aslipure2024"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -X POST http://localhost:5000/products \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"name":"Retinol Night Cream","price":39.99,"description":"0.3% retinol with ceramides"}'
```

---

## Running tests

```bash
pip install pytest
pytest tests/ -v
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
└─────────────────────────────────────┘
```

---

## Project structure

```
aslipurecare-api/
├── app.py                        # Flask application
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Local orchestration
├── render.yaml                   # Render.com deployment config
├── .env.example                  # Environment variable template
├── tests/
│   └── test_app.py               # Pytest test suite
├── docs/                         # Static frontend (GitHub Pages)
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
