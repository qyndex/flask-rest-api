# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flask REST API — Minimal Flask 3 REST API using the `create_app` factory pattern, SQLAlchemy 2 models with `Mapped`/`mapped_column` typed columns, marshmallow schemas for validation and serialisation, Alembic migrations, and Blueprint-based routing.

Stack: Flask 3.x, Python 3.13, SQLAlchemy 2, marshmallow 3, psycopg2-binary (PostgreSQL), gunicorn.

## Environment Setup

```bash
cp .env.example .env          # Fill in SECRET_KEY and DATABASE_URL
pip install -r requirements.txt
```

## Commands

```bash
# Development server
FLASK_APP=wsgi.py FLASK_ENV=development flask run --reload   # http://localhost:5000

# Production (gunicorn)
gunicorn wsgi:app -w 4 -b 0.0.0.0:8000

# Database migrations (Alembic via Flask-Migrate)
flask db init                 # Only once — creates migrations/ folder
flask db migrate -m "message" # Auto-generate migration from model changes
flask db upgrade              # Apply pending migrations
flask db downgrade            # Roll back one revision

# Testing
python -m pytest              # Run all tests (verbose, short tracebacks per pytest.ini)
python -m pytest tests/test_routes.py -v    # Routes only
python -m pytest tests/test_models.py -v    # Models only
python -m pytest --cov=app --cov-report=term-missing  # Coverage (needs pytest-cov)

# Linting / formatting
ruff check .                  # Lint (pyproject.toml / ruff.toml config)
ruff format .                 # Auto-format
mypy app/                     # Type-check (mypy.ini config)
```

## Architecture

```
.
├── wsgi.py                   # Gunicorn / Flask dev-server entry point
├── config.py                 # DevelopmentConfig / TestingConfig / ProductionConfig
├── conftest.py               # pytest fixtures: app, db, client
├── .env.example              # Required environment variables
├── app/
│   ├── __init__.py           # create_app() factory — wires extensions + blueprints
│   ├── extensions.py         # db (SQLAlchemy), ma (Marshmallow), migrate singletons
│   ├── models.py             # SQLAlchemy ORM models (Item)
│   ├── schemas.py            # marshmallow schemas (ItemSchema) for validation + serialisation
│   └── api/
│       ├── __init__.py
│       └── routes.py         # Blueprint api_bp, registered at /api prefix
├── tests/
│   ├── test_routes.py        # HTTP-level tests via Flask test client
│   └── test_models.py        # ORM model unit tests
└── supabase/migrations/      # Alembic migration scripts
```

### Key design decisions

- **Application factory** (`create_app`): accepts a config dotted-path string; enables multiple configs per process (testing uses `config.TestingConfig` with in-memory SQLite).
- **Extension singletons** (`extensions.py`): `db`, `ma`, `migrate` are created without an app, then bound via `init_app()` — the standard Flask pattern for avoiding circular imports.
- **Blueprint `api_bp`** mounted at `/api`; all item routes live under `/api/items`.
- **marshmallow schemas** handle both deserialization (request validation via `schema.load()`) and serialization (response via `schema.dump()`). Validation errors raise `422 Unprocessable Entity`.
- **SQLAlchemy 2 typed columns** via `Mapped[T]` / `mapped_column()` — enables mypy strict-mode checking on models.

## Response Shape

All list endpoints return a plain JSON array (no envelope), matching the marshmallow `many=True` dump output:

```json
GET /api/items → [{"id": 1, "name": "Widget", ...}, ...]
POST /api/items → {"id": 2, "name": "Gadget", ...}  (201)
DELETE /api/items/1 → (empty body, 204)
```

Error responses use `{"error": "<description>"}`.

## Rules

- Use Flask Blueprints for all route organisation — no routes in `app/__init__.py`
- SQLAlchemy ORM for all database access — no raw SQL strings
- marshmallow schemas for request validation (`schema.load()`) and response serialisation (`schema.dump()`)
- Environment variables for all configuration — never hardcode secrets or database URLs
- `config.TestingConfig` (in-memory SQLite) for all tests — no external DB required
- Error handlers registered on the blueprint for 404 and 400; marshmallow raises 422 automatically
- `ruff` for linting and formatting; `mypy` with `mypy.ini` for type checking
- 80%+ test coverage required on new routes and models
