#!/usr/bin/env python
"""Simulate the complete register flow"""
import sys
import traceback
from datetime import datetime

print("=" * 60)
print("COMPREHENSIVE REGISTER TEST")
print("=" * 60)

# Test 1: Check imports
print("\n[1/5] Testing imports...")
try:
    from app.database import SessionLocal, Base, engine
    from app.models.user import User, RefreshToken
    from app.schemas.user import UserCreate, UserOut
    from app.utils.security import hash_password
    from app.config import settings
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 2: Check database connection
print("\n[2/5] Testing database connection...")
try:
    with engine.connect() as conn:
        pass
    print("✓ Database connection works")
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 3: Create tables
print("\n[3/5] Creating tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created/verified")
except Exception as e:
    print(f"✗ Table creation failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 4: Create a session and test user creation
print("\n[4/5] Testing user creation...")
db = SessionLocal()
try:
    # Clean up test user if exists
    db.query(User).filter(User.username == "appi").delete()
    db.commit()
    
    # Create new user
    user_in = UserCreate(
        username="appi",
        email="appi@gmail.com",
        password="appi@10",
        full_name="Appi"
    )
    print(f"  Creating user: {user_in.username} ({user_in.email})")
    
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hash_password(user_in.password),
    )
    db.add(new_user)
    db.commit()
    print(f"  User added to DB with ID: {new_user.id}")
    
    db.refresh(new_user)
    print(f"  User refreshed from DB")
    print(f"    - ID: {new_user.id}")
    print(f"    - Username: {new_user.username}")
    print(f"    - Email: {new_user.email}")
    print(f"    - Created At: {new_user.created_at}")
    print(f"    - Is Active: {new_user.is_active}")
    
    print("✓ User creation successful")
except Exception as e:
    print(f"✗ User creation failed: {e}")
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()

# Test 5: Test UserOut serialization
print("\n[5/5] Testing UserOut serialization...")
db = SessionLocal()
try:
    user = db.query(User).filter(User.username == "appi").first()
    if not user:
        print("✗ User not found in database")
        sys.exit(1)
    
    user_out = UserOut.model_validate(user)
    print(f"✓ UserOut serialization successful")
    print(f"  Response: {user_out.model_dump_json()}")
except Exception as e:
    print(f"✗ UserOut serialization failed: {e}")
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()

print("\n" + "=" * 60)
print("✓ ALL TESTS PASSED!")
print("=" * 60)
