"""Tests for request schema validation."""

import pytest
from marshmallow import ValidationError

from app.schemas import item_schema, user_schema


def test_item_schema_rejects_blank_name():
    with pytest.raises(ValidationError):
        item_schema.load({"name": "   ", "price": 1.0})


def test_user_schema_rejects_blank_full_name():
    with pytest.raises(ValidationError):
        user_schema.load(
            {
                "email": "user@example.com",
                "password": "password123",
                "full_name": "   ",
            }
        )
