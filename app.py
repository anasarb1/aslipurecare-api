"""
AslipureCare API - Main Flask Application
A microservice for managing skincare products.
"""

import logging
import uuid
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, jsonify, request

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
logger = logging.getLogger("aslipurecare")

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
app = Flask(__name__)

# ---------------------------------------------------------------------------
# In-memory product store (seed data)
# ---------------------------------------------------------------------------
_products: list[dict] = [
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


# ---------------------------------------------------------------------------
# Request logging decorator
# ---------------------------------------------------------------------------
def log_request(func):
    """Log every incoming request with timestamp, method, and endpoint."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        timestamp = datetime.now(timezone.utc).isoformat()
        logger.info(
            "REQUEST  | %s | %s %s | ip=%s",
            timestamp,
            request.method,
            request.path,
            request.remote_addr,
        )
        response = func(*args, **kwargs)
        # Flask view functions may return a tuple (response, status_code)
        status = response[1] if isinstance(response, tuple) else 200
        logger.info(
            "RESPONSE | %s | %s %s | status=%s",
            timestamp,
            request.method,
            request.path,
            status,
        )
        return response

    return wrapper


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
@log_request
def index():
    """Root endpoint — quick liveness check."""
    return jsonify({"message": "AslipureCare API is running", "status": "healthy"})


@app.route("/health", methods=["GET"])
@log_request
def health():
    """Detailed health check used by load-balancers and CI pipelines."""
    return jsonify(
        {
            "status": "healthy",
            "service": "aslipurecare-api",
            "version": "1.0.0",
        }
    )


@app.route("/products", methods=["GET"])
@log_request
def get_products():
    """Return the full list of skincare products."""
    return jsonify(_products)


@app.route("/products", methods=["POST"])
@log_request
def create_product():
    """
    Create a new skincare product.

    Expected JSON body:
        {
            "name":        "Product name"   (required, string),
            "price":       19.99            (required, positive number),
            "description": "Product info"  (required, string)
        }

    Returns the created product object (201 Created) or a 400 error.
    """
    data = request.get_json(silent=True)

    # --- Validation ---
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    missing = [f for f in ("name", "price", "description") if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    if not isinstance(data["price"], (int, float)) or data["price"] <= 0:
        return jsonify({"error": "'price' must be a positive number"}), 400

    # --- Persist ---
    product = {
        "id": str(uuid.uuid4()),
        "name": str(data["name"]).strip(),
        "price": round(float(data["price"]), 2),
        "description": str(data["description"]).strip(),
    }
    _products.append(product)
    logger.info("Created product id=%s name=%s", product["id"], product["name"])

    return jsonify(product), 201


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
# Entry-point (development server only — production uses gunicorn)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
