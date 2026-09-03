from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.models.user import User, UserRole


def require_roles(*allowed_roles: UserRole) -> Callable:
    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in {role.value for role in allowed_roles}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return role_dependency


def require_super_admin() -> Callable:
    return require_roles(UserRole.SUPER_ADMIN)


def require_super_admin_or_admin() -> Callable:
    return require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)


def require_admin() -> Callable:
    return require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)