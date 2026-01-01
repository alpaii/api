from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.database import get_db
from app.models import Album, AlbumImage, Recording, AlbumCustomUrl
from app.schemas import AlbumCreate, AlbumUpdate, AlbumResponse

router = APIRouter(
    prefix="/albums",
    tags=["albums"]
)

@router.post("/", response_model=AlbumResponse, status_code=status.HTTP_201_CREATED)
def create_album(album: AlbumCreate, db: Session = Depends(get_db)):
    """Create a new album"""
    # Verify all recordings exist
    if album.recording_ids:
        recordings = db.query(Recording).filter(Recording.id.in_(album.recording_ids)).all()
        if len(recordings) != len(album.recording_ids):
            found_ids = {r.id for r in recordings}
            missing_ids = set(album.recording_ids) - found_ids
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recordings with ids {missing_ids} not found"
            )
    else:
        recordings = []

    # Create album
    db_album = Album(
        album_type=album.album_type,
        discogs_url=album.discogs_url,
        goclassic_url=album.goclassic_url,
        memo=album.memo
    )
    db.add(db_album)
    db.flush()  # Get album ID before adding recordings, images, and custom URLs

    # Add recordings in the specified order
    if album.recording_ids:
        from app.models import album_recordings
        for order, recording_id in enumerate(album.recording_ids):
            db.execute(
                album_recordings.insert().values(
                    album_id=db_album.id,
                    recording_id=recording_id,
                    recording_order=order
                )
            )

    # Add images
    if album.image_urls:
        for idx, image_url in enumerate(album.image_urls):
            is_primary = 1 if album.primary_image_index is not None and idx == album.primary_image_index else 0
            db_image = AlbumImage(
                album_id=db_album.id,
                image_url=image_url,
                is_primary=is_primary
            )
            db.add(db_image)

    # Add custom URLs
    if album.custom_urls:
        for custom_url_data in album.custom_urls:
            # Handle both dict and Pydantic model
            if isinstance(custom_url_data, dict):
                url_name = custom_url_data.get("url_name")
                url = custom_url_data.get("url")
                url_order = custom_url_data.get("url_order", 0)
            else:
                url_name = custom_url_data.url_name
                url = custom_url_data.url
                url_order = custom_url_data.url_order

            db_custom_url = AlbumCustomUrl(
                album_id=db_album.id,
                url_name=url_name,
                url=url,
                url_order=url_order
            )
            db.add(db_custom_url)

    db.commit()
    db.refresh(db_album)
    return db_album

@router.get("/", response_model=List[AlbumResponse])
def read_albums(
    skip: int = 0,
    limit: int = 100,
    album_type: Optional[str] = Query(None, description="Filter by album type (LP or CD)"),
    db: Session = Depends(get_db)
):
    """Get all albums with pagination and optional filters"""
    query = db.query(Album).options(
        joinedload(Album.recordings).joinedload(Recording.artists),
        joinedload(Album.images),
        joinedload(Album.custom_urls)
    )

    if album_type:
        query = query.filter(Album.album_type == album_type)

    # Sort by ID descending (most recent first)
    query = query.order_by(Album.id.desc())

    albums = query.offset(skip).limit(limit).all()
    return albums

@router.get("/{album_id}", response_model=AlbumResponse)
def read_album(album_id: int, db: Session = Depends(get_db)):
    """Get a specific album by ID"""
    album = db.query(Album).options(
        joinedload(Album.recordings).joinedload(Recording.artists),
        joinedload(Album.images),
        joinedload(Album.custom_urls)
    ).filter(Album.id == album_id).first()

    if album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    return album

@router.put("/{album_id}", response_model=AlbumResponse)
def update_album(album_id: int, album: AlbumUpdate, db: Session = Depends(get_db)):
    """Update an album"""
    db_album = db.query(Album).options(
        joinedload(Album.recordings).joinedload(Recording.artists),
        joinedload(Album.images),
        joinedload(Album.custom_urls)
    ).filter(Album.id == album_id).first()

    if db_album is None:
        raise HTTPException(status_code=404, detail="Album not found")

    update_data = album.model_dump(exclude_unset=True)

    # Handle recording_ids separately
    if "recording_ids" in update_data:
        recording_ids = update_data.pop("recording_ids")
        if recording_ids is not None:
            # Verify all recordings exist
            recordings = db.query(Recording).filter(Recording.id.in_(recording_ids)).all()
            if len(recordings) != len(recording_ids):
                found_ids = {r.id for r in recordings}
                missing_ids = set(recording_ids) - found_ids
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Recordings with ids {missing_ids} not found"
                )

            # Delete existing recording associations
            from app.models import album_recordings
            db.execute(
                album_recordings.delete().where(
                    album_recordings.c.album_id == album_id
                )
            )

            # Add recordings in the new order
            for order, recording_id in enumerate(recording_ids):
                db.execute(
                    album_recordings.insert().values(
                        album_id=album_id,
                        recording_id=recording_id,
                        recording_order=order
                    )
                )

    # Handle image_urls separately
    if "image_urls" in update_data:
        image_urls = update_data.pop("image_urls")
        primary_image_index = update_data.pop("primary_image_index", None)

        if image_urls is not None:
            # Remove existing images
            db.query(AlbumImage).filter(AlbumImage.album_id == album_id).delete()

            # Add new images
            for idx, image_url in enumerate(image_urls):
                is_primary = 1 if primary_image_index is not None and idx == primary_image_index else 0
                db_image = AlbumImage(
                    album_id=album_id,
                    image_url=image_url,
                    is_primary=is_primary
                )
                db.add(db_image)
    elif "primary_image_index" in update_data:
        update_data.pop("primary_image_index")

    # Handle custom_urls separately
    if "custom_urls" in update_data:
        custom_urls = update_data.pop("custom_urls")
        if custom_urls is not None:
            # Remove existing custom URLs
            db.query(AlbumCustomUrl).filter(AlbumCustomUrl.album_id == album_id).delete()

            # Add new custom URLs
            for custom_url_data in custom_urls:
                # Handle both dict and Pydantic model
                if isinstance(custom_url_data, dict):
                    url_name = custom_url_data.get("url_name")
                    url = custom_url_data.get("url")
                    url_order = custom_url_data.get("url_order", 0)
                else:
                    url_name = custom_url_data.url_name
                    url = custom_url_data.url
                    url_order = custom_url_data.url_order

                db_custom_url = AlbumCustomUrl(
                    album_id=album_id,
                    url_name=url_name,
                    url=url,
                    url_order=url_order
                )
                db.add(db_custom_url)

    # Update other fields
    for key, value in update_data.items():
        setattr(db_album, key, value)

    db.commit()
    db.refresh(db_album)
    return db_album

@router.delete("/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_album(album_id: int, db: Session = Depends(get_db)):
    """Delete an album"""
    db_album = db.query(Album).filter(Album.id == album_id).first()
    if db_album is None:
        raise HTTPException(status_code=404, detail="Album not found")

    db.delete(db_album)
    db.commit()
    return None
