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
