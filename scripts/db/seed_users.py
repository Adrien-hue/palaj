from db import db
from db.models import User
from backend.app.security.password import hash_password

def upsert(session, username, password, role):
    u = session.query(User).filter(User.username == username).first()
    if u:
        u.password_hash = hash_password(password)
        u.role = role
        u.is_active = True
    else:
        print("Password:", repr(password), "len:", len(password), "bytes:", len(password.encode("utf-8")))
        session.add(User(username=username, password_hash=hash_password(password), role=role, is_active=True))


def main():
    with db.session_scope() as session:
        print("Seeding admin…")
        upsert(session, "admin", "admin", "admin")
        
        print("Seeding manager…")
        upsert(session, "manager", "manager", "manager")

if __name__ == "__main__":
    main()
