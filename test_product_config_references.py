import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.Configmaster import CompanyConfig
from app.models.company import Company
from app.routers.product import validate_product_configs
from app.schemas.product import ProductCreate


class ProductConfigReferenceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.db = Session(self.engine)
        self.company = Company(company_code="COMPANY-A", company_name="Company A")
        self.other_company = Company(company_code="COMPANY-B", company_name="Company B")
        self.db.add_all([self.company, self.other_company])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def make_request(self, config_id):
        return ProductCreate(
            product_code="FLOWER-1",
            product_name="Rose",
            purchase_price=1,
            selling_price=2,
            uom_config_id=config_id,
        )

    def test_accepts_active_config_of_expected_type_and_company(self):
        config = CompanyConfig(
            company_id=self.company.company_id,
            config_type="UOM",
            config_name="Stem",
            is_active=True,
        )
        self.db.add(config)
        self.db.commit()

        validate_product_configs(self.make_request(config.config_id), self.company.company_id, self.db)

    def test_rejects_config_from_another_company(self):
        config = CompanyConfig(
            company_id=self.other_company.company_id,
            config_type="UOM",
            config_name="Stem",
            is_active=True,
        )
        self.db.add(config)
        self.db.commit()

        with self.assertRaises(HTTPException) as error:
            validate_product_configs(self.make_request(config.config_id), self.company.company_id, self.db)

        self.assertEqual(error.exception.status_code, 422)

    def test_rejects_config_with_wrong_type(self):
        config = CompanyConfig(
            company_id=self.company.company_id,
            config_type="SIZE",
            config_name="Large",
            is_active=True,
        )
        self.db.add(config)
        self.db.commit()

        with self.assertRaises(HTTPException) as error:
            validate_product_configs(self.make_request(config.config_id), self.company.company_id, self.db)

        self.assertEqual(error.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()