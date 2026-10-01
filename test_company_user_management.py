import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth.authorization import require_super_admin
from app.database import Base
from app.models.user import User, UserRole
from app.routers.admin_users import create_admin_user, get_admin_user, list_admin_users
from app.routers.auth import register
from app.routers.company import get_company_by_id
from app.schemas.user import AdminUserCreate, UserCreate
from app.utils.security import verify_password


class CompanyUserManagementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=cls.engine)
        cls.engine.dispose()

    def setUp(self):
        self.db = Session(self.engine)

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def register_company(self, suffix="one"):
        return register(
            UserCreate(
                username=f"owner-{suffix}",
                email=f"owner-{suffix}@example.com",
                password="secure-password",
                full_name="Company Owner",
                company_id=0,
                company_name=f"Company {suffix}",
            ),
            self.db,
        )

    def test_registration_creates_company_and_hashed_super_admin(self):
        response = self.register_company()

        self.assertEqual(response.company.company_name, "Company one")
        self.assertGreater(response.company.company_id, 0)
        self.assertEqual(response.user.company_id, response.company.company_id)
        self.assertEqual(response.user.role, UserRole.SUPER_ADMIN)
        self.assertNotIn("password", response.user.model_dump())

        user = self.db.query(User).filter_by(user_id=response.user.user_id).one()
        self.assertNotEqual(user.password_hash, "secure-password")
        self.assertTrue(verify_password("secure-password", user.password_hash))

    def test_super_admin_can_add_two_users_but_not_a_fourth(self):
        response = self.register_company()
        manager = self.db.query(User).filter_by(user_id=response.user.user_id).one()

        for index in range(2):
            create_admin_user(
                AdminUserCreate(
                    username=f"staff-{index}",
                    email=f"staff-{index}@example.com",
                    password="secure-password",
                    role=UserRole.ADMIN_USER,
                ),
                manager=manager,
                db=self.db,
            )

        with self.assertRaises(HTTPException) as error:
            create_admin_user(
                AdminUserCreate(
                    username="staff-over-limit",
                    email="staff-over-limit@example.com",
                    password="secure-password",
                    role=UserRole.ADMIN_USER,
                ),
                manager=manager,
                db=self.db,
            )

        self.assertEqual(error.exception.status_code, 402)
        self.assertEqual(
            self.db.query(User).filter(User.company_id == manager.company_id).count(),
            3,
        )

    def test_non_super_admin_is_rejected_by_role_guard(self):
        regular_user = User(
            company_id=1,
            username="regular",
            email="regular@example.com",
            password_hash="not-used",
            role=UserRole.ADMIN_USER.value,
        )

        with self.assertRaises(HTTPException) as error:
            require_super_admin()(current_user=regular_user)

        self.assertEqual(error.exception.status_code, 403)

    def test_admin_can_view_only_their_own_company(self):
        own_company = self.register_company("admin-own").company
        other_company = self.register_company("admin-other").company
        admin = User(
            company_id=own_company.company_id,
            username="company-admin",
            email="company-admin@example.com",
            password_hash="not-used",
            role=UserRole.ADMIN.value,
        )

        result = get_company_by_id(own_company.company_id, current_user=admin, db=self.db)
        self.assertEqual(result.company_id, own_company.company_id)

        with self.assertRaises(HTTPException) as error:
            get_company_by_id(other_company.company_id, current_user=admin, db=self.db)

        self.assertEqual(error.exception.status_code, 403)

    def test_super_admin_can_only_view_users_in_their_company(self):
        own_company = self.register_company("own")
        other_company = self.register_company("other")
        manager = self.db.query(User).filter_by(user_id=own_company.user.user_id).one()

        visible_users = list_admin_users(manager=manager, db=self.db)
        self.assertEqual(
            [user.company_id for user in visible_users],
            [own_company.company.company_id],
        )

        with self.assertRaises(HTTPException) as error:
            get_admin_user(
                user_id=other_company.user.user_id,
                manager=manager,
                db=self.db,
            )

        self.assertEqual(error.exception.status_code, 403)

    def test_public_registration_cannot_join_an_existing_company(self):
        response = self.register_company()

        with self.assertRaises(HTTPException) as error:
            register(
                UserCreate(
                    username="uninvited",
                    email="uninvited@example.com",
                    password="secure-password",
                    company_id=response.company.company_id,
                    company_name="Attempted company",
                ),
                self.db,
            )

        self.assertEqual(error.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()