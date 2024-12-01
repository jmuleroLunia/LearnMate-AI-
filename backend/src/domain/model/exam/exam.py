import uuid
from typing import Optional, List

from pydantic import BaseModel, Field

from src import schemas


class Answer(BaseModel):
    text: str = Field(default=None, description="Answer text")


class Question(BaseModel):
    text: str = Field(default=None, description="Question text")
    answers: list[Answer] = Field(default=None, description="List of possible answers")


class Exam(BaseModel):
    """Exam Model"""
    date: Optional[str] = Field(default=None, description="Exam date")
    subject_id: Optional[int] = Field(default=None, description="Exam subject")
    questions: list[Question] = Field(default=None, description="List of exam questions")

class QuestionWithSubject(BaseModel):
    question: Question
    subject_id: int

# Define a response model to include both exams and errors
class BatchExamResponse(BaseModel):
    exams: List[schemas.ExamOut]
    errors: List[str]