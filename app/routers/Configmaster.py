from fastapi import APIRouter, Depends, Query 
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.Configmaster import (
    ConfigCreate,
    ConfigUpdate,
    ConfigOut
)
from app.models.Configmaster import CompanyConfig

router = APIRouter(
    prefix="/api/companies/{company_id}/configs",
    tags=["Company Config"]
)

@router.post("/", response_model=ConfigOut)
def create_config(
    company_id: int,
    request: ConfigCreate,
    db: Session = Depends(get_db)
):
    # Check duplicate config
    existing_config = (
        db.query(CompanyConfig)
        .filter(
            CompanyConfig.company_id == company_id,
            CompanyConfig.config_type == request.config_type,
            CompanyConfig.config_name == request.config_name
        )
        .first()
    )

    if existing_config:
        raise HTTPException(
            status_code=409,
            detail="Config already exists for this company"
        )

    # Create config
    config = CompanyConfig(
        company_id=company_id,
        config_type=request.config_type,
        config_name=request.config_name,
        is_active=request.is_active
    )

    db.add(config)
    db.commit()
    db.refresh(config)

    # IMPORTANT: return the created object
    return config

@router.get("/", response_model=list[ConfigOut])
def get_configs(
    company_id: int,
    config_type: str | None = Query(default=None),
    db: Session = Depends(get_db)
):
    query = db.query(CompanyConfig).filter(
        CompanyConfig.company_id == company_id
    )

    if config_type is not None:
        query = query.filter(CompanyConfig.config_type == config_type)

    return query.all()


@router.get("/{config_id}", response_model=ConfigOut)
def get_config(
    company_id: int,
    config_id: int,
    db: Session = Depends(get_db)
):
    config = (
        db.query(CompanyConfig)
        .filter(
            CompanyConfig.company_id == company_id,
            CompanyConfig.config_id == config_id
        )
        .first()
    )

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Config not found"
        )

    return config


@router.put("/{config_id}", response_model=ConfigOut)
def update_config(
    company_id: int,
    config_id: int,
    request: ConfigUpdate,
    db: Session = Depends(get_db)
):
    config = (
        db.query(CompanyConfig)
        .filter(
            CompanyConfig.company_id == company_id,
            CompanyConfig.config_id == config_id
        )
        .first()
    )

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Config not found"
        )

    duplicate = (
        db.query(CompanyConfig)
        .filter(
            CompanyConfig.company_id == company_id,
            CompanyConfig.config_type == request.config_type,
            CompanyConfig.config_name == request.config_name,
            CompanyConfig.config_id != config_id
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Config already exists for this company"
        )

    config.config_type = request.config_type
    config.config_name = request.config_name
    config.is_active = request.is_active

    db.commit()
    db.refresh(config)
    return config


@router.delete("/{config_id}")
def delete_config(
    company_id: int,
    config_id: int,
    db: Session = Depends(get_db)
):
    config = (
        db.query(CompanyConfig)
        .filter(
            CompanyConfig.company_id == company_id,
            CompanyConfig.config_id == config_id
        )
        .first()
    )

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Config not found"
        )

    db.delete(config)
    db.commit()
    return {"message": "Config deleted successfully"}


@router.patch("/{config_id}/status")
def update_config_status(
    company_id: int,
    config_id: int,
    is_active: bool,
    db: Session = Depends(get_db)
):
    config = (
        db.query(CompanyConfig)
        .filter(
            CompanyConfig.company_id == company_id,
            CompanyConfig.config_id == config_id
        )
        .first()
    )

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Config not found"
        )

    config.is_active = is_active
    db.commit()
    db.refresh(config)
    return config