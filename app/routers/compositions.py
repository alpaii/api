from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import re

from app.database import get_db
from app.models import Composition, Composer, Recording
from app.schemas import CompositionCreate, CompositionUpdate, CompositionResponse

def extract_sort_order(catalog_number: Optional[str]) -> Optional[int]:
    """Extract numeric value from catalog number for sorting"""
    if not catalog_number:
        return None
    # Extract first sequence of digits from the catalog number
    match = re.search(r'\d+', catalog_number)
    if match:
        try:
            return int(match.group())
        except ValueError:
            return None
    return None

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

    # Check for duplicate title within the same composer
    existing_title = db.query(Composition).filter(
        Composition.composer_id == composition.composer_id,
        Composition.title == composition.title
    ).first()
    if existing_title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Composition with title '{composition.title}' already exists for this composer"
        )

    # Check for duplicate catalog number within the same composer
    if composition.catalog_number:
        existing_catalog = db.query(Composition).filter(
            Composition.composer_id == composition.composer_id,
            Composition.catalog_number == composition.catalog_number
        ).first()
        if existing_catalog:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Composition with catalog number '{composition.catalog_number}' already exists for this composer"
            )

    data = composition.model_dump()
    data['sort_order'] = extract_sort_order(data.get('catalog_number'))

    db_composition = Composition(**data)
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
    # Subquery to count recordings per composition
    recording_count_subquery = (
        db.query(
            Recording.composition_id,
            func.count(Recording.id).label('recording_count')
        )
        .group_by(Recording.composition_id)
        .subquery()
    )

    # Main query with left join to get recording count
    query = db.query(
        Composition,
        func.coalesce(recording_count_subquery.c.recording_count, 0).label('recording_count')
    ).outerjoin(
        recording_count_subquery,
        Composition.id == recording_count_subquery.c.composition_id
    )

    if composer_id:
        query = query.filter(Composition.composer_id == composer_id)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Composition.title.like(search_pattern)) |
            (Composition.catalog_number.like(search_pattern))
        )

    # Order by composer_id, then sort_order (nulls last using CASE), then catalog_number
    # MySQL doesn't support NULLS LAST, so we use CASE to put nulls at the end
    from sqlalchemy import case
    query = query.order_by(
        Composition.composer_id.asc(),
        case((Composition.sort_order.is_(None), 1), else_=0),
        Composition.sort_order.asc(),
        Composition.catalog_number.asc()
    )

    results = query.offset(skip).limit(limit).all()

    # Convert results to response format
    compositions = []
    for composition, recording_count in results:
        comp_dict = {
            "id": composition.id,
            "composer_id": composition.composer_id,
            "catalog_number": composition.catalog_number,
            "sort_order": composition.sort_order,
            "title": composition.title,
            "recording_count": recording_count
        }
        compositions.append(comp_dict)

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

    # Check for duplicate title within the same composer
    if "title" in update_data:
        # Determine the composer_id to check against
        composer_id_to_check = update_data.get("composer_id", db_composition.composer_id)

        existing_title = db.query(Composition).filter(
            Composition.composer_id == composer_id_to_check,
            Composition.title == update_data["title"],
            Composition.id != composition_id  # Exclude current composition
        ).first()
        if existing_title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Composition with title '{update_data['title']}' already exists for this composer"
            )

    # Check for duplicate catalog number within the same composer
    if "catalog_number" in update_data and update_data["catalog_number"]:
        # Determine the composer_id to check against
        composer_id_to_check = update_data.get("composer_id", db_composition.composer_id)

        existing_catalog = db.query(Composition).filter(
            Composition.composer_id == composer_id_to_check,
            Composition.catalog_number == update_data["catalog_number"],
            Composition.id != composition_id  # Exclude current composition
        ).first()
        if existing_catalog:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Composition with catalog number '{update_data['catalog_number']}' already exists for this composer"
            )

    # Update sort_order if catalog_number is being updated
    if "catalog_number" in update_data:
        update_data['sort_order'] = extract_sort_order(update_data['catalog_number'])

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
