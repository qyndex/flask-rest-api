"""Unit tests for SQLAlchemy models.

All tests run inside a rolled-back transaction (via the ``db`` fixture) so
the database is always clean.
"""
from datetime import timezone

import pytest

from app.models import Item


# ---------------------------------------------------------------------------
# Item model — persistence
# ---------------------------------------------------------------------------


class TestItemModel:
    def test_create_item_with_required_fields(self, db):
        item = Item(name="Test Item", price=5.0)
        db.session.add(item)
        db.session.flush()  # assigns id without committing
        assert item.id is not None

    def test_item_repr(self, db):
        item = Item(name="Repr Item", price=1.0)
        db.session.add(item)
        db.session.flush()
        assert "Repr Item" in repr(item)
        assert str(item.id) in repr(item)

    def test_default_description_is_empty_string(self, db):
        item = Item(name="No Desc", price=2.0)
        db.session.add(item)
        db.session.flush()
        assert item.description == ""

    def test_default_quantity_is_zero(self, db):
        item = Item(name="No Qty", price=3.0)
        db.session.add(item)
        db.session.flush()
        assert item.quantity == 0

    def test_default_is_available_is_true(self, db):
        item = Item(name="Available", price=4.0)
        db.session.add(item)
        db.session.flush()
        assert item.is_available is True

    def test_created_at_set_on_insert(self, db):
        item = Item(name="Timestamped", price=1.0)
        db.session.add(item)
        db.session.flush()
        assert item.created_at is not None

    def test_updated_at_set_on_insert(self, db):
        item = Item(name="Timestamped", price=1.0)
        db.session.add(item)
        db.session.flush()
        assert item.updated_at is not None

    def test_created_at_is_timezone_aware(self, db):
        item = Item(name="TZ check", price=1.0)
        db.session.add(item)
        db.session.flush()
        assert item.created_at.tzinfo is not None

    def test_explicit_fields_persisted(self, db):
        item = Item(
            name="Full Item",
            description="Detailed description",
            price=12.50,
            quantity=5,
            is_available=False,
        )
        db.session.add(item)
        db.session.flush()

        fetched = db.session.get(Item, item.id)
        assert fetched.name == "Full Item"
        assert fetched.description == "Detailed description"
        assert fetched.price == 12.50
        assert fetched.quantity == 5
        assert fetched.is_available is False

    def test_item_can_be_deleted(self, db):
        item = Item(name="To Delete", price=1.0)
        db.session.add(item)
        db.session.flush()
        item_id = item.id

        db.session.delete(item)
        db.session.flush()
        assert db.session.get(Item, item_id) is None

    def test_multiple_items_independent(self, db):
        a = Item(name="A", price=1.0)
        b = Item(name="B", price=2.0)
        db.session.add_all([a, b])
        db.session.flush()
        assert a.id != b.id


# ---------------------------------------------------------------------------
# Item model — field constraints
# ---------------------------------------------------------------------------


class TestItemFieldConstraints:
    def test_name_max_length_boundary(self, db):
        """Name at the 200-char boundary should persist without error."""
        item = Item(name="x" * 200, price=1.0)
        db.session.add(item)
        db.session.flush()
        assert len(item.name) == 200

    def test_price_stored_as_float(self, db):
        item = Item(name="Float price", price=3.14)
        db.session.add(item)
        db.session.flush()
        assert isinstance(item.price, float)
