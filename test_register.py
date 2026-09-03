from app.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.security import hash_password

db = SessionLocal()
try:
    user_in = UserCreate(
        username="appi",
        email="appi@gmail.com",
        password="appi@10",
        full_name="Appi"
    )
    
    # Check for existing username / email
    existing = (
        db.query(User)
        .filter((User.username == user_in.username) | (User.email == user_in.email))
        .first()
    )
    if existing:
        print("✗ User already exists")
    else:
        new_user = User(
            username=user_in.username,
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hash_password(user_in.password),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"✓ User created successfully: {new_user.id}")
except Exception as e:
    import traceback
    print(f"✗ Error: {type(e).__name__}")
    print(f"  {e}")
    traceback.print_exc()
finally:
    db.close()
