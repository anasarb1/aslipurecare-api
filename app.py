"""
AslipureCare API - Main Flask Application
A microservice for managing skincare products.
"""

import logging
import os
import time
import uuid
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
logger = logging.getLogger("aslipurecare")

# ---------------------------------------------------------------------------
# App + DB + JWT
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///products.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-secret-key-change-in-prod!!")

db  = SQLAlchemy(app)
jwt = JWTManager(app)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
class Product(db.Model):
    __tablename__ = "products"

    id          = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name        = db.Column(db.String(200), nullable=False)
    price       = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id":          self.id,
            "name":        self.name,
            "price":       self.price,
            "description": self.description,
            "created_at":  self.created_at.isoformat() if self.created_at else None,
        }

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------
SEED_PRODUCTS = [
    {"id": "1", "name": "Hydrating Vitamin C Serum",     "price": 29.99, "description": "Brightening serum with 15% vitamin C, hyaluronic acid, and niacinamide."},
    {"id": "2", "name": "Gentle Foaming Cleanser",       "price": 14.99, "description": "Sulfate-free daily cleanser suitable for all skin types, pH-balanced formula."},
    {"id": "3", "name": "SPF 50 Lightweight Moisturiser","price": 34.99, "description": "Broad-spectrum UVA/UVB protection in a non-greasy, fast-absorbing moisturiser."},
]

def seed_db():
    if Product.query.count() == 0:
        for p in SEED_PRODUCTS:
            db.session.add(Product(**p))
        db.session.commit()
        logger.info("Database seeded with %d products", len(SEED_PRODUCTS))

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------
MAX_NAME_LEN = 200
MAX_DESC_LEN = 2000
MAX_PRICE    = 10_000

def validate_product_payload(data):
    """Validate product creation payload. Returns list of error strings."""
    errors = []
    if not data:
        return ["Request body must be valid JSON"]
    for field in ("name", "price", "description"):
        if field not in data:
            errors.append(f"'{field}' is required")
    if errors:
        return errors
    name = data.get("name", "")
    if not isinstance(name, str) or not name.strip():
        errors.append("'name' must be a non-empty string")
    elif len(name.strip()) > MAX_NAME_LEN:
        errors.append(f"'name' must be {MAX_NAME_LEN} characters or fewer")
    price = data.get("price")
    if not isinstance(price, (int, float)) or isinstance(price, bool):
        errors.append("'price' must be a number")
    elif price <= 0:
        errors.append("'price' must be greater than zero")
    elif price > MAX_PRICE:
        errors.append(f"'price' must be {MAX_PRICE} or less")
    desc = data.get("description", "")
    if not isinstance(desc, str) or not desc.strip():
        errors.append("'description' must be a non-empty string")
    elif len(desc.strip()) > MAX_DESC_LEN:
        errors.append(f"'description' must be {MAX_DESC_LEN} characters or fewer")
    return errors

# ---------------------------------------------------------------------------
# Request logging decorator
# ---------------------------------------------------------------------------
def log_request(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        timestamp = datetime.now(timezone.utc).isoformat()
        logger.info("REQUEST  | %s | %s %s | ip=%s", timestamp, request.method, request.path, request.remote_addr)
        response = func(*args, **kwargs)
        status = response[1] if isinstance(response, tuple) else 200
        logger.info("RESPONSE | %s | %s %s | status=%s", timestamp, request.method, request.path, status)
        return response
    return wrapper

# ---------------------------------------------------------------------------
# JWT error handlers (JSON responses instead of Flask default HTML)
# ---------------------------------------------------------------------------
@jwt.unauthorized_loader
def missing_token_callback(reason):
    return jsonify({"error": "Authorization token required", "detail": reason}), 401

@jwt.invalid_token_loader
def invalid_token_callback(reason):
    return jsonify({"error": "Invalid token", "detail": reason}), 422

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "Token has expired"}), 401

# ---------------------------------------------------------------------------
# Auth route
# ---------------------------------------------------------------------------
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "aslipure2024")

@app.route("/auth/token", methods=["POST"])
@log_request
def get_token():
    """Issue a JWT. Body: { "username": "admin", "password": "aslipure2024" }"""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400
    username = data.get("username") if isinstance(data.get("username"), str) else ""
    password = data.get("password") if isinstance(data.get("password"), str) else ""
    if not username or not password:
        return jsonify({"error": "'username' and 'password' are required"}), 400
    if username != ADMIN_USER or password != ADMIN_PASS:
        return jsonify({"error": "Invalid credentials"}), 401
    token = create_access_token(identity=username)
    logger.info("Token issued for user=%s", username)
    return jsonify({"access_token": token}), 200

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
@log_request
def index():
    return jsonify({"message": "AslipureCare API is running", "status": "healthy"})


@app.route("/health", methods=["GET"])
@log_request
def health():
    return jsonify({"status": "healthy", "service": "aslipurecare-api", "version": "2.0.0"})


@app.route("/products", methods=["GET"])
@log_request
def get_products():
    """Return all products. Accepts optional ?limit=N query param."""
    try:
        limit = request.args.get("limit")
        if limit is not None:
            if not limit.isdigit() or int(limit) < 1:
                return jsonify({"error": "'limit' must be a positive integer"}), 400
            products = Product.query.limit(int(limit)).all()
        else:
            products = Product.query.all()
        return jsonify([p.to_dict() for p in products])
    except Exception as exc:
        logger.exception("Error fetching products: %s", exc)
        return jsonify({"error": "Could not retrieve products"}), 500


@app.route("/products/<product_id>", methods=["GET"])
@log_request
def get_product(product_id):
    """Return a single product by ID."""
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product.to_dict())


@app.route("/products", methods=["POST"])
@jwt_required()
@log_request
def create_product():
    """Create a product. Requires Authorization: Bearer <token>."""
    data = request.get_json(silent=True)
    errors = validate_product_payload(data)
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400
    product = Product(
        name        = str(data["name"]).strip(),
        price       = round(float(data["price"]), 2),
        description = str(data["description"]).strip(),
    )
    try:
        db.session.add(product)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("DB error creating product: %s", exc)
        return jsonify({"error": "Could not save product"}), 500
    logger.info("Created product id=%s name=%s by=%s", product.id, product.name, get_jwt_identity())
    return jsonify(product.to_dict()), 201

# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request"}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    logger.exception("Unhandled exception: %s", error)
    return jsonify({"error": "Internal server error"}), 500

# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------
with app.app_context():
    db.create_all()
    seed_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
