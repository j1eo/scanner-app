# app.py
from flask import Flask, request, jsonify
from datetime import date, datetime
from db import SessionLocal
from models import Airline, Product, Flight, GuidelineTemplate, BottleRecord
from logic_evaluator import evaluate_action
from sqlalchemy import select
from flask_cors import CORS
import cv2, numpy as np, base64
from pyzbar.pyzbar import decode

app = Flask(__name__)

# Broad CORS (also see @after_request below to cover error responses)
CORS(app, resources={r"/*": {"origins": ["*", "null"]}}, supports_credentials=False)

# ───────────────────── Global CORS for *all* responses (incl. 4xx/5xx) ─────────────────────
@app.after_request
def apply_cors_headers(response):
    # Keep simple. If you need credentials, set a specific origin instead of "*"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# ───────────────────── Utilities ─────────────────────

def parse_percentage_like(value):
    """
    Accepts numeric strings like '80' or '80%' or numbers; returns float.
    Fallbacks to 0.0 on bad input.
    """
    if value is None:
        return 0.0
    try:
        if isinstance(value, str) and "%" in value:
            value = value.replace("%", "")
        return float(value)
    except Exception:
        return 0.0

def parse_int_like(value):
    try:
        return int(value)
    except Exception:
        return 0

# ───────────────────── IMAGE SCAN ENDPOINT ─────────────────────

@app.route("/scan-barcode-image", methods=["POST", "OPTIONS"])
def scan_barcode_image():
    """Decodes a barcode from a base64-encoded image and returns product info."""
    if request.method == "OPTIONS":
        # Preflight handled by @after_request too
        return jsonify({"status": "ok"}), 200

    try:
        data = request.get_json(force=True)
        image_b64 = data.get("image")
        if not image_b64:
            return jsonify({"error": "No image data provided"}), 400

        # Decode the base64 image
        image_bytes = base64.b64decode(image_b64.split(",")[-1])
        np_arr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        barcodes = decode(frame)
        if not barcodes:
            return jsonify({"success": False, "message": "No barcode detected"}), 404

        barcode_value = barcodes[0].data.decode("utf-8").strip()

        with SessionLocal() as db:
            product = db.execute(
                select(Product).where(Product.product_barcode == barcode_value)
            ).scalars().first()

        if not product:
            return jsonify({
                "success": True, "found": False,
                "barcode": barcode_value,
                "message": "Product not found in database"
            }), 200

        return jsonify({
            "success": True, "found": True,
            "barcode": barcode_value,
            "product_name": product.product_name,
            "brand": product.brand,
            "category": product.category,
            "bottle_size": product.bottle_size
        }), 200

    except Exception as e:
        app.logger.exception("Error decoding image")
        return jsonify({"error": str(e)}), 500


# ───────────────────── HELPERS ─────────────────────

def get_or_create_flight(db, *, airline_id, flight_number, origin, destination, flight_date, service_class):
    """Fetch or create a flight entry."""
    stmt = select(Flight).where(
        Flight.airline_id == airline_id,
        Flight.flight_number == flight_number,
        Flight.flight_date == flight_date,
        Flight.service_class == service_class
    )
    flight = db.execute(stmt).scalars().first()
    if flight:
        return flight

    flight = Flight(
        airline_id=airline_id,
        flight_number=flight_number,
        origin=origin or "UNKNOWN",
        destination=destination or "UNKNOWN",
        flight_date=flight_date,
        service_class=service_class
    )
    db.add(flight)
    db.commit()
    db.refresh(flight)
    return flight


# ───────────────────── BASE ROUTES ─────────────────────

@app.get("/health")
def health_check():
    return jsonify({
        "status": "API running",
        "timestamp": datetime.utcnow().isoformat()
    }), 200


# ───────────────────── AIRLINE ENDPOINTS ─────────────────────

@app.get("/airlines")
def list_airlines():
    """Return all airlines for dropdown/autocomplete."""
    with SessionLocal() as db:
        rows = db.query(Airline).all()
        return jsonify([
            {"airline_id": a.airline_id, "airline_code": a.airline_code, "airline_name": a.airline_name}
            for a in rows
        ]), 200


@app.get("/airline/by-name/<string:name>")
def airline_by_name(name):
    """Return a single airline by its name (case-insensitive)."""
    with SessionLocal() as db:
        airline = db.query(Airline).filter(Airline.airline_name.ilike(name)).first()
        if not airline:
            return jsonify({"error": "Airline not found"}), 404
        return jsonify({
            "airline_id": airline.airline_id,
            "airline_code": airline.airline_code,
            "airline_name": airline.airline_name
        }), 200


