"""JWT authentication for the Flask REST API.

Uses PyJWT directly for token creation/verification — no heavy framework
dependency.  Tokens are short-lived (default 30 minutes) and carry the user id
and role in the payload.
"""
from __future__ import annotations

import functools
from datetime import datetime, timedelta, timezone

import jwt
from flask import current_app, g, jsonify, request

from .extensions import db
from .models import User


def _get_secret() -> str:
    return current_app.config["SECRET_KEY"]


def create_access_token(user: User, expires_delta: timedelta | None = None) -> str:
    """Return a signed JWT for *user*."""
    now = datetime.now(timezone.utc)
    exp = now + (expires_delta or timedelta(minutes=30))
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "iat": now,
        "exp": exp,
    }
    return jwt.encode(payload, _get_secret(), algorithm="HS256")


def decode_token(token: str) -> dict:
    """Decode and verify a JWT.  Raises ``jwt.InvalidTokenError`` on failure."""
    return jwt.decode(token, _get_secret(), algorithms=["HS256"])


def _get_current_user() -> User | None:
    """Extract the user from the Authorization header, if present."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except jwt.InvalidTokenError:
        return None
    return db.session.get(User, int(payload["sub"]))


def jwt_required(fn):
    """Decorator that enforces a valid JWT on the wrapped view.

    On success the authenticated ``User`` is stored in ``g.current_user``.
    On failure a 401 JSON response is returned.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        user = _get_current_user()
        if user is None:
            return jsonify({"error": "Authentication required"}), 401
        if not user.is_active:
            return jsonify({"error": "Account deactivated"}), 403
        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper


def jwt_optional(fn):
    """Like ``jwt_required`` but allows anonymous access.

    ``g.current_user`` is set to ``None`` when no valid token is provided.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        g.current_user = _get_current_user()
        return fn(*args, **kwargs)

    return wrapper
