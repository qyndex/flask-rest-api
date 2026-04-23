# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flask REST API -- Production-ready Flask 3 REST API using the `create_app` factory pattern, SQLAlchemy 2 models with `Mapped`/`mapped_column` typed columns, JWT authentication, marshmallow schemas for validation and serialisation, Alembic migrations, CORS, rate limiting, and Blueprint-based routing.

Stack: Flask 3.x, Python 3.13, SQLAlchemy 2, marshmallow 3, PyJWT, psycopg2-binary (PostgreSQL), gunicorn.

## Environment Setup

```bash
cp .env.example .env          # Fill in SECRET_KEY and DATABASE_URL
pip install -r requirements.txt
python seed.py                # Populate sample users and items
```

## Commands

```bash
# Development server
FLASK_APP=wsgi.py FLASK_ENV=development flask run --reload   # http://localhost:5000

# Production (gunicorn)
gunicorn wsgi:app -w 4 -b 0.0.0.0:8000

# Database migrations (Alembic via Flask-Migrate)
flask db migrate -m "message" # Auto-generate migration from model changes
flask db upgrade              # Apply pending migrations
flask db downgrade            # Roll back one revision

# Seed data
python seed.py                # Creates 3 sample users + 8 items
python seed.py config.TestingConfig  # Seed with testing config

# Testing
python -m pytest              # Run all tests (verbose, short tracebacks per pytest.ini)
python -m pytest tests/test_routes.py -v    # Routes only
python -m pytest tests/test_models.py -v    # Models only
python -m pytest tests/test_auth.py -v      # Auth only
python -m pytest --cov=app --cov-report=term-missing  # Coverage (needs pytest-cov)

# Linting / formatting
ruff check .                  # Lint (ruff.toml config)
ruff format .                 # Auto-format
mypy app/                     # Type-check (mypy.ini config)

# Docker
docker compose up --build     # Runs app + PostgreSQL
```

## Architecture

```
.
├── wsgi.py                   # Gunicorn / Flask dev-server entry point
├── config.py                 # Dev / Testing / Production config classes
├── conftest.py               # pytest fixtures: app, db, client, test_user, auth_headers
├── seed.py                   # CLI seed script (3 users, 8 items)
├── alembic.ini               # Alembic configuration (URL injected by Flask-Migrate)
├── .env.example              # Required environment variables
├── app/
│   ├── __init__.py           # create_app() factory — wires extensions, CORS, rate limiter, error handlers
│   ├── extensions.py         # db (SQLAlchemy), ma (Marshmallow), migrate singletons
│   ├── models.py             # SQLAlchemy ORM models (User, Item with FK relationship)
│   ├── schemas.py            # marshmallow schemas (UserSchema, LoginSchema, ItemSchema)
│   ├── auth.py               # JWT token creation/verification, @jwt_required / @jwt_optional decorators
│   └── api/
│       ├── __init__.py
│       ├── routes.py         # Blueprint api_bp — Item CRUD at /api/items with pagination + filtering
│       └── auth_routes.py    # Blueprint auth_bp — POST /auth/register, POST /auth/login, GET /auth/me
├── migrations/               # Alembic migration scripts
│   ├── env.py                # Alembic environment (Flask-Migrate wired)
│   ├── script.py.mako        # Migration template
│   └── versions/
│       └── 001_initial_schema.py  # Users + Items tables
├── supabase/migrations/
│   └── 20240101000000_initial_schema.sql  # Supabase deployment option with RLS policies
└── tests/
    ├── test_auth.py          # Auth endpoints: register, login, /me, health
    ├── test_routes.py        # Item CRUD: list, create, get, update, delete, ownership
    └── test_models.py        # ORM model unit tests: User + Item
```

### Key design decisions

- **Application factory** (`create_app`): accepts a config dotted-path string; enables multiple configs per process (testing uses `config.TestingConfig` with in-memory SQLite).
- **Extension singletons** (`extensions.py`): `db`, `ma`, `migrate` are created without an app, then bound via `init_app()`.
- **JWT authentication** (`auth.py`): PyJWT-based, no heavy framework. `@jwt_required` enforces auth; `@jwt_optional` allows anonymous. Token carries `sub` (user id as string), `email`, `role`.
- **Ownership enforcement**: Items have a `created_by` FK to `users`. Only the owner can update or delete their items (403 for non-owners).
- **Blueprint routing**: `api_bp` mounted at `/api` for items; `auth_bp` at `/api` for auth routes.
- **marshmallow schemas** handle deserialization (request validation via `schema.load()`) and serialization (response via `schema.dump()`). Validation errors raise 422.
- **CORS** via Flask-CORS, configured per `CORS_ORIGINS` env var.
- **Rate limiting** via Flask-Limiter (200/hour, 50/minute default). Disabled in test config.
- **Dual migration paths**: Alembic (via Flask-Migrate) for SQLAlchemy; Supabase SQL migration for hosted Supabase deployment.

## Authentication

All mutating endpoints (POST/PUT/DELETE on items) require a valid JWT in the `Authorization: Bearer <token>` header. Read endpoints (GET) use `@jwt_optional` -- they work without auth but populate `g.current_user` if a token is provided.

```bash
# Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123","full_name":"User"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Use the token
curl http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer <token>"
```

Default test user credentials (from seed.py): `admin@example.com` / `admin1234`.

## Response Shape

All endpoints return JSON objects with named keys (never bare arrays):

```json
GET  /api/items      → {"items": [...], "meta": {"page": 1, "per_page": 20, "total": 8, "pages": 1}}
POST /api/items      → {"item": {...}}  (201)
GET  /api/items/1    → {"item": {...}}
PUT  /api/items/1    → {"item": {...}}
DELETE /api/items/1  → (empty body, 204)
GET  /api/auth/me    → {"user": {...}}
POST /api/auth/login → {"user": {...}, "access_token": "..."}
```

Error responses use `{"error": "<description>"}`, validation errors use `{"error": "Validation failed", "details": {...}}`.

## Item Filtering & Pagination

```
GET /api/items?category=electronics        # filter by category
GET /api/items?status=active               # filter by status
GET /api/items?min_price=10&max_price=50   # price range
GET /api/items?page=2&per_page=10          # pagination (max 100 per page)
```

Valid categories: `general`, `electronics`, `clothing`, `food`, `books`, `other`.
Valid statuses: `active`, `inactive`, `discontinued`.

## Rules

- Use Flask Blueprints for all route organisation -- no routes in `app/__init__.py`
- SQLAlchemy ORM for all database access -- no raw SQL strings
- marshmallow schemas for request validation (`schema.load()`) and response serialisation (`schema.dump()`)
- Environment variables for all configuration -- never hardcode secrets or database URLs
- `config.TestingConfig` (in-memory SQLite) for all tests -- no external DB required
- JWT auth via `@jwt_required` on all mutating endpoints; `@jwt_optional` on read endpoints
- Ownership enforcement: only the item creator can update/delete (checked via `created_by` FK)
- Response envelopes: always `{"key": value}`, never bare arrays
- Error handlers registered on the blueprint for 404, 400, 403; marshmallow raises 422 via app-level handler
- `ruff` for linting and formatting; `mypy` with `mypy.ini` for type checking
- 80%+ test coverage required on new routes and models
- Seed data must be idempotent (skips existing records)
- Alembic migrations use `IF NOT EXISTS` / `server_default` patterns
- Rate limiting defaults: 200/hour, 50/minute (disabled in tests via `RATELIMIT_ENABLED = False`)