# ───────────────────── BARCODE ENDPOINTS ─────────────────────

@app.get("/barcode/check/<string:barcode>")
def check_barcode(barcode):
    """Check if barcode exists in the database."""
    try:
        with SessionLocal() as db:
            product = db.execute(
                select(Product).where(Product.product_barcode == barcode)
            ).scalars().first()
            if product:
                return jsonify({
                    "exists": True,
                    "barcode": product.product_barcode,
                    "product_name": product.product_name,
                    "category": product.category,
                    "brand": product.brand,
                    "bottle_size": product.bottle_size
                }), 200
            return jsonify({"exists": False, "barcode": barcode, "message": "Not found"}), 404
    except Exception as e:
        app.logger.exception("Error checking barcode")
        return jsonify({"error": str(e)}), 500


@app.post("/barcode/register")
def register_barcode():
    """Registers a bottle scan, evaluates it, and returns an action recommendation."""
    data = request.get_json(force=True)

    barcode = (data.get("barcode") or "").strip()
    airline_code = (data.get("airline_code") or "").strip()
    flight_number = (data.get("flight_number") or "").strip()
    service_class = (data.get("service_class") or "").strip()
    origin = data.get("origin")
    destination = data.get("destination")
    flight_date_str = data.get("flight_date")

    if not barcode or not airline_code or not flight_number or not service_class:
        return jsonify({"error": "Missing required fields"}), 400

    # Parse date safely
    if flight_date_str:
        try:
            fdate = datetime.fromisoformat(flight_date_str).date()
        except ValueError:
            return jsonify({"error": "Invalid flight_date format"}), 400
    else:
        fdate = date.today()

    try:
        with SessionLocal() as db:
            prod = db.execute(select(Product).where(Product.product_barcode == barcode)).scalars().first()
            if not prod:
                return jsonify({"error": "Product not found", "barcode": barcode}), 404

            airline = db.execute(select(Airline).where(Airline.airline_code == airline_code)).scalars().first()
            if not airline:
                return jsonify({"error": "Airline not found", "airline_code": airline_code}), 404

            flight = get_or_create_flight(
                db,
                airline_id=airline.airline_id,
                flight_number=flight_number,
                origin=origin,
                destination=destination,
                flight_date=fdate,
                service_class=service_class
            )

            # ────────────── Bottle Evaluation ──────────────
            qualitative = data.get("qualitative", {}) or {}

            fill_level = parse_percentage_like(qualitative.get("fill_level", 0))
            cleanliness = parse_int_like(qualitative.get("cleanliness", 0))  # Now 1–10 scale
            seal = (qualitative.get("seal_status") or qualitative.get("seal") or "unknown").lower()
            condition = (qualitative.get("bottle_condition") or qualitative.get("condition") or "unknown").lower()

            guideline = evaluate_action(
                db,
                airline_id=airline.airline_id,
                liquor_type=prod.category,
                service_class=service_class,
                fill_level=fill_level,
                cleanliness_score=cleanliness,
                seal_status=seal,
                bottle_condition=condition
            )

            action = guideline.get("action", "UNKNOWN")
            matched_guideline_id = guideline.get("guideline_id")

            # Save record if guideline found
            record = BottleRecord(
                product_barcode=prod.product_barcode,
                airline_id=airline.airline_id,
                flight_id=flight.flight_id,
                guideline_id=matched_guideline_id,
                fill_level=fill_level,
                seal_status=seal,
                cleanliness_score=cleanliness,
                label_status=qualitative.get("label_status", "intact").lower(),
                bottle_condition=condition,
                recommended_action=action
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            return jsonify({
                "status": "success",
                "recommended_action": action,
                "guideline_id": matched_guideline_id,
                "record_id": record.record_id,
                "product": {
                    "barcode": prod.product_barcode,
                    "name": prod.product_name,
                    "category": prod.category,
                    "brand": prod.brand,
                    "bottle_size": prod.bottle_size
                },
                "flight": {
                    "flight_id": flight.flight_id,
                    "number": flight.flight_number,
                    "origin": flight.origin,
                    "destination": flight.destination,
                    "date": str(flight.flight_date),
                    "service_class": flight.service_class
                }
            }), 200

    except Exception as e:
        app.logger.exception("Error registering bottle")
        return jsonify({"error": str(e)}), 500



# ───────────────────── MAIN ─────────────────────

if __name__ == "__main__":
    print("Flask API running on http://127.0.0.1:6060 ...")
    app.run(host="0.0.0.0", port=6060, debug=True)
