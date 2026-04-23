"""REST API routes for the Flask REST API blueprint."""
from flask import Blueprint, abort, jsonify, request

from ..extensions import db
from ..models import Item
from ..schemas import item_schema, items_schema

api_bp = Blueprint("api", __name__)


@api_bp.get("/items")
def list_items():
    """Return all items."""
    items = db.session.execute(db.select(Item).order_by(Item.created_at.desc())).scalars().all()
    return jsonify(items_schema.dump(items))


@api_bp.post("/items")
def create_item():
    """Create a new item."""
    payload = item_schema.load(request.get_json(force=True))
    item = Item(**payload)
    db.session.add(item)
    db.session.commit()
    return jsonify(item_schema.dump(item)), 201


@api_bp.get("/items/<int:item_id>")
def get_item(item_id: int):
    """Return a single item by ID."""
    item = db.session.get(Item, item_id)
    if item is None:
        abort(404, description=f"Item {item_id} not found")
    return jsonify(item_schema.dump(item))


@api_bp.put("/items/<int:item_id>")
def update_item(item_id: int):
    """Replace an item's data."""
    item = db.session.get(Item, item_id)
    if item is None:
        abort(404, description=f"Item {item_id} not found")
    payload = item_schema.load(request.get_json(force=True))
    for key, value in payload.items():
        setattr(item, key, value)
    db.session.commit()
    return jsonify(item_schema.dump(item))


@api_bp.delete("/items/<int:item_id>")
def delete_item(item_id: int):
    """Delete an item."""
    item = db.session.get(Item, item_id)
    if item is None:
        abort(404, description=f"Item {item_id} not found")
    db.session.delete(item)
    db.session.commit()
    return "", 204


@api_bp.errorhandler(404)
def not_found(err):
    return jsonify({"error": str(err)}), 404


@api_bp.errorhandler(400)
def bad_request(err):
    return jsonify({"error": str(err)}), 400
