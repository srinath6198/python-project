import logging
from fastapi import FastAPI

from app.database import Base, engine
from app import models  # noqa: F401  (imports User so table gets registered)
from app.routers import admin_users, auth, company, product, user,Configmaster,purchase_order,purchase,stock
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Flower Billing App API",
    description="Billing application backend for flower farmers (rose, leaves, etc.)",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(company.router)
app.include_router(admin_users.router)
app.include_router(Configmaster.router)
app.include_router(product.router)
app.include_router(purchase_order.router)
app.include_router(purchase.router)
app.include_router(stock.router)

@app.on_event("startup")
def startup_event():
    """Create database tables on startup if they don't exist."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        logger.warning(
            "Make sure MySQL is running and database credentials are correct. "
            "Check your .env file for DB_USER, DB_PASSWORD, DB_HOST, and DB_NAME."
        )


@app.get("/", tags=["Health"])
def root():
    return {"message": "Flower Billing App API is running"}


# class student():
#     def __init__(self):
#         self.name="Srinath"
#         self.age=27
        
#     def display(self):
#         print("Name :",self.name)
#         print( "Age :",self.age)
        
# s1=student()
# s2= student()

# s1.name = "Appi"
# s1.age = 30

# s2.name = "Srinath"
# s2.age = 28


# s1.display()
# s2.display()
        