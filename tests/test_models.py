"""Unit tests for SQLAlchemy models.

All tests run inside a rolled-back transaction (via the ``db`` fixture) so
the database is always clean.
"""
from datetime import timezone

import pytest

from app.models import Item, User


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------


class TestUserModel:
    def test_create_user_with_required_fields(self, db):
        user = User(email="a@b.com", password_hash="x")
        db.session.add(user)
        db.session.flush()
        assert user.id is not None

    def test_set_and_check_password(self, db):
        user = User(email="pw@test.com")
        user.set_password("secret123")
        db.session.add(user)
        db.session.flush()
        assert user.check_password("secret123") is True
        assert user.check_password("wrong") is False

    def test_default_role_is_user(self, db):
        user = User(email="role@test.com", password_hash="x")
        db.session.add(user)
        db.session.flush()
        assert user.role == "user"

    def test_default_is_active(self, db):
        user = User(email="active@test.com", password_hash="x")
        db.session.add(user)
        db.session.flush()
        assert user.is_active is True

    def test_user_repr(self, db):
        user = User(email="repr@test.com", password_hash="x")
        db.session.add(user)
        db.session.flush()
        assert "repr@test.com" in repr(user)

    def test_email_unique_constraint(self, db):
        u1 = User(email="dup@test.com", password_hash="x")
        u2 = User(email="dup@test.com", password_hash="y")
        db.session.add(u1)
        db.session.flush()
        db.session.add(u2)
        with pytest.raises(Exception):  # IntegrityError
            db.session.flush()


# ---------------------------------------------------------------------------
# Item model — persistence
# ---------------------------------------------------------------------------


class TestItemModel:
    def test_create_item_with_required_fields(self, db):
        item = Item(name="Test Item", price=5.0)
        db.session.add(item)
        db.session.flush()
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

    def test_default_category(self, db):
        item = Item(name="Cat", price=1.0)
        db.session.add(item)
        db.session.flush()
        assert item.category == "general"

    def test_default_status(self, db):
        item = Item(name="Stat", price=1.0)
        db.session.add(item)
        db.session.flush()
        assert item.status == "active"

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
            category="electronics",
            status="inactive",
            is_available=False,
        )
        db.session.add(item)
        db.session.flush()

        fetched = db.session.get(Item, item.id)
        assert fetched.name == "Full Item"
        assert fetched.description == "Detailed description"
        assert fetched.price == 12.50
        assert fetched.quantity == 5
        assert fetched.category == "electronics"
        assert fetched.status == "inactive"
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

    def test_item_owner_relationship(self, db):
        user = User(email="owner@test.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()

        item = Item(name="Owned", price=1.0, created_by=user.id)
        db.session.add(item)
        db.session.flush()

        assert item.owner.id == user.id


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
