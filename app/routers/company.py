from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.authorization import require_super_admin
from app.database import get_db
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyOut, CompanyUpdate


router = APIRouter(prefix="/api/companies", tags=["Company Master"])


def get_company(company_id: int, db: Session) -> Company:
    company = db.query(Company).filter(Company.company_id == company_id).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


def ensure_unique_company(db: Session, code: str, email: str | None, company_id: int | None = None):
    query = db.query(Company).filter(Company.company_code == code)
    if company_id is not None:
        query = query.filter(Company.company_id != company_id)
    if query.first():
        raise HTTPException(status_code=409, detail="Company code already exists")

    if email:
        query = db.query(Company).filter(Company.email == email)
        if company_id is not None:
            query = query.filter(Company.company_id != company_id)
        if query.first():
            raise HTTPException(status_code=409, detail="Company email already exists")


@router.post("", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(
    request: CompanyCreate,
    current_user=Depends(require_super_admin()),
    db: Session = Depends(get_db),
):
    ensure_unique_company(db, request.company_code, request.email)
    company = Company(**request.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("", response_model=list[CompanyOut])
def list_companies(
    current_user=Depends(require_super_admin()),
    db: Session = Depends(get_db),
):
    return db.query(Company).order_by(Company.company_id).all()


@router.get("/{company_id}", response_model=CompanyOut)
def get_company_by_id(
    company_id: int,
    current_user=Depends(require_super_admin()),
    db: Session = Depends(get_db),
):
    return get_company(company_id, db)


@router.put("/{company_id}", response_model=CompanyOut)
def update_company(
    company_id: int,
    request: CompanyUpdate,
    current_user=Depends(require_super_admin()),
    db: Session = Depends(get_db),
):
    company = get_company(company_id, db)
    ensure_unique_company(db, request.company_code, request.email, company_id)
    for field, value in request.model_dump().items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}")
def delete_company(
    company_id: int,
    current_user=Depends(require_super_admin()),
    db: Session = Depends(get_db),
):
    company = get_company(company_id, db)
    db.delete(company)
    db.commit()
    return {"success": True, "message": "Company deleted successfully"}