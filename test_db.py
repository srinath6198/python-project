from app.database import SessionLocal
from app.models.user import User
from app.utils.security import hash_password

db = SessionLocal()
try:
    new_user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=hash_password("password123"),
    )
    db.add(new_user)
    db.commit()
    print("✓ User created successfully")
except Exception as e:
    import traceback
    print(f"✗ Error: {type(e).__name__}: {e}")
    traceback.print_exc()
finally:
    db.close()
