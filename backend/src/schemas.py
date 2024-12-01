# app/schemas.py
from datetime import datetime
from typing import Optional, List
from uuid import UUID

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
    status: str  # Nuevo campo 'status'

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


class AnswerBase(BaseModel):
    text: str


class AnswerCreate(AnswerBase):
    pass


class AnswerOut(AnswerBase):
    id: UUID
    question_id: UUID

    class Config:
        from_attributes = True


class QuestionBase(BaseModel):
    text: str


class QuestionCreate(QuestionBase):
    answers: List[AnswerCreate]


class QuestionOut(QuestionBase):
    id: UUID
    exam_id: UUID
    answers: List[AnswerOut]

    class Config:
        from_attributes = True


class ExamBase(BaseModel):
    date: Optional[datetime] = None


class ExamCreate(ExamBase):
    questions: Optional[List[QuestionCreate]] = None


class ExamOut(ExamBase):
    id: UUID
    subject_id: int
    questions: List[QuestionOut]
    created_at: datetime

    class Config:
        from_attributes = True