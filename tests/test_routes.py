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
    "is_available": True,
}


def _create_item(client, payload=None):
    """POST a single item and return the response."""
    return client.post(
        "/api/items",
        data=json.dumps(payload or ITEM_PAYLOAD),
        content_type="application/json",
    )


# ---------------------------------------------------------------------------
# GET /api/items
# ---------------------------------------------------------------------------


class TestListItems:
    def test_returns_empty_list_when_no_items(self, client):
        res = client.get("/api/items")
        assert res.status_code == 200
        data = res.get_json()
        assert isinstance(data, list)
        assert data == []

    def test_returns_all_items(self, client):
        _create_item(client)
        _create_item(client, {**ITEM_PAYLOAD, "name": "Gadget", "price": 4.99})
        res = client.get("/api/items")
        assert res.status_code == 200
        data = res.get_json()
        assert len(data) == 2

    def test_items_ordered_newest_first(self, client):
        _create_item(client, {**ITEM_PAYLOAD, "name": "First"})
        _create_item(client, {**ITEM_PAYLOAD, "name": "Second"})
        data = client.get("/api/items").get_json()
        # Most recently created item appears first
        assert data[0]["name"] == "Second"


# ---------------------------------------------------------------------------
# POST /api/items
# ---------------------------------------------------------------------------


class TestCreateItem:
    def test_creates_item_returns_201(self, client):
        res = _create_item(client)
        assert res.status_code == 201

    def test_response_contains_assigned_id(self, client):
        data = _create_item(client).get_json()
        assert "id" in data
        assert isinstance(data["id"], int)

    def test_response_reflects_payload(self, client):
        data = _create_item(client).get_json()
        assert data["name"] == ITEM_PAYLOAD["name"]
        assert data["price"] == ITEM_PAYLOAD["price"]
        assert data["quantity"] == ITEM_PAYLOAD["quantity"]
        assert data["is_available"] == ITEM_PAYLOAD["is_available"]

    def test_response_includes_timestamps(self, client):
        data = _create_item(client).get_json()
        assert data["created_at"] is not None
        assert data["updated_at"] is not None

    def test_missing_required_name_returns_422(self, client):
        payload = {k: v for k, v in ITEM_PAYLOAD.items() if k != "name"}
        res = _create_item(client, payload)
        assert res.status_code == 422

    def test_missing_required_price_returns_422(self, client):
        payload = {k: v for k, v in ITEM_PAYLOAD.items() if k != "price"}
        res = _create_item(client, payload)
        assert res.status_code == 422

    def test_negative_price_returns_422(self, client):
        res = _create_item(client, {**ITEM_PAYLOAD, "price": -1.0})
        assert res.status_code == 422

    def test_negative_quantity_returns_422(self, client):
        res = _create_item(client, {**ITEM_PAYLOAD, "quantity": -5})
        assert res.status_code == 422

    def test_optional_fields_use_defaults(self, client):
        minimal = {"name": "Minimal", "price": 1.0}
        data = _create_item(client, minimal).get_json()
        assert data["description"] == ""
        assert data["quantity"] == 0
        assert data["is_available"] is True


# ---------------------------------------------------------------------------
# GET /api/items/<id>
# ---------------------------------------------------------------------------


class TestGetItem:
    def test_returns_existing_item(self, client):
        created = _create_item(client).get_json()
        res = client.get(f"/api/items/{created['id']}")
        assert res.status_code == 200
        data = res.get_json()
        assert data["id"] == created["id"]
        assert data["name"] == created["name"]

    def test_returns_404_for_missing_item(self, client):
        res = client.get("/api/items/999999")
        assert res.status_code == 404

    def test_404_response_contains_error_key(self, client):
        data = client.get("/api/items/999999").get_json()
        assert "error" in data


# ---------------------------------------------------------------------------
# PUT /api/items/<id>
# ---------------------------------------------------------------------------


class TestUpdateItem:
    def test_updates_item_fields(self, client):
        item_id = _create_item(client).get_json()["id"]
        updated_payload = {**ITEM_PAYLOAD, "name": "Updated Widget", "price": 19.99}
        res = client.put(
            f"/api/items/{item_id}",
            data=json.dumps(updated_payload),
            content_type="application/json",
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data["name"] == "Updated Widget"
        assert data["price"] == 19.99

    def test_returns_404_when_item_not_found(self, client):
        res = client.put(
            "/api/items/999999",
            data=json.dumps(ITEM_PAYLOAD),
            content_type="application/json",
        )
        assert res.status_code == 404

    def test_invalid_update_payload_returns_422(self, client):
        item_id = _create_item(client).get_json()["id"]
        res = client.put(
            f"/api/items/{item_id}",
            data=json.dumps({**ITEM_PAYLOAD, "price": -5.0}),
            content_type="application/json",
        )
        assert res.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /api/items/<id>
# ---------------------------------------------------------------------------


class TestDeleteItem:
    def test_deletes_item_returns_204(self, client):
        item_id = _create_item(client).get_json()["id"]
        res = client.delete(f"/api/items/{item_id}")
        assert res.status_code == 204
        assert res.data == b""

    def test_item_no_longer_accessible_after_delete(self, client):
        item_id = _create_item(client).get_json()["id"]
        client.delete(f"/api/items/{item_id}")
        res = client.get(f"/api/items/{item_id}")
        assert res.status_code == 404

    def test_delete_nonexistent_item_returns_404(self, client):
        res = client.delete("/api/items/999999")
        assert res.status_code == 404
