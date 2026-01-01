from sqlalchemy import Column, Integer, String, ForeignKey, Table, UniqueConstraint
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import relationship
from app.database import Base

# Association table for many-to-many relationship between recordings and artists
recording_artists = Table(
    'recording_artists',
    Base.metadata,
    Column('recording_id', Integer, ForeignKey('recordings.id', ondelete='CASCADE'), primary_key=True),
    Column('artist_id', Integer, ForeignKey('artists.id', ondelete='CASCADE'), primary_key=True),
    Column('artist_order', Integer, nullable=False, default=0, comment="Order of artist in the recording")
)

# Association table for many-to-many relationship between albums and recordings
album_recordings = Table(
    'album_recordings',
    Base.metadata,
    Column('album_id', Integer, ForeignKey('albums.id', ondelete='CASCADE'), primary_key=True),
    Column('recording_id', Integer, ForeignKey('recordings.id', ondelete='CASCADE'), primary_key=True),
    Column('recording_order', Integer, nullable=False, default=0, comment="Order of recording in the album")
)

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
    __table_args__ = (
        UniqueConstraint('composer_id', 'title', name='uq_composer_title'),
        UniqueConstraint('composer_id', 'catalog_number', name='uq_composer_catalog'),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    composer_id = Column(Integer, ForeignKey("composers.id", ondelete="CASCADE"), nullable=False, comment="Composer ID")
    catalog_number = Column(String(50), nullable=True, comment="Catalog number (e.g., BWV 1060, K. 525)")
    sort_order = Column(Integer, nullable=True, comment="Numeric value extracted from catalog number for sorting")
    title = Column(String(200), nullable=False, comment="Composition title")

    # Relationship
    composer = relationship("Composer", back_populates="compositions")

class Artist(Base):
    __tablename__ = "artists"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, comment="Artist name")
    birth_year = Column(Integer, nullable=True, comment="Year of birth")
    death_year = Column(Integer, nullable=True, comment="Year of death")
    nationality = Column(String(50), nullable=True, comment="Country of origin")
    instrument = Column(String(50), nullable=True, comment="Primary instrument")

    # Relationship
    recordings = relationship("Recording", secondary=recording_artists, back_populates="artists")

class Recording(Base):
    __tablename__ = "recordings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    composition_id = Column(Integer, ForeignKey("compositions.id", ondelete="CASCADE"), nullable=False, comment="Composition ID")
    year = Column(Integer, nullable=True, comment="Recording year")

    # Relationships
    composition = relationship("Composition")
    artists = relationship(
        "Artist",
        secondary=recording_artists,
        back_populates="recordings",
        order_by=recording_artists.c.artist_order
    )
    albums = relationship("Album", secondary=album_recordings, back_populates="recordings")

class Album(Base):
    __tablename__ = "albums"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    album_type = Column(String(20), nullable=False, default="LP", comment="Album type (LP or CD)")
    discogs_url = Column(String(255), nullable=True, comment="Discogs URL")
    goclassic_url = Column(String(255), nullable=True, comment="GoClassic URL")
    memo = Column(String(1000), nullable=True, comment="Album memo")

    # Relationships
    recordings = relationship(
        "Recording",
        secondary=album_recordings,
        back_populates="albums",
        order_by=album_recordings.c.recording_order
    )
    images = relationship("AlbumImage", back_populates="album", cascade="all, delete-orphan")
    custom_urls = relationship("AlbumCustomUrl", back_populates="album", cascade="all, delete-orphan", order_by="AlbumCustomUrl.url_order")

class AlbumImage(Base):
    __tablename__ = "album_images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    album_id = Column(Integer, ForeignKey("albums.id", ondelete="CASCADE"), nullable=False, comment="Album ID")
    image_url = Column(MEDIUMTEXT, nullable=False, comment="Image URL or Base64 data")
    is_primary = Column(Integer, nullable=False, default=0, comment="Is primary image (1 or 0)")

    # Relationship
    album = relationship("Album", back_populates="images")

class AlbumCustomUrl(Base):
    __tablename__ = "album_custom_urls"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    album_id = Column(Integer, ForeignKey("albums.id", ondelete="CASCADE"), nullable=False, comment="Album ID")
    url_name = Column(String(100), nullable=False, comment="Display name for the URL")
    url = Column(String(255), nullable=False, comment="The URL")
    url_order = Column(Integer, nullable=False, default=0, comment="Order of URL in the album")

    # Relationship
    album = relationship("Album", back_populates="custom_urls")
