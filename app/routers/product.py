
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.authorization import require_admin
from app.models.Configmaster import CompanyConfig
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


router = APIRouter(
    prefix="/products", 
    tags=["Products"])


def product_data(product: Product) -> dict:
    return {
        "product_id": product.product_id,
        "product_code": product.product_code,
        "product_name": product.product_name,
        "uom_config_id": product.uom_config_id,
        "size_config_id": product.size_config_id,
        "length_config_id": product.length_config_id,
        "category": product.category,
        "unit": product.unit,
        "purchase_price": product.purchase_price,
        "selling_price": product.selling_price,
        "tax": product.tax,
        "opening_stock": product.opening_stock,
        "current_stock": product.current_stock,
        "minimum_stock": product.minimum_stock,
        "is_active": product.is_active,
        "created_date": product.created_date,
    }


def validate_product_configs(request: ProductCreate | ProductUpdate, company_id: int, db: Session) -> None:
    expected_types = {
        "uom_config_id": "UOM",
        "size_config_id": "SIZE",
        "length_config_id": "LENGTH",
    }

    for field, expected_type in expected_types.items():
        config_id = getattr(request, field)
        if config_id is None:
            continue

        config = db.query(CompanyConfig).filter(
            CompanyConfig.config_id == config_id,
            CompanyConfig.company_id == company_id,
            CompanyConfig.is_active.is_(True),
        ).first()
        if config is None or config.config_type.strip().upper() != expected_type:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} must reference an active {expected_type} config belonging to your company",
            )


# POST   /products              → Create product
# GET    /products              → Get all products
# GET    /products/{product_id} → Get product by ID
# PUT    /products/{product_id} → Update product
# DELETE /products/{product_id} → Delete product

@router.post("", status_code=status.HTTP_201_CREATED)
def create_product(
    request: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin()),
):
    if current_user.company_id is None:
        raise HTTPException(status_code=400, detail="User is not assigned to a company")
    validate_product_configs(request, current_user.company_id, db)
    existing_product = db.query(Product).filter(
        Product.product_code == request.product_code,
        Product.company_id == current_user.company_id,
    ).first()

    if existing_product:
        raise HTTPException(
            status_code=409,
            detail="Product code already exists"
        )

    product = Product(**request.model_dump(), company_id=current_user.company_id)

    db.add(product)
    db.commit()
    db.refresh(product)

    return {
        "success": True,
        "message": "Product created successfully",
        "data": product_data(product)
    }


@router.get("")
def get_products(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin()),
):
    products = db.query(Product).filter(Product.company_id == current_user.company_id).all()

    return {
        "success": True,
        "message": "Products fetched successfully",
        "data": [product_data(product) for product in products]
    }


@router.get("/{product_id}")
def get_product(
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

    return {
        "success": True,
        "message": "Product fetched successfully",
        "data": product_data(product)
    }


@router.put("/{product_id}")
def update_product(
    product_id: int,
    request: ProductUpdate,
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

    if current_user.company_id is None:
        raise HTTPException(status_code=400, detail="User is not assigned to a company")
    validate_product_configs(request, current_user.company_id, db)

    duplicate = db.query(Product).filter(
        Product.product_code == request.product_code,
        Product.product_id != product_id,
        Product.company_id == current_user.company_id,
    ).first()
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product code already exists",
        )

    for field, value in request.model_dump().items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return {
        "success": True,
        "message": "Product updated successfully",
        "data": product_data(product)
    }


@router.delete("/{product_id}")
def delete_product(
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

    db.delete(product)
    db.commit()

    return {
        "success": True,
        "message": "Product deleted successfully"
    }