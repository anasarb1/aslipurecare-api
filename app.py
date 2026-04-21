"""
AslipureCare API - Main Flask Application
A microservice for managing skincare products.
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

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
# App + DB setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///products.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

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
# Seed data helper
# ---------------------------------------------------------------------------
SEED_PRODUCTS = [
    {
        "id": "1",
        "name": "Hydrating Vitamin C Serum",
        "price": 29.99,
        "description": "Brightening serum with 15% vitamin C, hyaluronic acid, and niacinamide.",
    },
    {
        "id": "2",
        "name": "Gentle Foaming Cleanser",
        "price": 14.99,
        "description": "Sulfate-free daily cleanser suitable for all skin types, pH-balanced formula.",
    },
    {
        "id": "3",
        "name": "SPF 50 Lightweight Moisturiser",
        "price": 34.99,
        "description": "Broad-spectrum UVA/UVB protection in a non-greasy, fast-absorbing moisturiser.",
    },
]

def seed_db():
    if Product.query.count() == 0:
        for p in SEED_PRODUCTS:
            db.session.add(Product(**p))
        db.session.commit()
        logger.info("Database seeded with %d products", len(SEED_PRODUCTS))

# ---------------------------------------------------------------------------
# Request logging decorator
# ---------------------------------------------------------------------------
def log_request(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        timestamp = datetime.now(timezone.utc).isoformat()
        logger.info(
            "REQUEST  | %s | %s %s | ip=%s",
            timestamp, request.method, request.path, request.remote_addr,
        )
        response = func(*args, **kwargs)
        status = response[1] if isinstance(response, tuple) else 200
        logger.info(
            "RESPONSE | %s | %s %s | status=%s",
            timestamp, request.method, request.path, status,
        )
        return response
    return wrapper

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
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products])


@app.route("/products", methods=["POST"])
@log_request
def create_product():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    missing = [f for f in ("name", "price", "description") if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    if not isinstance(data["price"], (int, float)) or data["price"] <= 0:
        return jsonify({"error": "'price' must be a positive number"}), 400

    product = Product(
        name        = str(data["name"]).strip(),
        price       = round(float(data["price"]), 2),
        description = str(data["description"]).strip(),
    )
    db.session.add(product)
    db.session.commit()
    logger.info("Created product id=%s name=%s", product.id, product.name)
    return jsonify(product.to_dict()), 201

# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
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
