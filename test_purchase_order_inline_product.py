import unittest
from datetime import date

from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.company import Company
from app.models.product import Product
from app.routers.purchase_order import build_po_items
from app.schemas.purchase_order import PurchaseOrderCreate


class PurchaseOrderInlineProductTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.db = Session(self.engine)
        self.company = Company(company_code="PO-COMPANY", company_name="PO Company")
        self.db.add(self.company)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_inline_product_is_created_with_purchase_order_item(self):
        request = PurchaseOrderCreate(
            po_number="PO-1001",
            supplier_name="ABC Traders",
            order_date=date(2026, 10, 1),
            items=[
                {
                    "product_code": "FLOWER-1",
                    "product_name": "Rose",
                    "purchase_price": 120,
                    "selling_price": 150,
                    "quantity": 50,
                    "tax": 18,
                }
            ],
        )

        items, sub_total, tax_total = build_po_items(
            request,
            self.company.company_id,
            self.db,
            allow_inline_products=True,
        )

        product = self.db.query(Product).filter_by(product_code="FLOWER-1").one()
        self.assertEqual(items[0].product_id, product.product_id)
        self.assertEqual(product.company_id, self.company.company_id)
        self.assertEqual(sub_total, 6000)
        self.assertEqual(tax_total, 1080)

    def test_quantity_is_required_for_inline_product(self):
        with self.assertRaises(ValidationError):
            PurchaseOrderCreate(
                po_number="PO-1002",
                supplier_name="ABC Traders",
                order_date=date(2026, 10, 1),
                items=[
                    {
                        "product_code": "FLOWER-2",
                        "product_name": "Lily",
                        "purchase_price": 100,
                        "selling_price": 130,
                    }
                ],
            )


if __name__ == "__main__":
    unittest.main()