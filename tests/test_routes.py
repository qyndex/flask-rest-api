"""Tests for /api/items REST endpoints.

Uses the ``client`` fixture from conftest.py which wraps each test in a
rolled-back database transaction — no cleanup needed.
"""
import json

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ITEM_PAYLOAD = {
    "name": "Widget",
    "description": "A useful widget",
    "price": 9.99,
    "quantity": 10,
    "category": "electronics",
    "status": "active",
    "is_available": True,
}


def _create_item(client, payload=None, headers=None):
    """POST a single item and return the response."""
    return client.post(
        "/api/items",
        data=json.dumps(payload or ITEM_PAYLOAD),
        content_type="application/json",
        headers=headers or {},
    )


# ---------------------------------------------------------------------------
# GET /api/items  (public — jwt_optional)
# ---------------------------------------------------------------------------


class TestListItems:
    def test_returns_empty_list_when_no_items(self, client):
        res = client.get("/api/items")
        assert res.status_code == 200
        data = res.get_json()
        assert "items" in data
        assert data["items"] == []
        assert "meta" in data

    def test_returns_all_items(self, client, auth_headers):
        _create_item(client, headers=auth_headers)
        _create_item(
            client,
            {**ITEM_PAYLOAD, "name": "Gadget", "price": 4.99},
            headers=auth_headers,
        )
        res = client.get("/api/items")
        assert res.status_code == 200
        data = res.get_json()
        assert len(data["items"]) == 2

    def test_items_ordered_newest_first(self, client, auth_headers):
        _create_item(
            client, {**ITEM_PAYLOAD, "name": "First"}, headers=auth_headers
        )
        _create_item(
            client, {**ITEM_PAYLOAD, "name": "Second"}, headers=auth_headers
        )
        data = client.get("/api/items").get_json()
        assert data["items"][0]["name"] == "Second"

    def test_pagination_meta_present(self, client):
        res = client.get("/api/items")
        meta = res.get_json()["meta"]
        assert "page" in meta
        assert "per_page" in meta
        assert "total" in meta
        assert "pages" in meta

    def test_filter_by_category(self, client, auth_headers):
        _create_item(
            client,
            {**ITEM_PAYLOAD, "name": "Elec", "category": "electronics"},
            headers=auth_headers,
        )
        _create_item(
            client,
            {**ITEM_PAYLOAD, "name": "Book", "category": "books"},
            headers=auth_headers,
        )
        res = client.get("/api/items?category=books")
        items = res.get_json()["items"]
        assert len(items) == 1
        assert items[0]["name"] == "Book"

    def test_filter_by_price_range(self, client, auth_headers):
        _create_item(
            client,
            {**ITEM_PAYLOAD, "name": "Cheap", "price": 5.0},
            headers=auth_headers,
        )
        _create_item(
            client,
            {**ITEM_PAYLOAD, "name": "Pricey", "price": 100.0},
            headers=auth_headers,
        )
        res = client.get("/api/items?min_price=50&max_price=200")
        items = res.get_json()["items"]
        assert len(items) == 1
        assert items[0]["name"] == "Pricey"


# ---------------------------------------------------------------------------
# POST /api/items  (requires auth)
# ---------------------------------------------------------------------------


class TestCreateItem:
    def test_unauthenticated_returns_401(self, client):
        res = _create_item(client)
        assert res.status_code == 401

    def test_creates_item_returns_201(self, client, auth_headers):
        res = _create_item(client, headers=auth_headers)
        assert res.status_code == 201

    def test_response_contains_assigned_id(self, client, auth_headers):
        data = _create_item(client, headers=auth_headers).get_json()
        assert "item" in data
        assert "id" in data["item"]
        assert isinstance(data["item"]["id"], int)

    def test_response_reflects_payload(self, client, auth_headers):
        data = _create_item(client, headers=auth_headers).get_json()["item"]
        assert data["name"] == ITEM_PAYLOAD["name"]
        assert data["price"] == ITEM_PAYLOAD["price"]
        assert data["quantity"] == ITEM_PAYLOAD["quantity"]
        assert data["is_available"] == ITEM_PAYLOAD["is_available"]

    def test_response_includes_timestamps(self, client, auth_headers):
        data = _create_item(client, headers=auth_headers).get_json()["item"]
        assert data["created_at"] is not None
        assert data["updated_at"] is not None

    def test_created_by_set_to_current_user(self, client, auth_headers, test_user):
        data = _create_item(client, headers=auth_headers).get_json()["item"]
        assert data["created_by"] == test_user.id

    def test_missing_required_name_returns_422(self, client, auth_headers):
        payload = {k: v for k, v in ITEM_PAYLOAD.items() if k != "name"}
        res = _create_item(client, payload, headers=auth_headers)
        assert res.status_code == 422

    def test_missing_required_price_returns_422(self, client, auth_headers):
        payload = {k: v for k, v in ITEM_PAYLOAD.items() if k != "price"}
        res = _create_item(client, payload, headers=auth_headers)
        assert res.status_code == 422

    def test_negative_price_returns_422(self, client, auth_headers):
        res = _create_item(
            client, {**ITEM_PAYLOAD, "price": -1.0}, headers=auth_headers
        )
        assert res.status_code == 422

    def test_negative_quantity_returns_422(self, client, auth_headers):
        res = _create_item(
            client, {**ITEM_PAYLOAD, "quantity": -5}, headers=auth_headers
        )
        assert res.status_code == 422

    def test_invalid_category_returns_422(self, client, auth_headers):
        res = _create_item(
            client, {**ITEM_PAYLOAD, "category": "invalid"}, headers=auth_headers
        )
        assert res.status_code == 422

    def test_optional_fields_use_defaults(self, client, auth_headers):
        minimal = {"name": "Minimal", "price": 1.0}
        data = _create_item(client, minimal, headers=auth_headers).get_json()["item"]
        assert data["description"] == ""
        assert data["quantity"] == 0
        assert data["is_available"] is True
        assert data["category"] == "general"
        assert data["status"] == "active"


