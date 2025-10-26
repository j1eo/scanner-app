# db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

##DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://myuser:mypassword@localhost:5432/mydatabase")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://myuser:mypassword@localhost:5433/postgres")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)    
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
