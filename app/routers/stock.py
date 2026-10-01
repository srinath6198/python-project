from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.authorization import require_admin
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem


router = APIRouter(
    prefix="/stock",
    tags=["Stock"])


def stock_status(product: Product) -> str:
    current = product.current_stock or 0
    minimum = product.minimum_stock or 0

    if current <= 0:
        return "OUT_OF_STOCK"
    if current <= minimum:
        return "LOW_STOCK"
    return "IN_STOCK"


def on_order_quantities(company_id: int, db: Session) -> dict:
    # Quantity still expected from PENDING purchase orders, per product
    rows = db.query(
        PurchaseOrderItem.product_id,
        func.sum(PurchaseOrderItem.quantity),
    ).join(
        PurchaseOrder,
        PurchaseOrder.purchase_order_id == PurchaseOrderItem.purchase_order_id,
    ).filter(
        PurchaseOrder.company_id == company_id,
        PurchaseOrder.status == "PENDING",
    ).group_by(PurchaseOrderItem.product_id).all()

    return {product_id: float(quantity or 0) for product_id, quantity in rows}


def stock_data(product: Product, on_order: float = 0) -> dict:
    current = product.current_stock or 0
    return {
        "product_id": product.product_id,
        "product_code": product.product_code,
        "product_name": product.product_name,
        "category": product.category,
        "unit": product.unit,
        "opening_stock": product.opening_stock,
        "current_stock": current,
        "minimum_stock": product.minimum_stock,
        "on_order": on_order,
        "purchase_price": product.purchase_price,
        "selling_price": product.selling_price,
        "stock_value": current * (product.purchase_price or 0),
        "status": stock_status(product),
        "is_active": product.is_active,
    }


# GET /stock                → Get stock of all products (filters: search, category, status)
# GET /stock/low            → Get products at or below minimum stock
# GET /stock/{product_id}   → Get stock of one product

@router.get("")
def get_stock(
    search: Optional[str] = Query(default=None, description="Match product code or name"),
    category: Optional[str] = None,
    status: Optional[str] = Query(default=None, description="IN_STOCK / LOW_STOCK / OUT_OF_STOCK"),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin()),
):
    query = db.query(Product).filter(Product.company_id == current_user.company_id)

    if search:
        like = f"%{search}%"
        query = query.filter(
            Product.product_code.ilike(like) | Product.product_name.ilike(like)
        )

    if category:
        query = query.filter(Product.category == category)

    products = query.order_by(Product.product_name).all()
    on_order = on_order_quantities(current_user.company_id, db)

    rows = [stock_data(p, on_order.get(p.product_id, 0)) for p in products]

    if status:
        wanted = status.strip().upper()
        rows = [row for row in rows if row["status"] == wanted]

    return {
        "success": True,
        "message": "Stock fetched successfully",
        "summary": {
            "total_products": len(rows),
            "in_stock": sum(1 for row in rows if row["status"] == "IN_STOCK"),
            "low_stock": sum(1 for row in rows if row["status"] == "LOW_STOCK"),
            "out_of_stock": sum(1 for row in rows if row["status"] == "OUT_OF_STOCK"),
            "total_stock_value": sum(row["stock_value"] for row in rows),
        },
        "data": rows
    }


@router.get("/low")
def get_low_stock(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin()),
):
    products = db.query(Product).filter(
        Product.company_id == current_user.company_id,
        Product.is_active.is_(True),
        func.coalesce(Product.current_stock, 0) <= func.coalesce(Product.minimum_stock, 0),
    ).order_by(Product.current_stock).all()

    on_order = on_order_quantities(current_user.company_id, db)

    return {
        "success": True,
        "message": "Low stock products fetched successfully",
        "data": [stock_data(p, on_order.get(p.product_id, 0)) for p in products]
    }


@router.get("/{product_id}")
def get_product_stock(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin()),
):
    product = db.query(Product).filter(
        Product.product_id == product_id,
        Product.company_id == current_user.company_id,
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    on_order = on_order_quantities(current_user.company_id, db)

    return {
        "success": True,
        "message": "Stock fetched successfully",
        "data": stock_data(product, on_order.get(product.product_id, 0))
    }