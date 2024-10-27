# app/schemas.py
from typing import Optional, List

from pydantic import BaseModel, HttpUrl

# Esquemas para los Recursos
class ResourceBase(BaseModel):
    title: str
    url: Optional[HttpUrl] = None
    type: str  # "Libro", "Enlace Web" o "Apunte"
    notes: Optional[str] = None

class ResourceCreate(ResourceBase):
    pass

class Resource(ResourceBase):
    id: int
    subject_id: int
    file_path: Optional[str] = None

    class Config:
        orm_mode = True

# Esquemas para las Asignaturas
class SubjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class SubjectCreate(SubjectBase):
    pass

class SubjectOut(SubjectBase):
    id: int
    resources: List[Resource] = []

    class Config:
        orm_mode = True