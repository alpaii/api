from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.database import get_db
from app.models import Artist, Recording, recording_artists
from app.schemas import ArtistCreate, ArtistUpdate, ArtistResponse

router = APIRouter(
    prefix="/artists",
    tags=["artists"]
)

@router.post("/", response_model=ArtistResponse, status_code=status.HTTP_201_CREATED)
def create_artist(artist: ArtistCreate, db: Session = Depends(get_db)):
    """Create a new artist"""
    # Check for duplicate name
    existing_name = db.query(Artist).filter(Artist.name == artist.name).first()
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Artist with name '{artist.name}' already exists"
        )

    db_artist = Artist(**artist.model_dump())
    db.add(db_artist)
    db.commit()
    db.refresh(db_artist)
    return db_artist

@router.get("/", response_model=List[ArtistResponse])
def read_artists(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search artists by name, nationality, or instrument"),
    db: Session = Depends(get_db)
):
    """Get all artists with pagination and optional search, sorted by name"""
    # Subquery to count recordings per artist
    recording_count_subquery = (
        db.query(
            recording_artists.c.artist_id,
            func.count(recording_artists.c.recording_id).label('recording_count')
        )
        .group_by(recording_artists.c.artist_id)
        .subquery()
    )

    # Main query with left join to get recording count
    query = db.query(
        Artist,
        func.coalesce(recording_count_subquery.c.recording_count, 0).label('recording_count')
    ).outerjoin(
        recording_count_subquery,
        Artist.id == recording_count_subquery.c.artist_id
    )

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Artist.name.like(search_pattern)) |
            (Artist.nationality.like(search_pattern)) |
            (Artist.instrument.like(search_pattern))
        )

    # Sort by name ascending
    query = query.order_by(Artist.name.asc())

    results = query.offset(skip).limit(limit).all()

    # Convert results to response format
    artists = []
    for artist, recording_count in results:
        artist_dict = {
            "id": artist.id,
            "name": artist.name,
            "birth_year": artist.birth_year,
            "death_year": artist.death_year,
            "nationality": artist.nationality,
            "instrument": artist.instrument,
            "recording_count": recording_count
        }
        artists.append(artist_dict)

    return artists

@router.get("/{artist_id}", response_model=ArtistResponse)
def read_artist(artist_id: int, db: Session = Depends(get_db)):
    """Get a specific artist by ID"""
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    return artist

@router.put("/{artist_id}", response_model=ArtistResponse)
def update_artist(artist_id: int, artist: ArtistUpdate, db: Session = Depends(get_db)):
    """Update an artist"""
    db_artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if db_artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")

    update_data = artist.model_dump(exclude_unset=True)

    # Check for duplicate name (if updating name)
    if "name" in update_data and update_data["name"]:
        existing_name = db.query(Artist).filter(
            Artist.name == update_data["name"],
            Artist.id != artist_id
        ).first()
        if existing_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Artist with name '{update_data['name']}' already exists"
            )

    for key, value in update_data.items():
        setattr(db_artist, key, value)

    db.commit()
    db.refresh(db_artist)
    return db_artist

@router.delete("/{artist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_artist(artist_id: int, db: Session = Depends(get_db)):
    """Delete an artist"""
    db_artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if db_artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")

    db.delete(db_artist)
    db.commit()
    return None
