import base64
import binascii
import os
import uuid
from pathlib import Path

import requests

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta, date
from decimal import Decimal

from database import get_db, Base, engine
from models import User, Booking, RoomRate, Product, DailyRate
from auth import hash_password, verify_password, create_access_token, decode_access_token
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

Base.metadata.create_all(bind=engine)

# Media setup for uploaded product images
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", "media")).resolve()
PRODUCT_MEDIA_DIR = MEDIA_ROOT / "products"
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
PRODUCT_MEDIA_DIR.mkdir(parents=True, exist_ok=True)

IMAGEKIT_PUBLIC_KEY = os.getenv("IMAGEKIT_PUBLIC_KEY")
IMAGEKIT_PRIVATE_KEY = os.getenv("IMAGEKIT_PRIVATE_KEY")
_imagekit_endpoint_raw = os.getenv("IMAGEKIT_URL_ENDPOINT")
IMAGEKIT_URL_ENDPOINT = _imagekit_endpoint_raw.rstrip("/") if _imagekit_endpoint_raw else None
IMAGEKIT_UPLOAD_ENDPOINT = os.getenv("IMAGEKIT_UPLOAD_ENDPOINT", "https://upload.imagekit.io/api/v1/files/upload")
IMAGEKIT_FOLDER = os.getenv("IMAGEKIT_FOLDER", "/products")

app.mount("/media", StaticFiles(directory=str(MEDIA_ROOT)), name="media")

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


class ProductCreate(BaseModel):
    main_type: str
    sub_type: Optional[str] = None
    price: Optional[Decimal] = None
    price_start_date: Optional[date] = None
    description: Optional[str] = None
    quantity_type: Optional[str] = None
    created_by: Optional[str] = None
    image_url: Optional[str] = None
    image_data: Optional[str] = None
    image_filename: Optional[str] = None


class ProductOut(BaseModel):
    product_id: int
    main_type: str
    sub_type: Optional[str] = None
    price: Optional[Decimal] = None
    price_start_date: Optional[date] = None
    description: Optional[str] = None
    quantity_type: Optional[str] = None
    created_at: Optional[datetime]
    created_by: Optional[str]
    image_url: Optional[str] = None
    image_path: Optional[str] = None

    class Config:
        orm_mode = True


class ProductImageUpdate(BaseModel):
    image_data: Optional[str] = None
    image_url: Optional[str] = None
    image_filename: Optional[str] = None


class DailyRateSet(BaseModel):
    rate_date: date
    price: Decimal


class DailyRateOut(BaseModel):
    rate_date: date
    price: Decimal
    created_by: Optional[str] = None

    class Config:
        orm_mode = True

# ---------- Helpers ----------
def decode_token(token: str):
    try:
        return decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_base_nightly_rate(db: Session) -> Decimal:
    rate = db.query(RoomRate).order_by(RoomRate.id.asc()).first()
    if not rate or rate.nightly_rate is None:
        return Decimal("500000")
    return Decimal(rate.nightly_rate)


def calculate_booking_total(db: Session, start_dt: datetime, end_dt: datetime) -> Decimal:
    base_rate = get_base_nightly_rate(db)
    start_date = start_dt.date()
    end_date = end_dt.date()
    overrides = db.query(DailyRate).filter(
        DailyRate.rate_date >= start_date,
        DailyRate.rate_date < end_date
    ).all()
    override_map = {row.rate_date: Decimal(row.price) for row in overrides}
    total = Decimal("0")
    current = start_date
    while current < end_date:
        total += override_map.get(current, base_rate)
        current += timedelta(days=1)
    return total


def store_product_image(image_data: str, filename_hint: Optional[str] = None) -> tuple[str, Optional[str]]:
    if not image_data:
        raise HTTPException(status_code=400, detail="Missing image data")

    data_part = image_data
    ext: Optional[str] = None
    if image_data.startswith("data:") and "," in image_data:
        header, data_part = image_data.split(",", 1)
        try:
            mime = header.split(";")[0].split(":")[1]
            ext = mime.split("/")[1]
        except (IndexError, ValueError):
            ext = None

    if not ext and filename_hint:
        ext = Path(filename_hint).suffix.replace(".", "") or None
    if not ext:
        ext = "png"
    ext = ext.lower()

    try:
        binary = base64.b64decode(data_part)
    except (ValueError, binascii.Error):
        raise HTTPException(status_code=400, detail="Invalid image encoding")

    encoded_payload = base64.b64encode(binary).decode("ascii")

    if IMAGEKIT_PRIVATE_KEY and IMAGEKIT_URL_ENDPOINT:
        file_name = filename_hint or f"{uuid.uuid4().hex}.{ext}"
        if "." not in file_name:
            file_name = f"{file_name}.{ext}"
        multipart_payload = {
            "file": (None, encoded_payload),
            "fileName": (None, file_name),
            "useUniqueFileName": (None, "true"),
        }
        if IMAGEKIT_FOLDER:
            multipart_payload["folder"] = (None, IMAGEKIT_FOLDER)
        try:
            response = requests.post(
                IMAGEKIT_UPLOAD_ENDPOINT,
                auth=(IMAGEKIT_PRIVATE_KEY, ""),
                files=multipart_payload,
                timeout=20,
            )
        except requests.RequestException as exc:
            raise HTTPException(status_code=502, detail="Unable to upload image") from exc

        if response.status_code >= 400:
            try:
                error_payload = response.json()
            except ValueError:
                error_payload = {}
            message = error_payload.get("message") if isinstance(error_payload, dict) else None
            raise HTTPException(status_code=502, detail=message or "Image upload failed")

        try:
            payload = response.json()
        except ValueError as exc:
            raise HTTPException(status_code=502, detail="Invalid response from image server") from exc
        file_path = payload.get("filePath")
        normalized_path = file_path.lstrip("/") if isinstance(file_path, str) else None
        url = payload.get("url")
        if not url and normalized_path and IMAGEKIT_URL_ENDPOINT:
            url = f"{IMAGEKIT_URL_ENDPOINT}/{normalized_path}"
        if not url:
            raise HTTPException(status_code=502, detail="Image upload response missing URL")
        return url, normalized_path

    file_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = PRODUCT_MEDIA_DIR / file_name
    with open(file_path, "wb") as fh:
        fh.write(binary)
    relative_path = f"products/{file_name}"
    return f"/media/{relative_path}", relative_path


