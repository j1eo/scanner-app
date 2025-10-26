# Alcohol Bottle Handling System (HackMTY 2025)

A backend system for **automatic scanning, evaluation, and handling of airline alcohol bottles**, designed to streamline sustainability and reuse tracking in airline operations.

Developed as part of **HackMTY 2025**, this project uses:

* **Flask (Python)** for the REST API backend
* **PostgreSQL** for structured data storage
* **OpenCV + pyzbar** for real-time barcode scanning
* **React Native** as the mobile interface for operators
* **Scikit-learn (planned)** for AI-based prediction of bottle handling actions

---

## Features

* **Barcode Scanning** – Read bottle barcodes via webcam or external scanner
* **API Integration** – Automatically lookup bottle info, airline, and flight
* **Manual Operator Input** – Record cleanliness, seal, fill level, and condition
* **Guideline Enforcement** – Policies per airline, class, and liquor type
* **Recommended Actions** – Keep / Refill / Replace / Discard
* **Pending Storage** – Temporarily store scans before completing record
* **PostgreSQL Schema** – Normalized database with referential integrity

---

## System Architecture

```
Camera/Scanner
   ↓
Flask API (Python)
   ↓
PostgreSQL Database (Airlines, Flights, Products, Guidelines, Records)
   ↓
React Native Mobile App (Operator UI)
```

---

## Project Structure

```
scaner/
│
├─ app.py                 # Flask API with endpoints for registering & saving records
├─ barcode_scanner.py     # Camera-based barcode reader using OpenCV + pyzbar
├─ db.py                  # Database connection manager (SQLAlchemy)
├─ models.py              # SQLAlchemy ORM models
├─ logic_evaluator.py     # Business logic for guideline compliance
├─ pending_store.py       # In-memory temporary intake storage
├─ requirements.txt       # Python dependencies
└─ README.md              # Documentation
```

---

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/AlcoholBottleHandling.git
cd scaner
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate      # (Windows)
# or
source venv/bin/activate   # (Linux/Mac)
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Dependencies include:

* `flask`
* `sqlalchemy`
* `psycopg2`
* `opencv-python`
* `pyzbar`
* `requests`
* `pandas`
* `scikit-learn`

---

## Database Configuration

You need a running PostgreSQL instance.

### Option 1 — Local Docker setup

Run this to spin up a local PostgreSQL container:

```bash
docker run --name bottle_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=AlcoholBottleHandling \
  -p 5432:5432 \
  postgres
```

Then set the connection in `db.py`:

```python
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/AlcoholBottleHandling"
```

### Option 2 — Remote teammate database

If you’re connecting to a teammate’s instance:

```python
DATABASE_URL = "postgresql://myuser:mypassword@IP-EXAMPLE:5432/mydatabase"
```

Make sure the database allows external connections (`listen_addresses='*'` and firewall open on port 5432).

---

## Running the Backend

```bash
python app.py
```

Flask will start on:

```
http://127.0.0.1:6060
```

You can test the API health endpoint:

```
GET http://127.0.0.1:6060/health
```

Should return:

```json
{
  "status": "API running",
  "timestamp": "2025-10-25T17:50:40.375589"
}
```

---


## API Endpoints

### `GET /health`

Check API status.

---

### `POST /barcode/register`

Registers a scanned barcode and links it to flight/airline context.

**Example JSON:**

```json
{
  "barcode": "WH750E",
  "airline_code": "EK",
  "flight_number": "EK022",
  "service_class": "Business",
  "origin": "DXB",
  "destination": "LHR",
  "flight_date": "2025-10-25"
}
```

**Returns:**
Product info, airline, flight, and an intake ID.

---

### `GET /intake/<intake_id>`

Retrieve stored intake info (pending record).

---

### `POST /intake/<intake_id>/details`

Add bottle condition details to complete the record.

**Example JSON:**

```json
{
  "fill_level": 85,
  "seal_status": "Sealed",
  "cleanliness_score": 9,
  "label_status": "Intact",
  "bottle_condition": "Good",
  "notes": "Visual check OK"
}
```

**Returns:**
Recommended action (`keep`, `refill`, `discard`, `replace`) and saved record.

---

## Frontend Integration

**React Nativa app**:

* Access the camera (barcode or AI image recognition)
* Display the scanned info and policy status
* Allow manual override or verification
* Synchronize records with the Flask API

---

## Troubleshooting

| Issue                           | Fix                                                  |
| ------------------------------- | ---------------------------------------------------- |
| Flask says “Connection refused” | Make sure PostgreSQL is running and the port is open |
| Barcode not detected            | Check lighting, camera focus, or pyzbar installation |
| CORS issue (Flutter)            | Add Flask-CORS to allow frontend access              |
| Database timeout                | Check if the correct IP/port is accessible           |

---

## Contributors

* **Jesús Leonardo Jiménez González**
* **Eber Edrey Alejo Berrones**
* **Israel Treviño Leyva**
* **Oziel Misael Velazquez Carrizales**
* HackMTY 2025, Monterrey, México

---

## License
Developed for educational purpose.
