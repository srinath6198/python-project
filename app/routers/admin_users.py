from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.authorization import require_super_admin_or_admin
from app.database import get_db
from app.models.company import Company
from app.models.user import User, UserRole
from app.schemas.user import AdminUserCreate, AdminUserUpdate, UserOut
from app.utils.security import hash_password


router = APIRouter(prefix="/api/admin/users", tags=["Admin User Master"])


def can_manage_role(manager: User, target_role: UserRole) -> bool:
    if manager.role == UserRole.SUPER_ADMIN.value:
        return target_role in {
            UserRole.SUPER_ADMIN_USER,
            UserRole.ADMIN,
            UserRole.ADMIN_USER,
        }
    return manager.role == UserRole.ADMIN.value and target_role == UserRole.ADMIN_USER


def can_manage_user(manager: User, target: User) -> bool:
    try:
        target_role = UserRole(target.role)
    except ValueError:
        return False
    return can_manage_role(manager, target_role)


def get_target_user(user_id: int, db: Session) -> User:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def ensure_company(company_id: int | None, db: Session) -> None:
    if company_id is not None and db.query(Company).filter(Company.company_id == company_id).first() is None:
        raise HTTPException(status_code=404, detail="Company not found")


def ensure_unique_user_fields(
    db: Session,
    username: str,
    email: str,
    user_id: int | None = None,
) -> None:
    query = db.query(User).filter((User.username == username) | (User.email == email))
    if user_id is not None:
        query = query.filter(User.user_id != user_id)
    if query.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        )


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_admin_user(
    request: AdminUserCreate,
    manager: User = Depends(require_super_admin_or_admin()),
    db: Session = Depends(get_db),
):
    if not can_manage_role(manager, request.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot create a user with this role",
        )
    company_id = request.company_id if manager.role == UserRole.SUPER_ADMIN.value else manager.company_id
    if company_id is None:
        raise HTTPException(status_code=400, detail="Manager is not assigned to a company")
    ensure_company(company_id, db)
    ensure_unique_user_fields(db, request.username, request.email)

    user = User(
        company_id=company_id,
        username=request.username,
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        mobile_number=request.mobile_number,
        address=request.address,
        shopName=request.shopName,
        role=request.role.value,
        is_active=request.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=list[UserOut])
def list_admin_users(
    manager: User = Depends(require_super_admin_or_admin()),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if manager.role != UserRole.SUPER_ADMIN.value and manager.company_id is not None:
        query = query.filter(User.company_id == manager.company_id)
    if manager.role == UserRole.ADMIN.value:
        query = query.filter(User.role == UserRole.ADMIN_USER.value)
    else:
        query = query.filter(User.role != UserRole.SUPER_ADMIN.value)
    return query.order_by(User.user_id).all()


@router.get("/{user_id}", response_model=UserOut)
def get_admin_user(
    user_id: int,
    manager: User = Depends(require_super_admin_or_admin()),
    db: Session = Depends(get_db),
):
    user = get_target_user(user_id, db)
    if not can_manage_user(manager, user) or (
        manager.role != UserRole.SUPER_ADMIN.value
        and manager.company_id != user.company_id
    ):
        raise HTTPException(status_code=403, detail="You cannot manage this user")
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_admin_user(
    user_id: int,
    request: AdminUserUpdate,
    manager: User = Depends(require_super_admin_or_admin()),
    db: Session = Depends(get_db),
):
    user = get_target_user(user_id, db)
    if not can_manage_user(manager, user) or not can_manage_role(manager, request.role) or (
        manager.role != UserRole.SUPER_ADMIN.value
        and manager.company_id != user.company_id
    ):
        raise HTTPException(status_code=403, detail="You cannot manage this role")
    ensure_unique_user_fields(db, request.username, request.email, user_id)

    user.username = request.username
    if manager.role == UserRole.SUPER_ADMIN.value and request.company_id is not None:
        ensure_company(request.company_id, db)
        user.company_id = request.company_id
    user.email = request.email
    user.full_name = request.full_name
    user.mobile_number = request.mobile_number
    user.address = request.address
    user.shopName = request.shopName
    user.role = request.role.value
    user.is_active = request.is_active
    if request.password:
        user.password_hash = hash_password(request.password)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_admin_user(
    user_id: int,
    manager: User = Depends(require_super_admin_or_admin()),
    db: Session = Depends(get_db),
):
    user = get_target_user(user_id, db)
    if not can_manage_user(manager, user) or (
        manager.role != UserRole.SUPER_ADMIN.value
        and manager.company_id != user.company_id
    ):
        raise HTTPException(status_code=403, detail="You cannot delete this user")
    if user.user_id == manager.user_id:
        raise HTTPException(status_code=403, detail="You cannot delete your own account")

    db.delete(user)
    db.commit()
    return {"success": True, "message": "User deleted successfully"}