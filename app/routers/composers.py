from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import case
from typing import List, Optional
import os
import uuid
from pathlib import Path

from app.database import get_db
from app.models import Composer
from app.schemas import ComposerCreate, ComposerUpdate, ComposerResponse

# Directory for storing uploaded images
UPLOAD_DIR = Path("static/images/composers")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(
    prefix="/composers",
    tags=["composers"]
)

@router.post("/", response_model=ComposerResponse, status_code=status.HTTP_201_CREATED)
def create_composer(composer: ComposerCreate, db: Session = Depends(get_db)):
    """Create a new composer"""
    # Check for duplicate full_name
    existing_full_name = db.query(Composer).filter(Composer.full_name == composer.full_name).first()
    if existing_full_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Composer with name '{composer.full_name}' already exists"
        )

    # Check for duplicate name
    existing_name = db.query(Composer).filter(Composer.name == composer.name).first()
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Composer with short name '{composer.name}' already exists"
        )

    db_composer = Composer(**composer.model_dump())
    db.add(db_composer)
    db.commit()
    db.refresh(db_composer)
    return db_composer

@router.get("/", response_model=List[ComposerResponse])
def read_composers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search composers by full_name, name, or nationality"),
    db: Session = Depends(get_db)
):
    """Get all composers with pagination and optional search, sorted by birth year"""
    query = db.query(Composer)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Composer.full_name.like(search_pattern)) |
            (Composer.name.like(search_pattern)) |
            (Composer.nationality.like(search_pattern))
        )

    # Sort by birth_year ascending (nulls last using CASE), then by name
    # MySQL doesn't support NULLS LAST, so we use CASE to put nulls at the end
    query = query.order_by(
        case((Composer.birth_year.is_(None), 1), else_=0),
        Composer.birth_year.asc(),
        Composer.name.asc()
    )

    composers = query.offset(skip).limit(limit).all()
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

    # Check for duplicate full_name (if updating full_name)
    if "full_name" in update_data and update_data["full_name"]:
        existing_full_name = db.query(Composer).filter(
            Composer.full_name == update_data["full_name"],
            Composer.id != composer_id
        ).first()
        if existing_full_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Composer with name '{update_data['full_name']}' already exists"
            )

    # Check for duplicate name (if updating name)
    if "name" in update_data and update_data["name"]:
        existing_name = db.query(Composer).filter(
            Composer.name == update_data["name"],
            Composer.id != composer_id
        ).first()
        if existing_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Composer with short name '{update_data['name']}' already exists"
            )

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

    # Delete associated image file if it exists
    if db_composer.image_url and db_composer.image_url.startswith("/static/"):
        image_path = Path(db_composer.image_url.lstrip("/"))
        if image_path.exists():
            image_path.unlink()

    db.delete(db_composer)
    db.commit()
    return None

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """Upload a composer image"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )

    # Generate unique filename
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    # Save file
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

    # Return the URL path
    return {"image_url": f"/static/images/composers/{unique_filename}"}
