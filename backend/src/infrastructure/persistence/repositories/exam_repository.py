from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.model.exam.exam import Exam, Question, Answer
from src.infrastructure.persistence.models.exam import ExamModel, QuestionModel, AnswerModel

class ExamRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, exam: Exam) -> UUID:
        exam_model = ExamModel(
            date=datetime.strptime(exam.date, "%Y-%m-%d") if exam.date else None,
            subject_id=exam.subject_id  # Usamos el subject_id del exam
        )

        for question in exam.questions:
            question_model = QuestionModel(text=question.text)

            for answer in question.answers:
                answer_model = AnswerModel(text=answer.text)
                question_model.answers.append(answer_model)

            exam_model.questions.append(question_model)

        self.session.add(exam_model)
        self.session.commit()

        return exam_model.id


    def get_by_id(self, exam_id: UUID) -> Optional[Exam]:
        exam_model = self.session.query(ExamModel).filter(
            ExamModel.id == exam_id
        ).first()

        if not exam_model:
            return None

        return Exam(
            date=exam_model.date.strftime("%Y-%m-%d") if exam_model.date else None,
            subject_id=exam_model.subject_id,
            questions=[
                Question(
                    text=question.text,
                    answers=[
                        Answer(text=answer.text)
                        for answer in question.answers
                    ]
                )
                for question in exam_model.questions
            ]
        )