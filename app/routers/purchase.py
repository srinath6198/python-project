from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.authorization import require_admin
from app.models.product import Product
from app.models.purchase import Purchase, PurchaseItem
from app.models.purchase_order import PurchaseOrder
from app.schemas.purchase import PurchaseCreate, PurchaseItemCreate


router = APIRouter(
    prefix="/purchases",
    tags=["Purchases"])


def purchase_data(purchase: Purchase) -> dict:
    return {
        "purchase_id": purchase.purchase_id,
        "purchase_order_id": purchase.purchase_order_id,
        "invoice_number": purchase.invoice_number,
        "supplier_name": purchase.supplier_name,
        "purchase_date": purchase.purchase_date,
        "sub_total": purchase.sub_total,
        "tax_total": purchase.tax_total,
        "grand_total": purchase.grand_total,
        "notes": purchase.notes,
        "is_active": purchase.is_active,
        "created_date": purchase.created_date,
        "items": [
            {
                "purchase_item_id": item.purchase_item_id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "purchase_price": item.purchase_price,
                "tax": item.tax,
                "line_total": item.line_total,
            }
            for item in purchase.items
        ],
    }


# POST   /purchases               → Create purchase entry (increases stock, marks PO as RECEIVED)
# GET    /purchases               → Get all purchases
# GET    /purchases/{purchase_id} → Get purchase by ID
# DELETE /purchases/{purchase_id} → Delete purchase (reverses stock, PO back to PENDING)

@router.post("", status_code=status.HTTP_201_CREATED)
def create_purchase(
    request: PurchaseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin()),
):
    if current_user.company_id is None:
        raise HTTPException(status_code=400, detail="User is not assigned to a company")

    existing_purchase = db.query(Purchase).filter(
        Purchase.invoice_number == request.invoice_number,
        Purchase.company_id == current_user.company_id,
    ).first()

    if existing_purchase:
        raise HTTPException(
            status_code=409,
            detail="Invoice number already exists"
        )

    po = None
    items_source = request.items
    supplier_name = request.supplier_name

    if request.purchase_order_id is not None:
        po = db.query(PurchaseOrder).filter(
            PurchaseOrder.purchase_order_id == request.purchase_order_id,
            PurchaseOrder.company_id == current_user.company_id,
        ).with_for_update().first()

        if not po:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Purchase order not found in your company",
            )

        if po.status != "PENDING":
            raise HTTPException(
                status_code=409,
                detail=f"Purchase order is already {po.status}",
            )

        if not items_source:
            items_source = [
                PurchaseItemCreate(
                    product_id=po_item.product_id,
                    quantity=po_item.quantity,
                    purchase_price=po_item.purchase_price,
                    tax=po_item.tax,
                )
                for po_item in po.items
            ]

        if not supplier_name:
            supplier_name = po.supplier_name

    purchase = Purchase(
        company_id=current_user.company_id,
        purchase_order_id=po.purchase_order_id if po else None,
        invoice_number=request.invoice_number,
        supplier_name=supplier_name,
        purchase_date=request.purchase_date,
        notes=request.notes,
    )

    sub_total = 0.0
    tax_total = 0.0

    for item in items_source:
        product = db.query(Product).filter(
            Product.product_id == item.product_id,
            Product.company_id == current_user.company_id,
        ).with_for_update().first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Product {item.product_id} not found in your company",
            )

        tax_percent = item.tax if item.tax is not None else (product.tax or 0)
        line_amount = item.quantity * item.purchase_price
        line_tax = line_amount * tax_percent / 100

        purchase.items.append(
            PurchaseItem(
                product_id=product.product_id,
                quantity=item.quantity,
                purchase_price=item.purchase_price,
                tax=tax_percent,
                line_total=line_amount + line_tax,
            )
        )

        sub_total += line_amount
        tax_total += line_tax

        product.current_stock = (product.current_stock or 0) + item.quantity
        product.purchase_price = item.purchase_price

    purchase.sub_total = sub_total
    purchase.tax_total = tax_total
    purchase.grand_total = sub_total + tax_total

    if po:
        po.status = "RECEIVED"

    db.add(purchase)
    db.commit()
    db.refresh(purchase)

    return {
        "success": True,
        "message": "Purchase created successfully",
        "data": purchase_data(purchase)
    }


@router.get("")
def get_purchases(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin()),
):
    purchases = db.query(Purchase).filter(
        Purchase.company_id == current_user.company_id
    ).order_by(Purchase.purchase_id.desc()).all()

    return {
        "success": True,
        "message": "Purchases fetched successfully",
        "data": [purchase_data(purchase) for purchase in purchases]
    }


@router.get("/{purchase_id}")
def get_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin()),
):
    purchase = db.query(Purchase).filter(
        Purchase.purchase_id == purchase_id,
        Purchase.company_id == current_user.company_id,
    ).first()

    if not purchase:
        raise HTTPException(
            status_code=404,
            detail="Purchase not found"
        )

    return {
        "success": True,
        "message": "Purchase fetched successfully",
        "data": purchase_data(purchase)
    }


@router.delete("/{purchase_id}")
def delete_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin()),
):
    purchase = db.query(Purchase).filter(
        Purchase.purchase_id == purchase_id,
        Purchase.company_id == current_user.company_id,
    ).first()

    if not purchase:
        raise HTTPException(
            status_code=404,
            detail="Purchase not found"
        )

    for item in purchase.items:
        product = db.query(Product).filter(
            Product.product_id == item.product_id,
            Product.company_id == current_user.company_id,
        ).with_for_update().first()

        if product:
            if (product.current_stock or 0) < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot delete: stock of '{product.product_name}' is already below purchased quantity",
                )
            product.current_stock = product.current_stock - item.quantity

    if purchase.purchase_order_id is not None:
        po = db.query(PurchaseOrder).filter(
            PurchaseOrder.purchase_order_id == purchase.purchase_order_id,
            PurchaseOrder.company_id == current_user.company_id,
        ).first()
        if po and po.status == "RECEIVED":
            po.status = "PENDING"

    db.delete(purchase)
    db.commit()

    return {
        "success": True,
        "message": "Purchase deleted successfully"
    }