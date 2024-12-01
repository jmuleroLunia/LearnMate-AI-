from datetime import datetime

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from src.database import Base


class ExamModel(Base):
    __tablename__ = 'exams'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime, nullable=True)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    subject = relationship("Subject", back_populates="exams")
    questions = relationship("QuestionModel", back_populates="exam", cascade="all, delete-orphan")


class QuestionModel(Base):
    __tablename__ = 'questions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(Text, nullable=False)
    exam_id = Column(UUID(as_uuid=True), ForeignKey('exams.id'))

    exam = relationship("ExamModel", back_populates="questions")
    answers = relationship("AnswerModel", back_populates="question", cascade="all, delete-orphan")


class AnswerModel(Base):
    __tablename__ = 'answers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(Text, nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.id'))

    question = relationship("QuestionModel", back_populates="answers")

