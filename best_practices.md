# 📘 Project Best Practices

## 1. Project Purpose
A lightweight booking portal with:
- Public/static frontend (vanilla HTML/CSS/JS, Tailwind via CDN)
- FastAPI backend for authentication (JWT), nightly rate management, and booking lifecycle
- Admin capabilities to manage nightly rates and view all bookings; regular users can browse availability and create bookings

Domain: small property booking with date-range selection and basic pricing.

## 2. Project Structure
- Backend (Python/FastAPI/SQLAlchemy):
  - main.py — FastAPI app, routes, request/response schemas, dependency wiring, CORS
  - models.py — SQLAlchemy ORM models (User, Booking, RoomRate)
  - database.py — SQLAlchemy engine, SessionLocal, Base; dotenv loading
  - auth.py — Password hashing (passlib), JWT helpers (python-jose)
  - requirements.txt — Python dependencies
- Frontend (static HTML/JS):
  - index.html — Landing/images with links to booking
  - cardlogin.html — Login/registration page with JWT persistence in localStorage
  - booking.html — Main booking UI for users and admins (calendar, price calc, submit, admin view)
  - monitor.html — Admin monitor (rate + calendar + list of bookings)
  - backup/, style/ — Additional/legacy HTML variants

Entry points and configuration:
- FastAPI app starts from main.py; DB tables are created at import via Base.metadata.create_all(bind=engine)
- Environment variables via .env expected; currently DATABASE_URL is hardcoded in database.py
- CORS is enabled for all origins in development; restrict for production

## 3. Test Strategy
Framework: pytest + httpx (for ASGI tests) + SQLAlchemy testing utils.

Organization:
- tests/ unit, integration split:
  - tests/unit/test_auth.py — hashing and token helpers
  - tests/unit/test_overlap.py — booking overlap predicate
  - tests/integration/test_bookings.py — API happy-path and conflict cases
  - tests/integration/test_rate.py — admin rate set/get

Guidelines:
- Use a dedicated test database (ephemeral) or SQLite-in-memory for unit tests where feasible. For integration tests, spin up a disposable Postgres instance or use a separate schema.
- Provide a Session override fixture to inject a transactional Session per test; rollback after each test.
- Mock time for deterministic date handling; test boundary conditions (adjacent bookings, same start/end, cross-midnight, TZ offsets).
- Do not rely on client-computed values (e.g., payment_value) in assertions; compute on server for verification.
- Target ~80% coverage on core modules (auth, models, booking rules).

## 4. Code Style
Python (backend):
- Use type hints; prefer Python 3.10+ union syntax (str | None)
- Pydantic models: Request schema names end with Create/Update; response schemas end with Out
- SQLAlchemy models are PascalCase; columns snake_case
- Datetimes are timezone-aware UTC; normalize incoming datetimes and persist in UTC. Avoid naive datetimes
- Monetary values: use Decimal in code and Numeric(12,2) at DB; avoid float arithmetic
- Errors: raise HTTPException with precise status codes and user-friendly detail; never leak secrets or stack traces
- Logging: use Python logging (INFO for normal ops, WARNING/ERROR for errors); avoid print; disable engine echo in production

JavaScript (frontend):
- Keep DOM IDs lowerCamelCase; function names lowerCamelCase
- Avoid inline style attributes when possible; prefer CSS classes
- Keep API_BASE in a single place; read from env-config in production builds
- Avoid trusting client-side totals; server must recompute price
- Always handle network errors and non-2xx status separately; provide user-facing messages

## 5. Common Patterns
Backend:
- Dependency injection via FastAPI Depends for DB sessions and auth
- JWT-based auth; admin determined by claim adm (current code infers admin from email prefix on login)
- Overlap check uses half-open interval logic: existing.start < new.end AND existing.end > new.start
- Response models (response_model=...) ensure output shape; orm_mode enabled for SQLAlchemy objects

Frontend:
- Calendar rendering generates a booked date set and marks past/booked days; user selects a range; price computed as nights * nightlyRate
- LocalStorage used for access_token, user_email, user_is_admin
- Simple fetch with Bearer token for protected endpoints

## 6. Do's and Don'ts
Do:
- Load configuration from environment variables
  - DATABASE_URL
  - SECRET_KEY
  - ACCESS_TOKEN_EXPIRE_MINUTES (optional)
  - CORS_ORIGINS (comma-separated) for production
- Use Alembic for schema migrations rather than Base.metadata.create_all in app startup
- Validate and normalize datetime inputs to UTC
- Recalculate pricing server-side; do not trust client-submitted payment_value
- Restrict CORS in production; set allow_origins to trusted domains
- Implement role-based authorization in DB (e.g., users.role or users.is_admin) instead of email prefix heuristic
- Add indexes for frequent queries (e.g., bookings date range, users.email)
- Handle overlapping/adjacent bookings consistently; define whether end_date is exclusive
- Write unit tests for auth, bookings, and rate endpoints

Don't:
- Do not hardcode secrets or database URLs in source (auth.py SECRET_KEY, database.py DATABASE_URL)
- Do not expose echo SQL logs in production
- Do not rely on client for business-critical values (price, role)
- Do not leave dead/unused code paths; remove or fix legacy helpers in database.py

## 7. Tools & Dependencies
Key libraries:
- fastapi — Web framework
- uvicorn — ASGI server
- sqlalchemy — ORM
- psycopg2-binary — Postgres driver
- python-dotenv — .env loader
- passlib[bcrypt] — password hashing
- python-jose — JWT
- tailwindcss (CDN) — frontend styling

Setup:
- Python 3.10+
- Create a .env file with:
  - DATABASE_URL=postgresql+psycopg2://user:pass@host/dbname?sslmode=require
  - SECRET_KEY=your-strong-secret
  - CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5500

Install & run API:
- pip install -r requirements.txt
- uvicorn main:app --reload

Open frontend:
- Open booking.html or index.html in a static file server (e.g., VSCode Live Server) to avoid CORS/file:// quirks

## 8. Other Notes
- Frontend references GET /public-bookings when not admin; backend currently does not provide this route. Add a public read-only endpoint or adjust frontend to use a suitable endpoint
- auth.py SECRET_KEY must be provided via environment; remove placeholder
- database.py currently hardcodes DATABASE_URL and contains legacy helper functions referencing undefined symbols (select, insert, users). Remove or fix these to avoid confusion
- Consider centralizing settings (e.g., a settings.py using pydantic BaseSettings)
- Define clear booking semantics:
  - Persist UTC datetimes; in UI, present local time with check-in/out times (e.g., 14:00 check-in, 12:00 check-out)
  - Clarify whether end_date is exclusive on server; align frontend day-range visualization to avoid off-by-one
- Add structured logging and request/response logging middleware (sanitize sensitive headers)
- Consider rate history and effective-dated pricing if future changes are required
- For LLM-generated code in this repo:
  - Prefer FastAPI dependency patterns already in use
  - Keep SQLAlchemy ORM with session per-request
  - Use Pydantic models with orm_mode for responses
  - Mirror naming conventions (snake_case for columns; PascalCase models; SchemaCreate/SchemaOut)
  - Avoid introducing new frameworks unless necessary