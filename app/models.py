from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Composer(Base):
    __tablename__ = "composers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name = Column(String(100), nullable=False, unique=True, comment="Full name in English")
    name = Column(String(50), nullable=False, unique=True, comment="Short name or nickname")
    birth_year = Column(Integer, nullable=True, comment="Year of birth")
    death_year = Column(Integer, nullable=True, comment="Year of death")
    nationality = Column(String(50), nullable=True, comment="Country of origin")
    image_url = Column(String(255), nullable=True, comment="Profile image URL")

    # Relationship
    compositions = relationship("Composition", back_populates="composer", cascade="all, delete-orphan")

class Composition(Base):
    __tablename__ = "compositions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    composer_id = Column(Integer, ForeignKey("composers.id", ondelete="CASCADE"), nullable=False, comment="Composer ID")
    catalog_number = Column(String(50), nullable=True, comment="Catalog number (e.g., BWV 1060, K. 525)")
    title = Column(String(200), nullable=False, comment="Composition title")

    # Relationship
    composer = relationship("Composer", back_populates="compositions")