def compose_product_image_fields(image_url: Optional[str], image_data: Optional[str], image_filename: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    cleaned_data = image_data.strip() if isinstance(image_data, str) else None
    cleaned_url = image_url.strip() if isinstance(image_url, str) else None
    if cleaned_data:
        return store_product_image(cleaned_data, image_filename)
    if cleaned_url:
        if cleaned_url.startswith("http://") or cleaned_url.startswith("https://"):
            return cleaned_url, None
        normalized_path = cleaned_url.lstrip("/")
        if IMAGEKIT_URL_ENDPOINT:
            return f"{IMAGEKIT_URL_ENDPOINT}/{normalized_path}", normalized_path
        if cleaned_url.startswith("/"):
            return cleaned_url, normalized_path
        return cleaned_url, normalized_path
    return None, None

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

# ---------- Daily Rates ----------
@app.get("/daily-rates", response_model=List[DailyRateOut])
def list_daily_rates(start: Optional[date] = None,
                     end: Optional[date] = None,
                     db: Session = Depends(get_db)):
    query = db.query(DailyRate)
    if start:
        query = query.filter(DailyRate.rate_date >= start)
    if end:
        query = query.filter(DailyRate.rate_date < end)
    rows = query.order_by(DailyRate.rate_date.asc()).all()
    return rows


@app.post("/daily-rates", response_model=DailyRateOut)
def set_daily_rate(payload: DailyRateSet,
                   current_user: User = Depends(get_current_user),
                   _: None = Depends(require_admin),
                   db: Session = Depends(get_db)):
    if payload.price <= 0:
        raise HTTPException(status_code=400, detail="Price must be positive")
    existing = db.query(DailyRate).filter(DailyRate.rate_date == payload.rate_date).first()
    if existing:
        existing.price = payload.price
        existing.created_by = current_user.email if current_user else existing.created_by
        db.commit()
        db.refresh(existing)
        return existing
    new_rate = DailyRate(
        rate_date=payload.rate_date,
        price=payload.price,
        created_by=current_user.email if current_user else None
    )
    db.add(new_rate)
    db.commit()
    db.refresh(new_rate)
    return new_rate


@app.delete("/daily-rates/{rate_date}")
def delete_daily_rate(rate_date: date,
                      _: None = Depends(require_admin),
                      db: Session = Depends(get_db)):
    row = db.query(DailyRate).filter(DailyRate.rate_date == rate_date).first()
    if not row:
        raise HTTPException(status_code=404, detail="Daily rate not found")
    db.delete(row)
    db.commit()
    return {"message": "Daily rate removed"}

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
        payment_value=calculate_booking_total(db, booking.start_date, booking.end_date)
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


# ---------- Products (admin) ----------
@app.get("/public-products", response_model=List[ProductOut])
def public_products(db: Session = Depends(get_db)):
    rows = db.query(Product).order_by(Product.created_at.desc()).all()
    return rows


@app.get("/public-products/{product_id}", response_model=ProductOut)
def public_product_detail(product_id: int,
                          db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/products", response_model=List[ProductOut])
def list_products(_: None = Depends(require_admin),
                  db: Session = Depends(get_db)):
    rows = db.query(Product).order_by(Product.created_at.desc()).all()
    return rows


@app.post("/products", response_model=ProductOut)
def create_product(payload: ProductCreate,
                   current_user: User = Depends(get_current_user),
                   _: None = Depends(require_admin),
                   db: Session = Depends(get_db)):
    image_url, image_path = compose_product_image_fields(payload.image_url, payload.image_data, payload.image_filename)
    new_product = Product(
        main_type=payload.main_type,
        sub_type=payload.sub_type,
        price=payload.price,
        price_start_date=payload.price_start_date,
        description=payload.description,
        quantity_type=payload.quantity_type,
        image_url=image_url,
        image_path=image_path,
        created_by=current_user.email if current_user else payload.created_by
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


@app.post("/products/{product_id}/image", response_model=ProductOut)
def update_product_image(product_id: int,
                         payload: ProductImageUpdate,
                         _: None = Depends(require_admin),
                         db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    image_url, image_path = compose_product_image_fields(payload.image_url, payload.image_data, payload.image_filename)
    if not image_url:
        raise HTTPException(status_code=400, detail="Image data or URL required")
    # remove previous stored file if replacing with new local file
    if product.image_path:
        old_file = MEDIA_ROOT / product.image_path
        should_remove = False
        if image_path and product.image_path != image_path:
            should_remove = True
        if image_path is None:
            should_remove = True
        if should_remove and old_file.exists():
            try:
                old_file.unlink()
            except OSError:
                pass
    product.image_url = image_url
    product.image_path = image_path
    db.commit()
    db.refresh(product)
    return product


@app.delete("/products/{product_id}")
def delete_product(product_id: int,
                   _: None = Depends(require_admin),
                   db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.image_path:
        stored = MEDIA_ROOT / product.image_path
        if stored.exists():
            try:
                stored.unlink()
            except OSError:
                pass
    db.delete(product)
    db.commit()
    return {"message": "Product deleted"}
