# app/models.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from src.database import Base

class Subject(Base):
    __tablename__ = 'subjects'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)

    resources = relationship("Resource", back_populates="subject", cascade="all, delete-orphan")

class Resource(Base):
    __tablename__ = 'resources'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=True)
    type = Column(String, nullable=False)  # "Libro", "Enlace Web", "Apunte"
    notes = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    subject_id = Column(Integer, ForeignKey('subjects.id'))

    subject = relationship("Subject", back_populates="resources")