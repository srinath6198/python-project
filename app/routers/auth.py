from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.auth.jwt_handler import create_access_token
from app.schemas import RegisterResponse, Token, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["Authentication"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.execute(
        select(User).where(
            (User.username == user_in.username) | (User.email == user_in.email)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    user = User(
        username=user_in.username,
        email=user_in.email,
        role=user_in.role,
        hashed_password=pwd_context.hash(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    access_token = create_access_token({"sub": user.username, "role": user.role})
    return {
        **UserOut.model_validate(user).model_dump(),
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Authenticate with form fields `username` and `password`."""
    user = db.execute(
        select(User).where(User.username == form_data.username)
    ).scalar_one_or_none()

    if user is None or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token({"sub": user.username, "role": user.role})
    return Token(access_token=access_token, role=user.role)
