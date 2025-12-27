from pydantic import BaseModel, Field
from typing import Optional, List

# Composition schemas
class CompositionBase(BaseModel):
    composer_id: int = Field(..., description="Composer ID")
    catalog_number: Optional[str] = Field(None, description="Catalog number (e.g., BWV 1060, K. 525)", max_length=50)
    title: str = Field(..., description="Composition title", max_length=200)

class CompositionCreate(CompositionBase):
    pass

class CompositionUpdate(BaseModel):
    composer_id: Optional[int] = None
    catalog_number: Optional[str] = Field(None, max_length=50)
    title: Optional[str] = Field(None, max_length=200)

    class Config:
        min_properties = 1

class CompositionResponse(CompositionBase):
    id: int
    sort_order: Optional[int] = None
    recording_count: int = Field(default=0, description="Number of recordings")

    class Config:
        from_attributes = True

# Composer schemas
class ComposerBase(BaseModel):
    full_name: str = Field(..., description="Full name in English", max_length=100)
    name: str = Field(..., description="Short name or nickname", max_length=50)
    birth_year: Optional[int] = Field(None, description="Year of birth")
    death_year: Optional[int] = Field(None, description="Year of death")
    nationality: Optional[str] = Field(None, description="Country of origin", max_length=50)
    image_url: Optional[str] = Field(None, description="Profile image URL", max_length=255)

class ComposerCreate(ComposerBase):
    pass

class ComposerUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    name: Optional[str] = Field(None, max_length=50)
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    nationality: Optional[str] = Field(None, max_length=50)
    image_url: Optional[str] = Field(None, max_length=255)

    class Config:
        # At least one field must be provided for update
        min_properties = 1

class ComposerResponse(ComposerBase):
    id: int
    composition_count: int = Field(default=0, description="Number of compositions")

    class Config:
        from_attributes = True

class ComposerWithCompositions(ComposerResponse):
    compositions: List[CompositionResponse] = []

    class Config:
        from_attributes = True

# Artist schemas
class ArtistBase(BaseModel):
    name: str = Field(..., description="Artist name", max_length=100)
    birth_year: Optional[int] = Field(None, description="Year of birth")
    death_year: Optional[int] = Field(None, description="Year of death")
    nationality: Optional[str] = Field(None, description="Country of origin", max_length=50)
    instrument: Optional[str] = Field(None, description="Primary instrument", max_length=50)

class ArtistCreate(ArtistBase):
    pass

class ArtistUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    nationality: Optional[str] = Field(None, max_length=50)
    instrument: Optional[str] = Field(None, max_length=50)

    class Config:
        min_properties = 1

class ArtistResponse(ArtistBase):
    id: int
    recording_count: int = Field(default=0, description="Number of recordings")

    class Config:
        from_attributes = True

# Recording schemas
class RecordingBase(BaseModel):
    composition_id: int = Field(..., description="Composition ID")
    year: Optional[int] = Field(None, description="Recording year")

class RecordingCreate(RecordingBase):
    artist_ids: List[int] = Field(..., description="List of artist IDs")

class RecordingUpdate(BaseModel):
    composition_id: Optional[int] = None
    year: Optional[int] = None
    artist_ids: Optional[List[int]] = None

    class Config:
        min_properties = 1

class RecordingResponse(RecordingBase):
    id: int
    artists: List[ArtistResponse] = []

    class Config:
        from_attributes = True

# Album Image schemas
class AlbumImageBase(BaseModel):
    image_url: str = Field(..., description="Image URL or Base64 data")
    is_primary: int = Field(0, description="Is primary image (1 or 0)")

class AlbumImageResponse(AlbumImageBase):
    id: int
    album_id: int

    class Config:
        from_attributes = True

# Album schemas
class AlbumBase(BaseModel):
    title: str = Field(..., description="Album title", max_length=200)
    album_type: str = Field(default="LP", description="Album type (LP or CD)", max_length=20)

class AlbumCreate(AlbumBase):
    recording_ids: List[int] = Field(..., description="List of recording IDs")
    image_urls: List[str] = Field(default=[], description="List of image URLs")
    primary_image_index: Optional[int] = Field(None, description="Index of primary image (0-based)")

class AlbumUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    album_type: Optional[str] = Field(None, max_length=20)
    recording_ids: Optional[List[int]] = None
    image_urls: Optional[List[str]] = None
    primary_image_index: Optional[int] = None

    class Config:
        min_properties = 1

class AlbumResponse(AlbumBase):
    id: int
    recordings: List[RecordingResponse] = []
    images: List[AlbumImageResponse] = []

    class Config:
        from_attributes = True
