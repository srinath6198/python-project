from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.auth.dependencies import get_current_user
from app.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.config import settings
from app.database import get_db
from app.models.user import User, RefreshToken
from app.schemas.user import Token, UserCreate, UserOut, RefreshTokenRequest, LogoutRequest, RegisterResponse, AuthResponse
from app.utils.security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # check for existing username / email
    existing = (
        db.query(User)
        .filter((User.username == user_in.username) | (User.email == user_in.email))
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hash_password(user_in.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate tokens
    access_token = create_access_token(data={"sub": new_user.username})
    refresh_token = create_refresh_token(data={"sub": new_user.username})
    
    # Calculate expiration time
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    
    # Save refresh token to database
    refresh_token_record = RefreshToken(
        user_id=new_user.id,
        token=refresh_token,
        expires_at=expires_at,
        is_revoked=False
    )
    db.add(refresh_token_record)
    db.commit()
    
    return RegisterResponse(
        user=new_user,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_at=expires_at
    )


@router.post("/login", response_model=AuthResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.username == form_data.username
    ).first()

    if not user or not verify_password(
        form_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    # Save refresh token to database
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    refresh_token_record = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=expires_at,
        is_revoked=False
    )
    db.add(refresh_token_record)
    db.commit()
    
    return AuthResponse(
        user=user,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_at=expires_at
    )

@router.post("/refresh", response_model=Token)
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    username = verify_refresh_token(request.refresh_token)

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(
        User.username == username
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    new_access_token = create_access_token(
        data={"sub": user.username}
    )

    new_refresh_token = create_refresh_token(
        data={"sub": user.username}
    )

    # Save new refresh token to database
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    refresh_token_record = RefreshToken(
        user_id=user.id,
        token=new_refresh_token,
        expires_at=expires_at,
        is_revoked=False
    )
    db.add(refresh_token_record)
    db.commit()

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


@router.get("/me", response_model=UserOut)
def get_current_user_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user's details."""
    return current_user


@router.post("/logout")
def logout(
    request: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke the refresh token to logout."""
    refresh_token_record = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token == request.refresh_token,
            RefreshToken.user_id == current_user.id,
            RefreshToken.is_revoked == False
        )
        .first()
    )

    if refresh_token_record:
        refresh_token_record.is_revoked = True
        db.commit()

    return {
        "success": True,
        "message": "Logout successful"
    }