from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import case
from typing import List, Optional

from app.database import get_db
from app.models import Recording, Artist, Composition
from app.schemas import RecordingCreate, RecordingUpdate, RecordingResponse

router = APIRouter(
    prefix="/recordings",
    tags=["recordings"]
)

@router.post("/", response_model=RecordingResponse, status_code=status.HTTP_201_CREATED)
def create_recording(recording: RecordingCreate, db: Session = Depends(get_db)):
    """Create a new recording"""
    # Verify composition exists
    composition = db.query(Composition).filter(Composition.id == recording.composition_id).first()
    if not composition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Composition with id {recording.composition_id} not found"
        )

    # Verify all artists exist
    artists = db.query(Artist).filter(Artist.id.in_(recording.artist_ids)).all()
    if len(artists) != len(recording.artist_ids):
        found_ids = {a.id for a in artists}
        missing_ids = set(recording.artist_ids) - found_ids
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artists with ids {missing_ids} not found"
        )

    # Create recording
    db_recording = Recording(
        composition_id=recording.composition_id,
        year=recording.year
    )
    db.add(db_recording)
    db.flush()  # Get the recording ID before adding artists

    # Add artists in the specified order
    from app.models import recording_artists
    for order, artist_id in enumerate(recording.artist_ids):
        db.execute(
            recording_artists.insert().values(
                recording_id=db_recording.id,
                artist_id=artist_id,
                artist_order=order
            )
        )

    db.commit()
    db.refresh(db_recording)
    return db_recording

@router.get("/", response_model=List[RecordingResponse])
def read_recordings(
    skip: int = 0,
    limit: int = 100,
    composition_id: Optional[int] = Query(None, description="Filter by composition ID"),
    composer_id: Optional[int] = Query(None, description="Filter by composer ID"),
    artist_id: Optional[int] = Query(None, description="Filter by artist ID"),
    db: Session = Depends(get_db)
):
    """Get all recordings with pagination and optional filters"""
    query = db.query(Recording).options(joinedload(Recording.artists))

    if composition_id:
        query = query.filter(Recording.composition_id == composition_id)

    if composer_id:
        query = query.join(Composition).filter(Composition.composer_id == composer_id)

    if artist_id:
        query = query.join(Recording.artists).filter(Artist.id == artist_id)

    # Sort by year descending (most recent first), nulls last
    query = query.order_by(
        case((Recording.year.is_(None), 1), else_=0),
        Recording.year.desc(),
        Recording.id.desc()
    )

    recordings = query.offset(skip).limit(limit).all()
    return recordings

@router.get("/{recording_id}", response_model=RecordingResponse)
def read_recording(recording_id: int, db: Session = Depends(get_db)):
    """Get a specific recording by ID"""
    recording = db.query(Recording).options(joinedload(Recording.artists)).filter(Recording.id == recording_id).first()
    if recording is None:
        raise HTTPException(status_code=404, detail="Recording not found")
    return recording

@router.put("/{recording_id}", response_model=RecordingResponse)
def update_recording(recording_id: int, recording: RecordingUpdate, db: Session = Depends(get_db)):
    """Update a recording"""
    db_recording = db.query(Recording).options(joinedload(Recording.artists)).filter(Recording.id == recording_id).first()
    if db_recording is None:
        raise HTTPException(status_code=404, detail="Recording not found")

    update_data = recording.model_dump(exclude_unset=True)

    # Handle artist_ids separately
    if "artist_ids" in update_data:
        artist_ids = update_data.pop("artist_ids")
        if artist_ids is not None:
            # Verify all artists exist
            artists = db.query(Artist).filter(Artist.id.in_(artist_ids)).all()
            if len(artists) != len(artist_ids):
                found_ids = {a.id for a in artists}
                missing_ids = set(artist_ids) - found_ids
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Artists with ids {missing_ids} not found"
                )

            # Delete existing artist associations
            from app.models import recording_artists
            db.execute(
                recording_artists.delete().where(
                    recording_artists.c.recording_id == recording_id
                )
            )

            # Add artists in the new order
            for order, artist_id in enumerate(artist_ids):
                db.execute(
                    recording_artists.insert().values(
                        recording_id=recording_id,
                        artist_id=artist_id,
                        artist_order=order
                    )
                )

    # Verify composition if being updated
    if "composition_id" in update_data and update_data["composition_id"] is not None:
        composition = db.query(Composition).filter(Composition.id == update_data["composition_id"]).first()
        if not composition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Composition with id {update_data['composition_id']} not found"
            )

    # Update other fields
    for key, value in update_data.items():
        setattr(db_recording, key, value)

    db.commit()
    db.refresh(db_recording)
    return db_recording

@router.delete("/{recording_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recording(recording_id: int, db: Session = Depends(get_db)):
    """Delete a recording"""
    db_recording = db.query(Recording).filter(Recording.id == recording_id).first()
    if db_recording is None:
        raise HTTPException(status_code=404, detail="Recording not found")

    db.delete(db_recording)
    db.commit()
    return None
