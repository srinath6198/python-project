from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey
from datetime import datetime

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=True, index=True)

    product_code = Column(String(50), unique=True, nullable=False)
    product_name = Column(String(150), nullable=False)

    uom_config_id = Column(Integer, ForeignKey("company_configs.config_id"), nullable=True)
    size_config_id = Column(Integer, ForeignKey("company_configs.config_id"), nullable=True)
    length_config_id = Column(Integer, ForeignKey("company_configs.config_id"), nullable=True)

    category = Column(String(100), nullable=True)
    unit = Column(String(50), nullable=True)

    purchase_price = Column(Numeric(10, 2), nullable=False)
    selling_price = Column(Numeric(10, 2), nullable=False)

    tax = Column(Numeric(5, 2), nullable=True)

    opening_stock = Column(Integer, default=0)
    current_stock = Column(Integer, default=0)
    minimum_stock = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)

    created_date = Column(
        DateTime,
        default=datetime.utcnow
    )