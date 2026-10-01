from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.authorization import require_admin
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderUpdate


router = APIRouter(
    prefix="/purchase_orders",
    tags=["Purchase Orders"])


def purchase_order_data(po: PurchaseOrder) -> dict:
    return {
        "purchase_order_id": po.purchase_order_id,
        "po_number": po.po_number,
        "supplier_name": po.supplier_name,
        "order_date": po.order_date,
        "expected_date": po.expected_date,
        "sub_total": po.sub_total,
        "tax_total": po.tax_total,
        "grand_total": po.grand_total,
        "status": po.status,
        "notes": po.notes,
        "is_active": po.is_active,
        "created_date": po.created_date,
        "items": [
            {
                "purchase_order_item_id": item.purchase_order_item_id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "purchase_price": item.purchase_price,
                "tax": item.tax,
                "line_total": item.line_total,
            }
            for item in po.items
        ],
    }


def build_po_items(
    request: PurchaseOrderCreate | PurchaseOrderUpdate,
    company_id: int,
    db: Session,
    allow_inline_products: bool = False,
):
    items = []
    sub_total = 0.0
    tax_total = 0.0

    for item in request.items:
        if item.product_id is not None:
            product = db.query(Product).filter(
                Product.product_id == item.product_id,
                Product.company_id == company_id,
            ).first()

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Product {item.product_id} not found in your company",
                )
        else:
            if not allow_inline_products:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Inline product creation is only available when creating a purchase order",
                )

            existing_product = db.query(Product).filter(
                Product.product_code == item.product_code,
            ).first()
            if existing_product:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Product code {item.product_code} already exists; use product_id instead",
                )

            product = Product(
                company_id=company_id,
                product_code=item.product_code,
                product_name=item.product_name,
                purchase_price=item.purchase_price,
                selling_price=item.selling_price,
                tax=item.tax if item.tax is not None else 0,
                category=item.category,
                unit=item.unit,
                opening_stock=0,
                current_stock=0,
                minimum_stock=0,
                is_active=True,
            )
            db.add(product)
            db.flush()

        tax_percent = item.tax if item.tax is not None else (product.tax or 0)
        line_amount = item.quantity * item.purchase_price
        line_tax = line_amount * tax_percent / 100

        items.append(
            PurchaseOrderItem(
                product_id=product.product_id,
                quantity=item.quantity,
                purchase_price=item.purchase_price,
                tax=tax_percent,
                line_total=line_amount + line_tax,
            )
        )
        sub_total += line_amount
        tax_total += line_tax

    return items, sub_total, tax_total


# POST   /purchase-orders                      → Create purchase order
# GET    /purchase-orders                      → Get all purchase orders
# GET    /purchase-orders/{purchase_order_id}  → Get purchase order by ID
# PUT    /purchase-orders/{purchase_order_id}  → Update purchase order (PENDING only)
# PUT    /purchase-orders/{purchase_order_id}/cancel → Cancel purchase order (PENDING only)

@router.post("", status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    request: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin()),
):
    if current_user.company_id is None:
        raise HTTPException(status_code=400, detail="User is not assigned to a company")

    existing = db.query(PurchaseOrder).filter(
        PurchaseOrder.po_number == request.po_number,
        PurchaseOrder.company_id == current_user.company_id,
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="PO number already exists"
        )

    items, sub_total, tax_total = build_po_items(
        request,
        current_user.company_id,
        db,
        allow_inline_products=True,
    )

    po = PurchaseOrder(
        company_id=current_user.company_id,
        po_number=request.po_number,
        supplier_name=request.supplier_name,
        order_date=request.order_date,
        expected_date=request.expected_date,
        notes=request.notes,
        status="PENDING",
        sub_total=sub_total,
        tax_total=tax_total,
        grand_total=sub_total + tax_total,
    )
    po.items = items

    db.add(po)
    db.commit()
    db.refresh(po)

    return {
        "success": True,
        "message": "Purchase order created successfully",
        "data": purchase_order_data(po)
    }


@router.get("")
def get_purchase_orders(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin()),
):
    orders = db.query(PurchaseOrder).filter(
        PurchaseOrder.company_id == current_user.company_id
    ).order_by(PurchaseOrder.purchase_order_id.desc()).all()

    return {
        "success": True,
        "message": "Purchase orders fetched successfully",
        "data": [purchase_order_data(po) for po in orders]
    }


@router.get("/{purchase_order_id}")
def get_purchase_order(
    purchase_order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin()),
):
    po = db.query(PurchaseOrder).filter(
        PurchaseOrder.purchase_order_id == purchase_order_id,
        PurchaseOrder.company_id == current_user.company_id,
    ).first()

    if not po:
        raise HTTPException(
            status_code=404,
            detail="Purchase order not found"
        )

    return {
        "success": True,
        "message": "Purchase order fetched successfully",
        "data": purchase_order_data(po)
    }


@router.put("/{purchase_order_id}")
def update_purchase_order(
    purchase_order_id: int,
    request: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin()),
):
    po = db.query(PurchaseOrder).filter(
        PurchaseOrder.purchase_order_id == purchase_order_id,
        PurchaseOrder.company_id == current_user.company_id,
    ).first()

    if not po:
        raise HTTPException(
            status_code=404,
            detail="Purchase order not found"
        )

    if po.status != "PENDING":
        raise HTTPException(
            status_code=409,
            detail=f"Only PENDING purchase orders can be edited (current status: {po.status})",
        )

    duplicate = db.query(PurchaseOrder).filter(
        PurchaseOrder.po_number == request.po_number,
        PurchaseOrder.purchase_order_id != purchase_order_id,
        PurchaseOrder.company_id == current_user.company_id,
    ).first()
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="PO number already exists",
        )

    items, sub_total, tax_total = build_po_items(request, current_user.company_id, db)

    po.po_number = request.po_number
    po.supplier_name = request.supplier_name
    po.order_date = request.order_date
    po.expected_date = request.expected_date
    po.notes = request.notes
    po.sub_total = sub_total
    po.tax_total = tax_total
    po.grand_total = sub_total + tax_total
    po.items.clear()
    po.items.extend(items)

    db.commit()
    db.refresh(po)

    return {
        "success": True,
        "message": "Purchase order updated successfully",
        "data": purchase_order_data(po)
    }


@router.put("/{purchase_order_id}/cancel")
def cancel_purchase_order(
    purchase_order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin()),
):
    po = db.query(PurchaseOrder).filter(
        PurchaseOrder.purchase_order_id == purchase_order_id,
        PurchaseOrder.company_id == current_user.company_id,
    ).first()

    if not po:
        raise HTTPException(
            status_code=404,
            detail="Purchase order not found"
        )

    if po.status != "PENDING":
        raise HTTPException(
            status_code=409,
            detail=f"Only PENDING purchase orders can be cancelled (current status: {po.status})",
        )

    po.status = "CANCELLED"
    db.commit()
    db.refresh(po)

    return {
        "success": True,
        "message": "Purchase order cancelled successfully",
        "data": purchase_order_data(po)
    }