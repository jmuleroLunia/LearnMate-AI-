import random
from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session
from src import models

def generate_mock_exam(subject_id: int, num_questions: int, db: Session):
    # Obtener todos los exámenes de la asignatura
    exams = db.query(models.ExamModel).filter(models.ExamModel.subject_id == subject_id).all()

    if not exams:
        raise ValueError("No se encontraron exámenes para la asignatura dada.")

    # Recopilar todas las preguntas de estos exámenes
    all_questions = []
    for exam in exams:
        all_questions.extend(exam.questions)

    if not all_questions:
        raise ValueError("No se encontraron preguntas para la asignatura dada.")

    # Seleccionar aleatoriamente el número deseado de preguntas
    selected_questions = random.sample(all_questions, min(num_questions, len(all_questions)))

    # Generar campos necesarios para el examen ficticio
    exam_id = uuid4()
    created_at = datetime.utcnow()

    # Construir la estructura del examen ficticio
    mock_exam = {
        "id": exam_id,
        "created_at": created_at,
        "subject_id": subject_id,
        "questions": []
    }

    for question in selected_questions:
        question_id = question.id  # Usando el ID existente de la pregunta
        question_data = {
            "id": question_id,
            "exam_id": exam_id,  # Asociar con el ID del examen ficticio
            "text": question.text,
            "answers": []
        }

        for answer in question.answers:
            answer_data = {
                "id": answer.id,
                "question_id": question_id,  # Asociar con el ID de la pregunta
                "text": answer.text
            }
            question_data["answers"].append(answer_data)

        mock_exam["questions"].append(question_data)

    return mock_exam

