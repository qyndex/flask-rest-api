# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flask REST API — Minimal Flask 3 REST API using the create_app factory, SQLAlchemy 2 models, marshmallow schemas, Alembic migrations, and Blueprint-based routing.

Built with Flask 3.x, Python 3.13, and SQLAlchemy.

## Commands

```bash
pip install -r requirements.txt          # Install dependencies
flask run --reload                       # Start dev server (http://localhost:5000)
python -m pytest                         # Run tests
ruff check .                             # Lint
ruff format .                            # Format
```

## Architecture

- `app.py` or `wsgi.py` — Flask application entry point
- `models/` — SQLAlchemy models
- `routes/` or `views/` — Route handlers (Blueprints)
- `templates/` — Jinja2 templates
- `static/` — Static assets
- `tests/` — Test files

## Rules

- Use Flask Blueprints for route organization
- SQLAlchemy for all database access — no raw SQL
- Environment variables for all configuration (never hardcode secrets)
- Error handlers for 404, 500, and validation errors
