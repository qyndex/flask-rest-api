"""Marshmallow schemas for the Flask REST API."""
from marshmallow import Schema, fields, validate


class UserSchema(Schema):
    """Schema for serialising/deserialising User objects."""

    id = fields.Int(dump_only=True)
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=8, max=128))
    full_name = fields.Str(load_default="", validate=validate.Length(max=200))
    role = fields.Str(dump_only=True)
    is_active = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class LoginSchema(Schema):
    """Schema for login requests."""

    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=1))


class ItemSchema(Schema):
    """Schema for serialising/deserialising Item objects."""

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str(load_default="")
    price = fields.Float(required=True, validate=validate.Range(min=0))
    quantity = fields.Int(load_default=0, validate=validate.Range(min=0))
    category = fields.Str(
        load_default="general",
        validate=validate.OneOf(
            ["general", "electronics", "clothing", "food", "books", "other"]
        ),
    )
    status = fields.Str(
        load_default="active",
        validate=validate.OneOf(["active", "inactive", "discontinued"]),
    )
    is_available = fields.Bool(load_default=True)
    created_by = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


item_schema = ItemSchema()
items_schema = ItemSchema(many=True)
user_schema = UserSchema()
login_schema = LoginSchema()
