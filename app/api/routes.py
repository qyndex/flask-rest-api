"""REST API routes for the Flask REST API blueprint."""
from flask import Blueprint, abort, g, jsonify, request
from sqlalchemy import and_

from ..auth import jwt_optional, jwt_required
from ..extensions import db
from ..models import Item
from ..schemas import item_schema, items_schema

api_bp = Blueprint("api", __name__)

# --------------------------------------------------------------------------
# Pagination defaults
# --------------------------------------------------------------------------
DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


def _paginate_query(query):
    """Apply page/per_page from query-string and return (items, meta)."""
    page = request.args.get("page", DEFAULT_PAGE, type=int)
    per_page = min(
        request.args.get("per_page", DEFAULT_PER_PAGE, type=int), MAX_PER_PAGE
    )
    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    meta = {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
    }
    return pagination.items, meta


# --------------------------------------------------------------------------
# GET /items  — list with filtering + pagination
# --------------------------------------------------------------------------
@api_bp.get("/items")
@jwt_optional
def list_items():
    """Return paginated items with optional filters.

    Query params:
      - category: filter by category
      - status: filter by status (active/inactive/discontinued)
      - min_price / max_price: price range filter
      - page / per_page: pagination
    """
    query = db.select(Item)

    # --- filters ---
    category = request.args.get("category")
    if category:
        query = query.where(Item.category == category)

    status = request.args.get("status")
    if status:
        query = query.where(Item.status == status)

    min_price = request.args.get("min_price", type=float)
    if min_price is not None:
        query = query.where(Item.price >= min_price)

    max_price = request.args.get("max_price", type=float)
    if max_price is not None:
        query = query.where(Item.price <= max_price)

    query = query.order_by(Item.created_at.desc())

    items, meta = _paginate_query(query)
    return jsonify({"items": items_schema.dump(items), "meta": meta})


# --------------------------------------------------------------------------
# POST /items
# --------------------------------------------------------------------------
@api_bp.post("/items")
@jwt_required
def create_item():
    """Create a new item owned by the authenticated user."""
    payload = item_schema.load(request.get_json(force=True))
    item = Item(**payload, created_by=g.current_user.id)
    db.session.add(item)
    db.session.commit()
    return jsonify({"item": item_schema.dump(item)}), 201


# --------------------------------------------------------------------------
# GET /items/<id>
# --------------------------------------------------------------------------
@api_bp.get("/items/<int:item_id>")
@jwt_optional
def get_item(item_id: int):
    """Return a single item by ID."""
    item = db.session.get(Item, item_id)
    if item is None:
        abort(404, description=f"Item {item_id} not found")
    return jsonify({"item": item_schema.dump(item)})


# --------------------------------------------------------------------------
# PUT /items/<id>
# --------------------------------------------------------------------------
@api_bp.put("/items/<int:item_id>")
@jwt_required
def update_item(item_id: int):
    """Replace an item's data.  Only the owner may update."""
    item = db.session.get(Item, item_id)
    if item is None:
        abort(404, description=f"Item {item_id} not found")
    if item.created_by != g.current_user.id:
        return jsonify({"error": "You can only update your own items"}), 403
    payload = item_schema.load(request.get_json(force=True))
    for key, value in payload.items():
        setattr(item, key, value)
    db.session.commit()
    return jsonify({"item": item_schema.dump(item)})


# --------------------------------------------------------------------------
# DELETE /items/<id>
# --------------------------------------------------------------------------
@api_bp.delete("/items/<int:item_id>")
@jwt_required
def delete_item(item_id: int):
    """Delete an item.  Only the owner may delete."""
    item = db.session.get(Item, item_id)
    if item is None:
        abort(404, description=f"Item {item_id} not found")
    if item.created_by != g.current_user.id:
        return jsonify({"error": "You can only delete your own items"}), 403
    db.session.delete(item)
    db.session.commit()
    return "", 204


# --------------------------------------------------------------------------
# Error handlers (blueprint-scoped)
# --------------------------------------------------------------------------
@api_bp.errorhandler(404)
def not_found(err):
    return jsonify({"error": str(err)}), 404


@api_bp.errorhandler(400)
def bad_request(err):
    return jsonify({"error": str(err)}), 400


@api_bp.errorhandler(403)
def forbidden(err):
    return jsonify({"error": str(err)}), 403
