"""Seed the database with sample data.

Usage:
    flask seed          # via CLI command registered in create_app
    python seed.py      # standalone script
"""
from __future__ import annotations

import sys

from app import create_app
from app.extensions import db
from app.models import Item, User


SAMPLE_USERS = [
    {
        "email": "admin@example.com",
        "password": "admin1234",
        "full_name": "Admin User",
        "role": "admin",
    },
    {
        "email": "alice@example.com",
        "password": "alice1234",
        "full_name": "Alice Johnson",
        "role": "user",
    },
    {
        "email": "bob@example.com",
        "password": "bob12345",
        "full_name": "Bob Smith",
        "role": "user",
    },
]

SAMPLE_ITEMS = [
    {
        "name": "Wireless Keyboard",
        "description": "Ergonomic wireless keyboard with backlit keys",
        "price": 79.99,
        "quantity": 150,
        "category": "electronics",
        "status": "active",
    },
    {
        "name": "USB-C Hub",
        "description": "7-in-1 USB-C hub with HDMI, SD card reader, and USB 3.0 ports",
        "price": 49.99,
        "quantity": 200,
        "category": "electronics",
        "status": "active",
    },
    {
        "name": "Cotton T-Shirt",
        "description": "100% organic cotton crew-neck t-shirt",
        "price": 24.99,
        "quantity": 500,
        "category": "clothing",
        "status": "active",
    },
    {
        "name": "Running Shoes",
        "description": "Lightweight trail running shoes with cushioned sole",
        "price": 129.99,
        "quantity": 75,
        "category": "clothing",
        "status": "active",
    },
    {
        "name": "Python Cookbook",
        "description": "Recipes for mastering Python 3.13",
        "price": 39.99,
        "quantity": 60,
        "category": "books",
        "status": "active",
    },
    {
        "name": "Organic Green Tea",
        "description": "Premium loose-leaf green tea, 200g tin",
        "price": 14.99,
        "quantity": 300,
        "category": "food",
        "status": "active",
    },
    {
        "name": "Vintage Desk Lamp",
        "description": "Brass desk lamp with adjustable arm (discontinued model)",
        "price": 89.99,
        "quantity": 0,
        "category": "general",
        "status": "discontinued",
        "is_available": False,
    },
    {
        "name": "Noise-Cancelling Headphones",
        "description": "Over-ear ANC headphones with 30h battery life",
        "price": 249.99,
        "quantity": 40,
        "category": "electronics",
        "status": "active",
    },
]


def seed(verbose: bool = True) -> None:
    """Insert sample users and items into the database."""
    # --- Users ---
    created_users: list[User] = []
    for data in SAMPLE_USERS:
        existing = db.session.execute(
            db.select(User).where(User.email == data["email"])
        ).scalar_one_or_none()
        if existing:
            if verbose:
                print(f"  User already exists: {data['email']}")
            created_users.append(existing)
            continue

        user = User(
            email=data["email"],
            full_name=data["full_name"],
            role=data["role"],
        )
        user.set_password(data["password"])
        db.session.add(user)
        created_users.append(user)
        if verbose:
            print(f"  Created user: {data['email']}")

    db.session.flush()  # assign IDs

    # --- Items (owned by alice) ---
    owner = next((u for u in created_users if u.email == "alice@example.com"), created_users[0])
    for data in SAMPLE_ITEMS:
        existing = db.session.execute(
            db.select(Item).where(Item.name == data["name"])
        ).scalar_one_or_none()
        if existing:
            if verbose:
                print(f"  Item already exists: {data['name']}")
            continue

        item = Item(**data, created_by=owner.id)
        db.session.add(item)
        if verbose:
            print(f"  Created item: {data['name']}")

    db.session.commit()
    if verbose:
        print(f"\nSeed complete: {len(SAMPLE_USERS)} users, {len(SAMPLE_ITEMS)} items.")


def main() -> None:
    config = "config.DevelopmentConfig"
    if len(sys.argv) > 1:
        config = sys.argv[1]

    app = create_app(config)
    with app.app_context():
        db.create_all()
        print("Seeding database...")
        seed()


if __name__ == "__main__":
    main()
