from sqlalchemy import Column, Integer, String
from app.database import Base

class Composer(Base):
    __tablename__ = "composers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, comment="Full name in English")
    short_name = Column(String(50), nullable=False, unique=True, comment="Short name or nickname")
    birth_year = Column(Integer, nullable=True, comment="Year of birth")
    death_year = Column(Integer, nullable=True, comment="Year of death")
    nationality = Column(String(50), nullable=True, comment="Country of origin")
