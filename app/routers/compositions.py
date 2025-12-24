from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import Composition, Composer
from app.schemas import CompositionCreate, CompositionUpdate, CompositionResponse

router = APIRouter(
    prefix="/compositions",
    tags=["compositions"]
)

@router.post("/", response_model=CompositionResponse, status_code=status.HTTP_201_CREATED)
def create_composition(composition: CompositionCreate, db: Session = Depends(get_db)):
    """Create a new composition"""
    # Verify that composer exists
    composer = db.query(Composer).filter(Composer.id == composition.composer_id).first()
    if not composer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Composer with id {composition.composer_id} not found"
        )

    db_composition = Composition(**composition.model_dump())
    db.add(db_composition)
    db.commit()
    db.refresh(db_composition)
    return db_composition

@router.get("/", response_model=List[CompositionResponse])
def read_compositions(
    skip: int = 0,
    limit: int = 100,
    composer_id: Optional[int] = Query(None, description="Filter by composer ID"),
    search: Optional[str] = Query(None, description="Search by title or catalog number"),
    db: Session = Depends(get_db)
):
    """Get all compositions with pagination and optional filters"""
    query = db.query(Composition)

    if composer_id:
        query = query.filter(Composition.composer_id == composer_id)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Composition.title.like(search_pattern)) |
            (Composition.catalog_number.like(search_pattern))
        )

    # Order by composer_id, then catalog_number
    query = query.order_by(
        Composition.composer_id.asc(),
        Composition.catalog_number.asc()
    )

    compositions = query.offset(skip).limit(limit).all()
    return compositions

@router.get("/{composition_id}", response_model=CompositionResponse)
def read_composition(composition_id: int, db: Session = Depends(get_db)):
    """Get a specific composition by ID"""
    composition = db.query(Composition).filter(Composition.id == composition_id).first()
    if composition is None:
        raise HTTPException(status_code=404, detail="Composition not found")
    return composition

@router.put("/{composition_id}", response_model=CompositionResponse)
def update_composition(composition_id: int, composition: CompositionUpdate, db: Session = Depends(get_db)):
    """Update a composition"""
    db_composition = db.query(Composition).filter(Composition.id == composition_id).first()
    if db_composition is None:
        raise HTTPException(status_code=404, detail="Composition not found")

    update_data = composition.model_dump(exclude_unset=True)

    # Verify composer exists if updating composer_id
    if "composer_id" in update_data and update_data["composer_id"]:
        composer = db.query(Composer).filter(Composer.id == update_data["composer_id"]).first()
        if not composer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Composer with id {update_data['composer_id']} not found"
            )

    for key, value in update_data.items():
        setattr(db_composition, key, value)

    db.commit()
    db.refresh(db_composition)
    return db_composition

@router.delete("/{composition_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_composition(composition_id: int, db: Session = Depends(get_db)):
    """Delete a composition"""
    db_composition = db.query(Composition).filter(Composition.id == composition_id).first()
    if db_composition is None:
        raise HTTPException(status_code=404, detail="Composition not found")

    db.delete(db_composition)
    db.commit()
    return None
