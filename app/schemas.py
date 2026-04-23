"""Marshmallow schemas for the Flask REST API."""
from marshmallow import Schema, fields, validate


class ItemSchema(Schema):
    """Schema for serialising/deserialising Item objects."""

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str(load_default="")
    price = fields.Float(required=True, validate=validate.Range(min=0))
    quantity = fields.Int(load_default=0, validate=validate.Range(min=0))
    is_available = fields.Bool(load_default=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


item_schema = ItemSchema()
items_schema = ItemSchema(many=True)
