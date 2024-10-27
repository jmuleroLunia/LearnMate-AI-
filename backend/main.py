# app/main.py
from typing import List
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import openai
import os

from starlette.middleware.cors import CORSMiddleware

from src import database, schemas
from src import models
from src.database import engine

# Crear las tablas en la base de datos si no existen
models.Base.metadata.create_all(bind=engine)
UPLOAD_DIRECTORY = "./uploaded_files"  # Directorio para almacenar archivos

app = FastAPI()

# Configuración de CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencia de base de datos
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint para crear una asignatura
@app.post("/subjects/", response_model=schemas.SubjectOut)
def create_subject(subject: schemas.SubjectCreate, db: Session = Depends(get_db)):
    db_subject = models.Subject(name=subject.name, description=subject.description)
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject

# Endpoint para obtener todas las asignaturas
@app.get("/subjects/", response_model=List[schemas.SubjectOut])
def get_subjects(db: Session = Depends(get_db)):
    return db.query(models.Subject).all()

# Endpoint para actualizar una asignatura
@app.put("/subjects/{subject_id}", response_model=schemas.SubjectOut)
def update_subject(subject_id: int, subject: schemas.SubjectCreate, db: Session = Depends(get_db)):
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    db_subject.name = subject.name
    db_subject.description = subject.description
    db.commit()
    db.refresh(db_subject)
    return db_subject

# Endpoint para eliminar una asignatura
@app.delete("/subjects/{subject_id}", status_code=204)
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    db.delete(db_subject)
    db.commit()
    return {"message": "Subject deleted successfully"}

# Endpoint para obtener sugerencias de IA
@app.post("/subjects/suggestions/")
def get_subject_suggestions(subject: schemas.SubjectCreate):
    openai.api_key = os.getenv('OPENAI_API_KEY')
    prompt = f"Genera una lista de temas y recursos iniciales para una asignatura llamada '{subject.name}' con la siguiente descripción: '{subject.description}'."
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150,
        temperature=0.7,
    )
    suggestions = response.choices[0].text.strip()
    return {"suggestions": suggestions}

# Endpoint para crear un recurso en una asignatura específica con archivo opcional
@app.post("/subjects/{subject_id}/resources", response_model=schemas.Resource)
async def create_resource_for_subject(
        subject_id: int,
        title: str = Form(...),
        type: str = Form(...),
        url: str = Form(None),
        notes: str = Form(None),
        file: UploadFile = File(None),  # Campo de archivo opcional
        db: Session = Depends(get_db)
):
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    file_path = None
    if file and (type == "Libro" or type == "Apunte"):
        # Crear el directorio si no existe
        os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

    db_resource = models.Resource(
        title=title,
        url=url,
        type=type,
        notes=notes,
        file_path=file_path,
        subject_id=subject_id
    )
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    return db_resource


# Endpoint para obtener todos los recursos de una asignatura específica
@app.get("/subjects/{subject_id}/resources", response_model=List[schemas.Resource])
def get_resources_for_subject(subject_id: int, db: Session = Depends(get_db)):
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    return db_subject.resources
