from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base


class Purchase(Base):
    __tablename__ = "purchases"

    purchase_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, nullable=False, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.purchase_order_id"), nullable=True)
    invoice_number = Column(String(100), nullable=False)
    supplier_name = Column(String(200), nullable=True)
    purchase_date = Column(Date, nullable=False)
    sub_total = Column(Float, nullable=False, default=0)
    tax_total = Column(Float, nullable=False, default=0)
    grand_total = Column(Float, nullable=False, default=0)
    notes = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_date = Column(DateTime, server_default=func.now())

    items = relationship(
        "PurchaseItem",
        back_populates="purchase",
        cascade="all, delete-orphan",
    )


class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    purchase_item_id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.purchase_id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Float, nullable=False)
    purchase_price = Column(Float, nullable=False)
    tax = Column(Float, nullable=False, default=0)
    line_total = Column(Float, nullable=False, default=0)

    purchase = relationship("Purchase", back_populates="items")