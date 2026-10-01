from datetime import date

from pydantic import BaseModel, Field, model_validator


class PurchaseOrderItemCreate(BaseModel):
    product_id: int | None = None
    product_code: str | None = Field(default=None, min_length=1, max_length=50)
    product_name: str | None = Field(default=None, min_length=2, max_length=150)
    selling_price: float | None = Field(default=None, ge=0)
    category: str | None = None
    unit: str | None = None
    quantity: float = Field(gt=0)
    purchase_price: float = Field(ge=0)
    tax: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_product_reference(self):
        inline_fields = (self.product_code, self.product_name, self.selling_price)
        if self.product_id is None:
            if any(value is None for value in inline_fields):
                raise ValueError(
                    "Provide product_id, or provide product_code, product_name, and selling_price to create a product"
                )
        elif any(value is not None for value in inline_fields):
            raise ValueError("Provide product_id or inline product details, not both")
        return self


class PurchaseOrderCreate(BaseModel):
    po_number: str
    supplier_name: str
    order_date: date
    expected_date: date | None = None
    notes: str | None = None
    items: list[PurchaseOrderItemCreate] = Field(min_length=1)


class PurchaseOrderUpdate(PurchaseOrderCreate):
    pass