#!/usr/bin/env python
"""Direct test of the register endpoint"""
import sys
import traceback

print("Testing register endpoint...")
print("=" * 60)

try:
    from app.database import SessionLocal, Base, engine
    from app.models.user import User
    from app.schemas.user import UserCreate
    from app.utils.security import hash_password
    
    # Clean up any existing test users
    db = SessionLocal()
    db.query(User).filter(User.username == "appi").delete()
    db.commit()
    db.close()
    
    # Now test registration
    db = SessionLocal()
    
    user_in = UserCreate(
        username="appi",
        email="appi@gmail.com",
        password="appi@10",
        full_name="Appi"
    )
    
    print(f"1. Creating user object...")
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hash_password(user_in.password),
    )
    print(f"   ✓ User object created")
    
    print(f"2. Adding to database...")
    db.add(new_user)
    print(f"   ✓ User added to session")
    
    print(f"3. Committing...")
    db.commit()
    print(f"   ✓ Committed to database")
    
    print(f"4. Refreshing user...")
    db.refresh(new_user)
    print(f"   ✓ User refreshed")
    
    print(f"\n✓ SUCCESS! User created:")
    print(f"  - ID: {new_user.id}")
    print(f"  - Username: {new_user.username}")
    print(f"  - Email: {new_user.email}")
    print(f"  - Full Name: {new_user.full_name}")
    print(f"  - Created At: {new_user.created_at}")
    
except Exception as e:
    print(f"\n✗ ERROR: {type(e).__name__}")
    print(f"  Message: {e}")
    print(f"\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
finally:
    try:
        db.close()
    except:
        pass

print("\n" + "=" * 60)
