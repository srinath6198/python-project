from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class PurchaseItemCreate(BaseModel):
    product_id: int
    quantity: float = Field(gt=0)
    purchase_price: float = Field(ge=0)
    tax: Optional[float] = Field(default=None, ge=0)


class PurchaseCreate(BaseModel):
    purchase_order_id: Optional[int] = None
    invoice_number: str
    supplier_name: Optional[str] = None
    purchase_date: date
    notes: Optional[str] = None
    items: Optional[List[PurchaseItemCreate]] = None

    @model_validator(mode="after")
    def check_items_or_po(self):
        if not self.items and self.purchase_order_id is None:
            raise ValueError("items are required when purchase_order_id is not provided")
        return self