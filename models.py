# models.py
from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime, DECIMAL, ForeignKey, Text
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# ───────────────────── AIRLINES ─────────────────────
class Airline(Base):
    __tablename__ = "airlines"
    airline_id = Column(Integer, primary_key=True, autoincrement=True)
    airline_code = Column(String(10), nullable=False)
    airline_name = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<Airline(code={self.airline_code}, name={self.airline_name})>"


# ───────────────────── PRODUCTS ─────────────────────
class Product(Base):
    __tablename__ = "products"
    product_barcode = Column(String(50), primary_key=True)
    product_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # liquor type: Whiskey, Vodka, Wine, etc.
    brand = Column(String(50), nullable=False)
    bottle_size = Column(String(20), nullable=False)

    def __repr__(self):
        return f"<Product(name={self.product_name}, category={self.category})>"


# ───────────────────── GUIDELINE TEMPLATES ─────────────────────
class GuidelineTemplate(Base):
    __tablename__ = "guideline_templates"
    guideline_id = Column(Integer, primary_key=True, autoincrement=True)
    airline_id = Column(Integer, ForeignKey("airlines.airline_id"), nullable=False)
    liquor_type = Column(String(50), nullable=False)
    service_class = Column(String(20), nullable=False)
    min_cleanliness_score = Column(Integer, nullable=False)  # 1–10 scale
    allowed_seal_status = Column(String(100), nullable=False)  # e.g. "sealed|resealed"
    allowed_bottle_condition = Column(String(100), nullable=False)  # e.g. "good|excellent"
    min_fill_level_threshold = Column(DECIMAL(5, 2), nullable=False)  # e.g. 75.0
    recommended_action = Column(String(20), nullable=False)  # e.g. "Keep", "Refill", "Discard"
    is_active = Column(Boolean, default=True)

    airline = relationship("Airline")

    def __repr__(self):
        return (
            f"<GuidelineTemplate(liquor={self.liquor_type}, class={self.service_class}, "
            f"action={self.recommended_action})>"
        )


# ───────────────────── FLIGHTS ─────────────────────
class Flight(Base):
    __tablename__ = "flights"
    flight_id = Column(Integer, primary_key=True, autoincrement=True)
    airline_id = Column(Integer, ForeignKey("airlines.airline_id"), nullable=False)
    flight_number = Column(String(20), nullable=False)
    origin = Column(String(50), nullable=False)
    destination = Column(String(50), nullable=False)
    flight_date = Column(Date, nullable=False)
    service_class = Column(String(20), nullable=False)

    airline = relationship("Airline")

    def __repr__(self):
        return f"<Flight(number={self.flight_number}, class={self.service_class})>"


# ───────────────────── BOTTLE RECORDS ─────────────────────
class BottleRecord(Base):
    __tablename__ = "bottle_records"
    record_id = Column(Integer, primary_key=True, autoincrement=True)
    product_barcode = Column(String(50), ForeignKey("products.product_barcode"), nullable=False)
    airline_id = Column(Integer, ForeignKey("airlines.airline_id"), nullable=False)
    flight_id = Column(Integer, ForeignKey("flights.flight_id"), nullable=False)
    guideline_id = Column(Integer, ForeignKey("guideline_templates.guideline_id"))
    fill_level = Column(DECIMAL(5, 2), nullable=False)
    seal_status = Column(String(50), nullable=False)
    cleanliness_score = Column(Integer, nullable=False)
    label_status = Column(String(50), nullable=False, default="intact")
    bottle_condition = Column(String(50), nullable=False)
    recommended_action = Column(String(20), nullable=False)
    scan_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    product = relationship("Product")
    airline = relationship("Airline")
    flight = relationship("Flight")
    guideline = relationship("GuidelineTemplate")

    def __repr__(self):
        return (
            f"<BottleRecord(barcode={self.product_barcode}, "
            f"action={self.recommended_action}, "
            f"condition={self.bottle_condition})>"
        )
