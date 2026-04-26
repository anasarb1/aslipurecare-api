"""
AslipureCare API - Test Suite
Run with: pytest tests/ -v
"""

import pytest
from app import app, db, Product


@pytest.fixture
def client():
    """Configure app for testing and provide a test client."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        # Seed a known product for GET /products/<id> tests
        if Product.query.count() == 0:
            db.session.add(Product(
                id="test-1",
                name="Vitamin C Serum",
                price=29.99,
                description="Brightening serum"
            ))
            db.session.commit()

    with app.test_client() as client:
        yield client


def get_token(client):
    """Helper: get a valid JWT token."""
    r = client.post("/auth/token", json={"username": "admin", "password": "aslipure2024"})
    return r.get_json()["access_token"]


# ---------------------------------------------------------------------------
# 1. GET / returns 200
# ---------------------------------------------------------------------------
def test_index_returns_200(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "healthy"


# ---------------------------------------------------------------------------
# 2. GET /health returns version 2.0.0
# ---------------------------------------------------------------------------
def test_health_returns_version(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "healthy"
    assert data["version"] == "2.0.0"
    assert data["service"] == "aslipurecare-api"


# ---------------------------------------------------------------------------
# 3. GET /products returns a list
# ---------------------------------------------------------------------------
def test_get_products_returns_list(client):
    r = client.get("/products")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1


# ---------------------------------------------------------------------------
# 4. POST /auth/token with valid credentials returns a token
# ---------------------------------------------------------------------------
def test_auth_token_valid_credentials(client):
    r = client.post("/auth/token", json={"username": "admin", "password": "aslipure2024"})
    assert r.status_code == 200
    data = r.get_json()
    assert "access_token" in data
    assert len(data["access_token"]) > 20


# ---------------------------------------------------------------------------
# 5. POST /auth/token with wrong password returns 401
# ---------------------------------------------------------------------------
def test_auth_token_wrong_password(client):
    r = client.post("/auth/token", json={"username": "admin", "password": "wrongpassword"})
    assert r.status_code == 401
    assert "error" in r.get_json()


# ---------------------------------------------------------------------------
# 6. POST /products without token returns 401
# ---------------------------------------------------------------------------
def test_create_product_without_token_returns_401(client):
    r = client.post("/products", json={
        "name": "Test Product",
        "price": 9.99,
        "description": "A test product"
    })
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# 7. GET /metrics returns uptime and product_count
# ---------------------------------------------------------------------------
def test_metrics_returns_uptime_and_count(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    data = r.get_json()
    assert "uptime_seconds" in data
    assert "product_count" in data
    assert "total_requests" in data
    assert isinstance(data["uptime_seconds"], (int, float))
    assert data["product_count"] >= 1


# ---------------------------------------------------------------------------
# 8. GET /products/<id> with invalid id returns 404
# ---------------------------------------------------------------------------
def test_get_product_invalid_id_returns_404(client):
    r = client.get("/products/does-not-exist-999")
    assert r.status_code == 404
    assert r.get_json()["error"] == "Product not found"


# ---------------------------------------------------------------------------
# Bonus: POST /products with valid token creates product
# ---------------------------------------------------------------------------
def test_create_product_with_valid_token(client):
    token = get_token(client)
    r = client.post(
        "/products",
        json={"name": "Night Serum", "price": 34.99, "description": "Retinol complex"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 201
    data = r.get_json()
    assert data["name"] == "Night Serum"
    assert data["price"] == 34.99
    assert "id" in data


# ---------------------------------------------------------------------------
# Bonus: POST /products with missing fields returns 400 with details
# ---------------------------------------------------------------------------
def test_create_product_missing_fields(client):
    token = get_token(client)
    r = client.post(
        "/products",
        json={"name": "Incomplete"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 400
    data = r.get_json()
    assert data["error"] == "Validation failed"
    assert "details" in data
