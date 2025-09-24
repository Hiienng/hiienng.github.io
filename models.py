from sqlalchemy import Column, Integer, String, Boolean, Numeric, TIMESTAMP, func
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    # role column có thể vẫn tồn tại trong DB cũ nhưng không dùng nữa

class Booking(Base):
    __tablename__ = "bookings"
    booking_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(50), nullable=False)
    start_date = Column(TIMESTAMP, nullable=True)
    end_date = Column(TIMESTAMP, nullable=True)
    no_visitors = Column(Integer, nullable=True)
    payment_flag = Column(Boolean, default=False)
    no_day = Column(Integer, nullable=True)
    payment_value = Column(Numeric(12, 2), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

class RoomRate(Base):
    __tablename__ = "room_rates"
    id = Column(Integer, primary_key=True, index=True)
    nightly_rate = Column(Numeric(12,2), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())