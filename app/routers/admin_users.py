from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.authorization import require_super_admin
from app.database import get_db
from app.models.company import Company
from app.models.user import RefreshToken, User, UserRole
from app.schemas.user import AdminUserCreate, AdminUserUpdate, UserOut
from app.utils.security import hash_password


router = APIRouter(prefix="/api/admin/users", tags=["Admin User Master"])


def can_manage_role(manager: User, target_role: UserRole) -> bool:
    return (
        manager.role == UserRole.SUPER_ADMIN.value
        and target_role != UserRole.SUPER_ADMIN
    )


def can_manage_user(manager: User, target: User) -> bool:
    return (
        manager.role == UserRole.SUPER_ADMIN.value
        and manager.company_id is not None
        and target.company_id == manager.company_id
    )


def get_target_user(user_id: int, db: Session) -> User:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


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
    manager: User = Depends(require_super_admin()),
    db: Session = Depends(get_db),
):
    if not can_manage_role(manager, request.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot create a user with this role",
        )
    company_id = manager.company_id
    if company_id is None:
        raise HTTPException(status_code=403, detail="Super Admin must belong to a company")
    if request.company_id not in (None, company_id):
        raise HTTPException(status_code=403, detail="Users must belong to your company")

    company = (
        db.query(Company)
        .filter(Company.company_id == company_id)
        .with_for_update()
        .first()
    )
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    user_count = db.query(User).filter(User.company_id == company_id).count()
    if user_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Free plan includes 3 users. Upgrade the company plan to add more users.",
        )

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
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        ) from exc
    db.refresh(user)
    return user


@router.get("", response_model=list[UserOut])
def list_admin_users(
    manager: User = Depends(require_super_admin()),
    db: Session = Depends(get_db),
):
    return (
        db.query(User)
        .filter(User.company_id == manager.company_id)
        .order_by(User.user_id)
        .all()
    )


@router.get("/{user_id}", response_model=UserOut)
def get_admin_user(
    user_id: int,
    manager: User = Depends(require_super_admin()),
    db: Session = Depends(get_db),
):
    user = get_target_user(user_id, db)
    if not can_manage_user(manager, user):
        raise HTTPException(status_code=403, detail="You cannot manage this user")
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_admin_user(
    user_id: int,
    request: AdminUserUpdate,
    manager: User = Depends(require_super_admin()),
    db: Session = Depends(get_db),
):
    user = get_target_user(user_id, db)
    if not can_manage_user(manager, user):
        raise HTTPException(status_code=403, detail="You cannot manage this role")
    if request.company_id not in (None, manager.company_id):
        raise HTTPException(status_code=403, detail="Users cannot be moved to another company")
    if user.user_id == manager.user_id:
        if request.role != UserRole.SUPER_ADMIN or not request.is_active:
            raise HTTPException(status_code=403, detail="You cannot change your own Super Admin access")
    elif not can_manage_role(manager, request.role):
        raise HTTPException(status_code=403, detail="You cannot assign this role")
    ensure_unique_user_fields(db, request.username, request.email, user_id)

    user.username = request.username
    user.email = request.email
    user.full_name = request.full_name
    user.mobile_number = request.mobile_number
    user.address = request.address
    user.shopName = request.shopName
    user.role = request.role.value
    user.is_active = request.is_active
    if request.password:
        user.password_hash = hash_password(request.password)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        ) from exc
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_admin_user(
    user_id: int,
    manager: User = Depends(require_super_admin()),
    db: Session = Depends(get_db),
):
    user = get_target_user(user_id, db)
    if not can_manage_user(manager, user):
        raise HTTPException(status_code=403, detail="You cannot delete this user")
    if user.user_id == manager.user_id:
        raise HTTPException(status_code=403, detail="You cannot delete your own account")

    db.query(RefreshToken).filter(RefreshToken.user_id == user.user_id).delete(
        synchronize_session=False
    )
    db.delete(user)
    db.commit()
    return {"success": True, "message": "User deleted successfully"}