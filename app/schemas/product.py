from decimal import Decimal

from pydantic import BaseModel


class ProductCreate(BaseModel):
    product_code: str
    product_name: str
    uom_config_id: int | None = None
    size_config_id: int | None = None
    length_config_id: int | None = None
    category: str | None = None
    unit: str | None = None

    purchase_price: Decimal
    selling_price: Decimal
    tax: Decimal | None = 0

    opening_stock: int = 0
    current_stock: int = 0
    minimum_stock: int = 0

    is_active: bool = True


class ProductUpdate(BaseModel):
    product_code: str
    product_name: str
    uom_config_id: int | None = None
    size_config_id: int | None = None
    length_config_id: int | None = None
    category: str | None = None
    unit: str | None = None

    purchase_price: Decimal
    selling_price: Decimal
    tax: Decimal | None = 0

    opening_stock: int = 0
    current_stock: int = 0
    minimum_stock: int = 0

    is_active: bool = True