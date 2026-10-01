from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    purchase_order_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, nullable=False, index=True)
    po_number = Column(String(100), nullable=False)
    supplier_name = Column(String(200), nullable=False)
    order_date = Column(Date, nullable=False)
    expected_date = Column(Date, nullable=True)
    sub_total = Column(Float, nullable=False, default=0)
    tax_total = Column(Float, nullable=False, default=0)
    grand_total = Column(Float, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING / RECEIVED / CANCELLED
    notes = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_date = Column(DateTime, server_default=func.now())

    items = relationship(
        "PurchaseOrderItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    purchase_order_item_id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.purchase_order_id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Float, nullable=False)
    purchase_price = Column(Float, nullable=False)
    tax = Column(Float, nullable=False, default=0)
    line_total = Column(Float, nullable=False, default=0)

    purchase_order = relationship("PurchaseOrder", back_populates="items")