"""Authentication routes: register and login."""
from flask import Blueprint, jsonify, request

from ..auth import create_access_token, jwt_required
from ..extensions import db
from ..models import User
from ..schemas import login_schema, user_schema

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/auth/register")
def register():
    """Register a new user account.

    Expects JSON: ``{"email": "...", "password": "...", "full_name": "..."}``
    """
    data = user_schema.load(request.get_json(force=True))
    if db.session.execute(
        db.select(User).where(User.email == data["email"])
    ).scalar_one_or_none():
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        email=data["email"],
        full_name=data.get("full_name", ""),
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    token = create_access_token(user)
    return (
        jsonify(
            {
                "user": user_schema.dump(user),
                "access_token": token,
            }
        ),
        201,
    )


@auth_bp.post("/auth/login")
def login():
    """Authenticate and return a JWT.

    Expects JSON: ``{"email": "...", "password": "..."}``
    """
    data = login_schema.load(request.get_json(force=True))
    user = db.session.execute(
        db.select(User).where(User.email == data["email"])
    ).scalar_one_or_none()

    if user is None or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account deactivated"}), 403

    token = create_access_token(user)
    return jsonify(
        {
            "user": user_schema.dump(user),
            "access_token": token,
        }
    )


@auth_bp.get("/auth/me")
@jwt_required
def me():
    """Return the currently authenticated user."""
    from flask import g

    return jsonify({"user": user_schema.dump(g.current_user)})
