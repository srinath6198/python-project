from fastapi import FastAPI

from app.database import Base, engine
from app import models  # noqa: F401  (imports User so table gets registered)
from app.routers import auth

# Creates tables in MySQL if they don't already exist.
# (For production, use Alembic migrations instead of this.)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Flower Billing App API",
    description="Billing application backend for flower farmers (rose, leaves, etc.)",
    version="1.0.0",
)

app.include_router(auth.router)


@app.get("/", tags=["Health"])
def root():
    return {"message": "Flower Billing App API is running"}
