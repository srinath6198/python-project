from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class ProductCreate(BaseModel):
    product_code: str
    product_name: str
    uom: Optional[str] = None
    size: Optional[str] = None
    length: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None

    purchase_price: Decimal
    selling_price: Decimal
    tax: Optional[Decimal] = 0

    opening_stock: int = 0
    current_stock: int = 0
    minimum_stock: int = 0

    is_active: bool = True


class ProductUpdate(BaseModel):
    product_code: str
    product_name: str
    uom: Optional[str] = None
    size: Optional[str] = None
    length: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None

    purchase_price: Decimal
    selling_price: Decimal
    tax: Optional[Decimal] = 0

    opening_stock: int = 0
    current_stock: int = 0
    minimum_stock: int = 0

    is_active: bool = True