from flask import Flask, request, jsonify
from flask_cors import CORS
from db import SessionLocal
from models import Product
from sqlalchemy import select
import cv2
import numpy as np
import base64
from pyzbar.pyzbar import decode

app = Flask(__name__)
CORS(app)

@app.post("/scan-barcode-image")
def scan_barcode_image():
    """Receives a base64-encoded image, decodes the barcode, and checks DB."""
    try:
        data = request.get_json(force=True)
        image_b64 = data.get("image")

        if not image_b64:
            return jsonify({"error": "No image data provided"}), 400

        # Decode base64 image
        image_bytes = base64.b64decode(image_b64.split(",")[-1])
        np_arr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # Detect barcodes
        barcodes = decode(frame)
        if not barcodes:
            return jsonify({"success": False, "message": "No barcode detected"}), 404

        # Take first detected barcode
        barcode_value = barcodes[0].data.decode("utf-8").strip()

        # Check product in DB
        db = SessionLocal()
        product = db.execute(
            select(Product).where(Product.product_barcode == barcode_value)
        ).scalars().first()
        db.close()

        if not product:
            return jsonify({
                "success": True,
                "found": False,
                "barcode": barcode_value,
                "message": "Product not found in database"
            }), 200

        return jsonify({
            "success": True,
            "found": True,
            "barcode": barcode_value,
            "product_name": product.product_name,
            "brand": product.brand,
            "category": product.category,
            "bottle_size": product.bottle_size
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    print("🚀 Flask backend running at http://127.0.0.1:6060")
    app.run(host="0.0.0.0", port=6060, debug=True)