# ---------------------------------------------------------------------------
# GET /api/items/<id>  (public)
# ---------------------------------------------------------------------------


class TestGetItem:
    def test_returns_existing_item(self, client, auth_headers):
        created = _create_item(client, headers=auth_headers).get_json()["item"]
        res = client.get(f"/api/items/{created['id']}")
        assert res.status_code == 200
        data = res.get_json()["item"]
        assert data["id"] == created["id"]
        assert data["name"] == created["name"]

    def test_returns_404_for_missing_item(self, client):
        res = client.get("/api/items/999999")
        assert res.status_code == 404

    def test_404_response_contains_error_key(self, client):
        data = client.get("/api/items/999999").get_json()
        assert "error" in data


# ---------------------------------------------------------------------------
# PUT /api/items/<id>  (owner only)
# ---------------------------------------------------------------------------


class TestUpdateItem:
    def test_unauthenticated_returns_401(self, client, auth_headers):
        item_id = _create_item(client, headers=auth_headers).get_json()["item"]["id"]
        res = client.put(
            f"/api/items/{item_id}",
            data=json.dumps(ITEM_PAYLOAD),
            content_type="application/json",
        )
        assert res.status_code == 401

    def test_updates_item_fields(self, client, auth_headers):
        item_id = _create_item(client, headers=auth_headers).get_json()["item"]["id"]
        updated_payload = {**ITEM_PAYLOAD, "name": "Updated Widget", "price": 19.99}
        res = client.put(
            f"/api/items/{item_id}",
            data=json.dumps(updated_payload),
            content_type="application/json",
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.get_json()["item"]
        assert data["name"] == "Updated Widget"
        assert data["price"] == 19.99

    def test_returns_404_when_item_not_found(self, client, auth_headers):
        res = client.put(
            "/api/items/999999",
            data=json.dumps(ITEM_PAYLOAD),
            content_type="application/json",
            headers=auth_headers,
        )
        assert res.status_code == 404

    def test_invalid_update_payload_returns_422(self, client, auth_headers):
        item_id = _create_item(client, headers=auth_headers).get_json()["item"]["id"]
        res = client.put(
            f"/api/items/{item_id}",
            data=json.dumps({**ITEM_PAYLOAD, "price": -5.0}),
            content_type="application/json",
            headers=auth_headers,
        )
        assert res.status_code == 422

    def test_non_owner_cannot_update(self, client, app, db, auth_headers):
        """Another user cannot update an item they don't own."""
        # Create item as test_user
        item_id = _create_item(client, headers=auth_headers).get_json()["item"]["id"]

        # Create a second user and get their token
        from app.auth import create_access_token
        from app.models import User

        other = User(email="other@test.com", full_name="Other")
        other.set_password("otherpass1")
        db.session.add(other)
        db.session.flush()
        with app.app_context():
            other_token = create_access_token(other)
        other_headers = {
            "Authorization": f"Bearer {other_token}",
            "Content-Type": "application/json",
        }

        res = client.put(
            f"/api/items/{item_id}",
            data=json.dumps(ITEM_PAYLOAD),
            headers=other_headers,
        )
        assert res.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /api/items/<id>  (owner only)
# ---------------------------------------------------------------------------


class TestDeleteItem:
    def test_unauthenticated_returns_401(self, client, auth_headers):
        item_id = _create_item(client, headers=auth_headers).get_json()["item"]["id"]
        res = client.delete(f"/api/items/{item_id}")
        assert res.status_code == 401

    def test_deletes_item_returns_204(self, client, auth_headers):
        item_id = _create_item(client, headers=auth_headers).get_json()["item"]["id"]
        res = client.delete(f"/api/items/{item_id}", headers=auth_headers)
        assert res.status_code == 204
        assert res.data == b""

    def test_item_no_longer_accessible_after_delete(self, client, auth_headers):
        item_id = _create_item(client, headers=auth_headers).get_json()["item"]["id"]
        client.delete(f"/api/items/{item_id}", headers=auth_headers)
        res = client.get(f"/api/items/{item_id}")
        assert res.status_code == 404

    def test_delete_nonexistent_item_returns_404(self, client, auth_headers):
        res = client.delete("/api/items/999999", headers=auth_headers)
        assert res.status_code == 404

    def test_non_owner_cannot_delete(self, client, app, db, auth_headers):
        """Another user cannot delete an item they don't own."""
        item_id = _create_item(client, headers=auth_headers).get_json()["item"]["id"]

        from app.auth import create_access_token
        from app.models import User

        other = User(email="other2@test.com", full_name="Other")
        other.set_password("otherpass1")
        db.session.add(other)
        db.session.flush()
        with app.app_context():
            other_token = create_access_token(other)
        other_headers = {
            "Authorization": f"Bearer {other_token}",
            "Content-Type": "application/json",
        }

        res = client.delete(f"/api/items/{item_id}", headers=other_headers)
        assert res.status_code == 403
