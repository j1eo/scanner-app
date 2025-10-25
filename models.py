# models.py
from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime, Text, DECIMAL, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Airline(Base):
    __tablename__ = "airlines"
    airline_id = Column(Integer, primary_key=True)
    airline_code = Column(String, nullable=False)
    airline_name = Column(String, nullable=False)

class Product(Base):
    __tablename__ = "products"
    product_barcode = Column(String, primary_key=True)
    product_name = Column(String, nullable=False)
    category = Column(String, nullable=False)      # liquor type: Whiskey, Vodka, Wine, ...
    brand = Column(String, nullable=False)
    bottle_size = Column(String, nullable=False)

class GuidelineTemplate(Base):
    __tablename__ = "guideline_templates"
    guideline_id = Column(Integer, primary_key=True)
    airline_id = Column(Integer, ForeignKey("airlines.airline_id"), nullable=False)
    liquor_type = Column(String, nullable=False)    # matches Product.category
    service_class = Column(String, nullable=False)  # Business / First
    policy_name = Column(String, nullable=False)
    min_cleanliness_score = Column(Integer, nullable=False)
    allowed_seal_status = Column(String, nullable=False)          # e.g. 'sealed','resealed','any'
    allowed_bottle_condition = Column(String, nullable=False)     # 'Good','Excellent','Fair','Damaged','any'
    min_fill_level_threshold = Column(DECIMAL, nullable=False)
    label_requirements = Column(String, nullable=False)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)

    airline = relationship("Airline")

class Flight(Base):
    __tablename__ = "flights"
    flight_id = Column(Integer, primary_key=True)
    airline_id = Column(Integer, ForeignKey("airlines.airline_id"), nullable=False)
    flight_number = Column(String, nullable=False)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    flight_date = Column(Date, nullable=False)
    service_class = Column(String, nullable=False)

    airline = relationship("Airline")

class BottleRecord(Base):
    __tablename__ = "bottle_records"
    record_id = Column(Integer, primary_key=True)
    product_barcode = Column(String, ForeignKey("products.product_barcode"), nullable=False)
    airline_id = Column(Integer, ForeignKey("airlines.airline_id"), nullable=False)
    flight_id = Column(Integer, ForeignKey("flights.flight_id"), nullable=False)
    guideline_id = Column(Integer, ForeignKey("guideline_templates.guideline_id"), nullable=False)
    fill_level = Column(DECIMAL, nullable=False)
    seal_status = Column(String, nullable=False)
    cleanliness_score = Column(Integer, nullable=False)
    label_status = Column(String, nullable=False)
    bottle_condition = Column(String, nullable=False)
    recommended_action = Column(String, nullable=False)
    scan_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes = Column(Text)

    product = relationship("Product")
    airline = relationship("Airline")
    flight = relationship("Flight")
    guideline = relationship("GuidelineTemplate")
