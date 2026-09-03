#!/usr/bin/env python
"""Test all imports and basic functionality"""

print("Testing imports...")
try:
    from app.routers import auth
    print("✓ auth module imports")
except Exception as e:
    print(f"✗ Failed to import auth: {e}")
    exit(1)

try:
    from app.database import SessionLocal, Base, engine
    print("✓ database module imports")
except Exception as e:
    print(f"✗ Failed to import database: {e}")
    exit(1)

try:
    from app.models.user import User, RefreshToken
    print("✓ User and RefreshToken models import")
except Exception as e:
    print(f"✗ Failed to import models: {e}")
    exit(1)

try:
    from app.config import settings
    print(f"✓ settings loaded")
    print(f"  - DB: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    print(f"  - REFRESH_TOKEN_EXPIRE_DAYS: {settings.REFRESH_TOKEN_EXPIRE_DAYS}")
except Exception as e:
    print(f"✗ Failed to load settings: {e}")
    exit(1)

print("\nTesting database connection...")
try:
    with engine.connect() as conn:
        print("✓ Connected to MySQL")
except Exception as e:
    print(f"✗ Failed to connect to MySQL: {e}")
    exit(1)

print("\nTesting table creation...")
try:
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")
except Exception as e:
    print(f"✗ Failed to create tables: {e}")
    exit(1)

print("\n✓ All checks passed!")
