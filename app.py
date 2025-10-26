from flask import Flask, request, jsonify
from datetime import date, datetime
from db import SessionLocal
from models import Airline, Product, Flight, GuidelineTemplate, BottleRecord
from logic_evaluator import evaluate_action
from pending_store import PENDING
from sqlalchemy import select
from flask_cors import CORS
import cv2, numpy as np, base64
from pyzbar.pyzbar import decode

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["*", "null"]}}, supports_credentials=True)

# ───────────────────── IMAGE SCAN ENDPOINT ─────────────────────

@app.route("/scan-barcode-image", methods=["POST", "OPTIONS"])
def scan_barcode_image():
    if request.method == "OPTIONS":
        resp = jsonify({"status": "ok"})
        resp.headers.add("Access-Control-Allow-Origin", "*")
        resp.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        resp.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return resp, 200

    try:
        data = request.get_json(force=True)
        image_b64 = data.get("image")
        if not image_b64:
            return jsonify({"error": "No image data provided"}), 400

        image_bytes = base64.b64decode(image_b64.split(",")[-1])
        np_arr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        barcodes = decode(frame)
        if not barcodes:
            return jsonify({"success": False, "message": "No barcode detected"}), 404

        barcode_value = barcodes[0].data.decode("utf-8").strip()
        db = SessionLocal()
        product = db.execute(
            select(Product).where(Product.product_barcode == barcode_value)
        ).scalars().first()
        db.close()

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
        app.logger.error(f"Error decoding image: {e}")
        return jsonify({"error": str(e)}), 500

# ───────────────────── HELPERS ─────────────────────

def get_or_create_flight(db, *, airline_id, flight_number, origin, destination, flight_date, service_class):
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
    db.add(flight); db.commit(); db.refresh(flight)
    return flight

# ───────────────────── BASE ROUTES ─────────────────────

@app.get("/health")
def health_check():
    return jsonify({"status": "✅ API running", "timestamp": datetime.utcnow().isoformat()}), 200

# ───────────────────── AIRLINE ENDPOINTS ─────────────────────

@app.get("/airlines")
def list_airlines():
    """Return all airlines for dropdown/autocomplete."""
    db = SessionLocal()
    rows = db.query(Airline).all()
    db.close()
    return jsonify([
        {"airline_id": a.airline_id, "airline_code": a.airline_code, "airline_name": a.airline_name}
        for a in rows
    ])

@app.get("/airline/by-name/<string:name>")
def airline_by_name(name):
    """Return a single airline by its name."""
    db = SessionLocal()
    airline = db.query(Airline).filter(Airline.airline_name == name).first()
    db.close()
    if not airline:
        return jsonify({"error": "Airline not found"}), 404
    return jsonify({
        "airline_id": airline.airline_id,
        "airline_code": airline.airline_code,
        "airline_name": airline.airline_name
    })

# ───────────────────── BARCODE ENDPOINTS ─────────────────────

@app.get("/barcode/check/<string:barcode>")
def check_barcode(barcode):
    db = SessionLocal()
    try:
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
        app.logger.error(f"Error checking barcode: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.post("/barcode/register")
def register_barcode():
    data = request.get_json(force=True)
    barcode = (data.get("barcode") or "").strip()
    airline_code = (data.get("airline_code") or "").strip()
    flight_number = (data.get("flight_number") or "").strip()
    service_class = (data.get("service_class") or "").strip()
    origin = data.get("origin"); destination = data.get("destination")
    flight_date_str = data.get("flight_date")

    if not barcode or not airline_code or not flight_number or not service_class:
        return jsonify({"error": "Missing required fields"}), 400

    if flight_date_str:
        try:
            fdate = datetime.fromisoformat(flight_date_str).date()
        except ValueError:
            return jsonify({"error": "Invalid flight_date format"}), 400
    else:
        fdate = date.today()

    db = SessionLocal()
    try:
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

        intake_payload = {
            "product_barcode": prod.product_barcode,
            "product_name": prod.product_name,
            "liquor_type": prod.category,
            "brand": prod.brand,
            "bottle_size": prod.bottle_size,
            "airline_id": airline.airline_id,
            "airline_code": airline.airline_code,
            "airline_name": airline.airline_name,
            "flight_id": flight.flight_id,
            "flight_number": flight.flight_number,
            "service_class": service_class,
            "origin": flight.origin,
            "destination": flight.destination,
            "flight_date": str(flight.flight_date)
        }
        intake_id = PENDING.create(intake_payload)
        app.logger.info(f"Registered barcode {barcode} -> intake_id={intake_id}")

        return jsonify({
            "intake_id": intake_id,
            "product": {
                "barcode": prod.product_barcode,
                "name": prod.product_name,
                "category": prod.category,
                "brand": prod.brand,
                "bottle_size": prod.bottle_size
            },
            "airline": {
                "airline_id": airline.airline_id,
                "code": airline.airline_code,
                "name": airline.airline_name
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
    finally:
        db.close()

# ───────────────────── MAIN ─────────────────────

if __name__ == "__main__":
    print("🚀 Flask API running on http://127.0.0.1:6060 ...")
    app.run(host="0.0.0.0", port=6060, debug=True)
