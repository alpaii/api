from pydantic import BaseModel, Field
from typing import Optional

class ComposerBase(BaseModel):
    name: str = Field(..., description="Full name in English", max_length=100)
    short_name: Optional[str] = Field(None, description="Short name or nickname", max_length=50)
    birth_year: Optional[int] = Field(None, description="Year of birth")
    death_year: Optional[int] = Field(None, description="Year of death")
    nationality: Optional[str] = Field(None, description="Country of origin", max_length=50)

class ComposerCreate(ComposerBase):
    pass

class ComposerUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    short_name: Optional[str] = Field(None, max_length=50)
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    nationality: Optional[str] = Field(None, max_length=50)

class ComposerResponse(ComposerBase):
    id: int

    class Config:
        from_attributes = True
