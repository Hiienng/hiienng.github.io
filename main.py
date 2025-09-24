from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

from database import get_db, Base, engine
from models import User, Booking, RoomRate
from auth import hash_password, verify_password, create_access_token, decode_access_token
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Schemas ----------
class UserCreate(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    email: str
    password: str

class BookingCreate(BaseModel):
    start_date: datetime
    end_date: datetime
    no_visitors: int
    no_day: Optional[int] = None
    payment_value: Optional[Decimal] = None

class BookingOut(BaseModel):
    booking_id: int
    email: str
    start_date: datetime | None
    end_date: datetime | None
    no_visitors: int | None
    no_day: int | None
    payment_flag: bool | None
    payment_value: Decimal | None
    created_at: datetime | None
    reserved_until: Optional[datetime] = None
    class Config:
        orm_mode = True

class PublicBookingOut(BaseModel):
    start_date: datetime | None
    end_date: datetime | None

class RateUpdate(BaseModel):
    nightly_rate: Decimal

class RateOut(BaseModel):
    nightly_rate: Decimal
    updated_at: Optional[datetime]
    class Config:
        orm_mode = True

# ---------- Helpers ----------
def decode_token(token: str):
    try:
        return decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_current_user(authorization: str = Header(..., alias="Authorization"),
                     db: Session = Depends(get_db)) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_admin(authorization: str = Header(..., alias="Authorization")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload.get("adm"):
        raise HTTPException(status_code=403, detail="Admin only")

# ---------- Root ----------
@app.get("/")
def root():
    return {"message": "API OK"}

@app.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    email_lower = user.email.lower()

    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(email=user.email, password_hash=hash_password(user.password))
    db.add(new_user)
    db.commit()
    return {"message": "User created", "is_admin": email_lower.startswith("admin@")}

@app.post("/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    is_admin = db_user.email.lower().startswith("admin@")
    token_claims = {"sub": db_user.email}
    if is_admin:
        token_claims["adm"] = True
    token = create_access_token(token_claims)

    return {
        "message": "Login successful",
        "email": db_user.email,
        "is_admin": is_admin,
        "access_token": token
    }

# ---------- Public bookings (no auth) ----------
@app.get("/public-bookings", response_model=List[PublicBookingOut])
def public_bookings(db: Session = Depends(get_db)):
    active_since = datetime.utcnow() - timedelta(minutes=10)
    rows = db.query(Booking.start_date, Booking.end_date).filter(
        (Booking.payment_flag == True) | (Booking.created_at >= active_since)
    ).all()
    return [{"start_date": r[0], "end_date": r[1]} for r in rows]

# ---------- Rate (admin) ----------
@app.get("/rate", response_model=RateOut)
def get_rate(db: Session = Depends(get_db)):
    rate = db.query(RoomRate).order_by(RoomRate.id.asc()).first()
    if not rate:
        return RateOut(nightly_rate=Decimal("500000"), updated_at=None)
    return rate

@app.post("/rate", response_model=RateOut)
def set_rate(rate: RateUpdate,
             db: Session = Depends(get_db),
             _: None = Depends(require_admin)):
    existing = db.query(RoomRate).order_by(RoomRate.id.asc()).first()
    if not existing:
        new_rate = RoomRate(nightly_rate=rate.nightly_rate)
        db.add(new_rate)
        db.commit()
        db.refresh(new_rate)
        return new_rate
    existing.nightly_rate = rate.nightly_rate
    db.commit()
    db.refresh(existing)
    return existing

# ---------- Booking ----------
def serialize_booking(b: Booking) -> dict:
    return {
        "booking_id": b.booking_id,
        "email": b.email,
        "start_date": b.start_date,
        "end_date": b.end_date,
        "no_visitors": b.no_visitors,
        "no_day": b.no_day,
        "payment_flag": b.payment_flag,
        "payment_value": b.payment_value,
        "created_at": b.created_at,
        "reserved_until": (b.created_at + timedelta(minutes=10)) if b.created_at else None,
    }

@app.post("/book", response_model=BookingOut)
def create_booking(booking: BookingCreate,
                   current_user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    if booking.end_date <= booking.start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")
    # Only consider active bookings: paid or created within the last 10 minutes (waiting window)
    active_since = datetime.utcnow() - timedelta(minutes=10)
    overlap = db.query(Booking).filter(
        Booking.start_date < booking.end_date,
        Booking.end_date > booking.start_date,
        ((Booking.payment_flag == True) | (Booking.created_at >= active_since))
    ).first()
    if overlap:
        raise HTTPException(status_code=409, detail="Selected date range already booked")
    # Compute no_day from whole-day difference (end exclusive)
    start_utc = booking.start_date
    end_utc = booking.end_date
    no_day = max(0, int((end_utc - start_utc).total_seconds() // 86400))

    new_booking = Booking(
        email=current_user.email,
        start_date=booking.start_date,
        end_date=booking.end_date,
        no_visitors=booking.no_visitors,
        no_day=no_day,
        payment_value=booking.payment_value
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return serialize_booking(new_booking)

@app.get("/my-bookings", response_model=List[BookingOut])
def my_bookings(current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    rows = db.query(Booking).filter(Booking.email == current_user.email).order_by(Booking.created_at.desc()).all()
    return [serialize_booking(b) for b in rows]

@app.get("/all-bookings", response_model=List[BookingOut])
def all_bookings(_: None = Depends(require_admin),
                 db: Session = Depends(get_db)):
    rows = db.query(Booking).order_by(Booking.created_at.desc()).all()
    return [serialize_booking(b) for b in rows]

@app.post("/bookings/{booking_id}/pay", response_model=BookingOut)
def pay_booking(booking_id: int,
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    b = db.query(Booking).filter(
        Booking.booking_id == booking_id,
        Booking.email == current_user.email
    ).first()
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")
    if b.payment_flag:
        raise HTTPException(status_code=400, detail="Booking already paid")
    # allow payment within 10 minutes from creation
    created = b.created_at or datetime.utcnow()
    if datetime.utcnow() - created > timedelta(minutes=10):
        raise HTTPException(status_code=400, detail="Payment window expired")
    b.payment_flag = True
    db.commit()
    db.refresh(b)
    return serialize_booking(b)

@app.delete("/bookings/{booking_id}")
def cancel_booking(booking_id: int,
                   current_user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    b = db.query(Booking).filter(
        Booking.booking_id == booking_id,
        Booking.email == current_user.email
    ).first()
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")
    if b.payment_flag:
        raise HTTPException(status_code=400, detail="Cannot cancel a paid booking")
    db.delete(b)
    db.commit()
    return {"message": "Booking canceled"}
