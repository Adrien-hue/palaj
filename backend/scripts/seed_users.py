from __future__ import annotations

from sqlalchemy.orm import Session

from db import db
from backend.app.security.password import hash_password
from db.models import User


USERS = [
    {
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "is_active": True,
    },
    {
        "username": "manager",
        "password": "manager123",
        "role": "manager",
        "is_active": True,
    },
    {
        "username": "user",
        "password": "user123",
        "role": "user",
        "is_active": True,
    },
    {
        "username": "inactive",
        "password": "inactive123",
        "role": "user",
        "is_active": False,
    },
]


def seed_users(session: Session) -> None:
    print("Seeding users...")

    for data in USERS:
        existing = session.query(User).filter(User.username == data["username"]).first()
        if existing:
            print(f"    User '{data['username']}' already exists → skipped")
            continue

        user = User(
            username=data["username"],
            password_hash=hash_password(data["password"]),
            role=data["role"],
            is_active=data["is_active"],
        )
        session.add(user)
        print(f"Created user '{data['username']}' (role={data['role']})")

    session.commit()
    print("User seeding completed")


def main():
    session = db.get_session()
    try:
        seed_users(session)
    finally:
        session.close()


if __name__ == "__main__":
    main()
