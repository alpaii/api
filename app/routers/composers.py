from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Composer
from app.schemas import ComposerCreate, ComposerUpdate, ComposerResponse

router = APIRouter(
    prefix="/composers",
    tags=["composers"]
)

@router.post("/", response_model=ComposerResponse, status_code=status.HTTP_201_CREATED)
def create_composer(composer: ComposerCreate, db: Session = Depends(get_db)):
    """Create a new composer"""
    db_composer = Composer(**composer.model_dump())
    db.add(db_composer)
    db.commit()
    db.refresh(db_composer)
    return db_composer

@router.get("/", response_model=List[ComposerResponse])
def read_composers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all composers with pagination"""
    composers = db.query(Composer).offset(skip).limit(limit).all()
    return composers

@router.get("/{composer_id}", response_model=ComposerResponse)
def read_composer(composer_id: int, db: Session = Depends(get_db)):
    """Get a specific composer by ID"""
    composer = db.query(Composer).filter(Composer.id == composer_id).first()
    if composer is None:
        raise HTTPException(status_code=404, detail="Composer not found")
    return composer

@router.put("/{composer_id}", response_model=ComposerResponse)
def update_composer(composer_id: int, composer: ComposerUpdate, db: Session = Depends(get_db)):
    """Update a composer"""
    db_composer = db.query(Composer).filter(Composer.id == composer_id).first()
    if db_composer is None:
        raise HTTPException(status_code=404, detail="Composer not found")

    update_data = composer.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_composer, key, value)

    db.commit()
    db.refresh(db_composer)
    return db_composer

@router.delete("/{composer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_composer(composer_id: int, db: Session = Depends(get_db)):
    """Delete a composer"""
    db_composer = db.query(Composer).filter(Composer.id == composer_id).first()
    if db_composer is None:
        raise HTTPException(status_code=404, detail="Composer not found")

    db.delete(db_composer)
    db.commit()
    return None
