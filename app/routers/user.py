from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import ProfileUpdateRequest
from app.auth.dependencies import get_current_user
from sqlalchemy.orm import Session
from app.database import get_db


router = APIRouter(
    prefix="/user",
    tags=["User"]
)


@router.get("/profile")
def get_profile(
    current_user: User = Depends(get_current_user)
):
    return {
        "success": True,
        "message": "User profile fetched successfully",
        "data": {
            "userid": current_user.user_id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "mobile_number": current_user.mobile_number,
            "address": current_user.address,
            "shop": current_user.shopName,
            "role": current_user.role,
            "is_active": current_user.is_active
        }
    }
    
    
@router.get("/profile/{userid}")
def get_profile_by_userid(
    userid: int,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(
        User.user_id == userid
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "success": True,
        "message": "User profile fetched successfully",
        "data": {
            "userid": user.user_id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "mobile_number": user.mobile_number,
            "address": user.address,
            "shop": user.shopName,
            "role": user.role,
            "is_active": user.is_active
        }
    }
    
    
@router.put("/profile/{userid}")
def update_profile(
    userid: int,
    request: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.user_id != userid:
        raise HTTPException(
            status_code=403,
            detail="You cannot update another user's profile"
        )

    user = db.query(User).filter(
        User.user_id == userid
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user.username = request.username
    user.email = request.email
    user.full_name = request.full_name
    user.mobile_number = request.mobile_number
    user.address = request.address
    user.shopName = request.shopName

    db.commit()
    db.refresh(user)

    return {
        "success": True,
        "message": "User profile updated successfully",
        "data": {
            "userid": user.user_id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "mobile_number": user.mobile_number,
            "address": user.address,
            "shop": user.shopName,
            "role": user.role,
            "is_active": user.is_active
        }
    }