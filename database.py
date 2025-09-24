import os
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Boolean, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = "postgresql://neondb_owner:npg_rI4LDaegN8uU@ep-tiny-mouse-adruvfw6-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"


engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Hàm DB
def get_user_by_email(email: str):
    with engine.connect() as conn:
        query = select(users).where(users.c.email == email)
        result = conn.execute(query).first()
        return result

def create_user(email: str, hashed_password: str):
    with engine.connect() as conn:
        query = insert(users).values(email=email, hashed_password=hashed_password, created_at=datetime.utcnow())
        conn.execute(query)
        conn.commit()