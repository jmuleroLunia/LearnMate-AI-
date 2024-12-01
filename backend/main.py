from itertools import islice
from typing import List
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Path
from fastapi.staticfiles import StaticFiles
from langchain_community.document_loaders import TextLoader, UnstructuredMarkdownLoader, DirectoryLoader, \
    AzureAIDocumentIntelligenceLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import AzureOpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from llama_parse import LlamaParse
from nltk.corpus.reader import documents

from sqlalchemy.orm import Session
import os
import uuid
import asyncio

from starlette.middleware.cors import CORSMiddleware
import nltk

from src import database, schemas
from src import models
from src.application.service.exam.exam_extraction_service import ExtractExamCommand, ExamExtractionService
from src.application.service.exam.generate_mock_exam import generate_mock_exam
from src.application.service.question.suggest_answer import GetCorrectAnswerCommand, \
    SuggestAnswerService
from src.database import engine

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from datetime import datetime
from typing import List
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from uuid import UUID

# Importar Path de pathlib como FilePath para evitar colisión
from pathlib import Path as FilePath

from src.domain.model.exam.exam import Question, QuestionWithSubject, BatchExamResponse

# Crear las tablas en la base de datos si no existen
models.Base.metadata.create_all(bind=engine)

UPLOAD_DIRECTORY = "./uploaded_files"
VECTORSTORE_DIRECTORY = "./vectorstores"  # Ahora organizaremos por asignatura

os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(VECTORSTORE_DIRECTORY, exist_ok=True)
# Descargar recursos necesarios de NLTK
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger')
nltk.download('universal_tagset')
nltk.download('averaged_perceptron_tagger_eng')
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

# Montar los archivos estáticos
app.mount("/uploaded_files", StaticFiles(directory=UPLOAD_DIRECTORY), name="uploaded_files")


# Dependencia de base de datos
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Configurar APScheduler con un JobStore basado en SQLAlchemy para persistencia
scheduler = AsyncIOScheduler()
scheduler.add_jobstore(SQLAlchemyJobStore(url=database.DATABASE_URL), 'default')


@app.get("/subjects/{subject_id}/generate-exam", response_model=schemas.ExamOut)
def generate_exam_endpoint(
    subject_id: int = Path(..., description="El ID de la asignatura"),
    num_questions: int = 5,
    db: Session = Depends(get_db)
):
    try:
        mock_exam = generate_mock_exam(subject_id, num_questions, db)
        return mock_exam
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# Updated FastAPI endpoint
@app.post("/subjects/{subject_id}/exams", response_model=BatchExamResponse)
async def create_exam_for_subject(
        subject_id: int = Path(...),
        files: List[UploadFile] = File(...),
        date: str = Form(...),
        db: Session = Depends(get_db)
):
    # Verify that the subject exists
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    exams = []
    errors = []

    for file in files:
        try:
            # Validate that the file is a PDF
            if not file.filename.endswith('.pdf'):
                errors.append(f"File '{file.filename}' is not a PDF.")
                continue

            # Save the file
            os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
            unique_id = str(uuid.uuid4())
            filename = f"{unique_id}.pdf"
            file_location = os.path.join(UPLOAD_DIRECTORY, filename)

            with open(file_location, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            # Process the exam (extract questions and answers)
            command = ExtractExamCommand(
                pdf_path=FilePath(file_location),
                session=db,
                subject_id=subject_id,
                date=date
            )
            service = ExamExtractionService()
            exam_id = service.extract(command)

            # Retrieve the saved exam to return it
            exam_model = db.query(models.ExamModel).filter(models.ExamModel.id == exam_id).first()
            if not exam_model:
                errors.append(f"Failed to retrieve saved exam for file '{file.filename}'.")
                continue

            exams.append(exam_model)

        except Exception as e:
            errors.append(f"Error processing file '{file.filename}': {str(e)}")
            # Clean up the file if something goes wrong
            if os.path.exists(file_location):
                os.remove(file_location)
            continue

    return BatchExamResponse(exams=exams, errors=errors)





@app.get("/subjects/{subject_id}/exams", response_model=List[schemas.ExamOut])
def get_exams_for_subject(
        subject_id: int = Path(...),  # Uso correcto de Path de fastapi
        db: Session = Depends(get_db)
):
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    return db.query(models.ExamModel) \
        .filter(models.ExamModel.subject_id == subject_id) \
        .all()


@app.get("/exams/{exam_id}", response_model=schemas.ExamOut)
def get_exam(
        exam_id: UUID = Path(...),  # Uso correcto de Path de fastapi
        db: Session = Depends(get_db)
):
    exam = db.query(models.ExamModel).filter(models.ExamModel.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam


@app.delete("/exams/{exam_id}")
async def delete_exam(
        exam_id: UUID = Path(...),  # Uso correcto de Path de fastapi
        db: Session = Depends(get_db)
):
    exam = db.query(models.ExamModel).filter(models.ExamModel.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    db.delete(exam)
    db.commit()

    return {"message": "Exam deleted successfully"}


@app.get("/exams/{exam_id}/questions", response_model=List[schemas.QuestionOut])
def get_exam_questions(
        exam_id: UUID = Path(...),  # Uso correcto de Path de fastapi
        db: Session = Depends(get_db)
):
    exam = db.query(models.ExamModel).filter(models.ExamModel.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam.questions


@app.get("/questions/{question_id}/answers", response_model=List[schemas.AnswerOut])
def get_question_answers(
        question_id: UUID = Path(...),  # Uso correcto de Path de fastapi
        db: Session = Depends(get_db)
):
    question = db.query(models.QuestionModel).filter(models.QuestionModel.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question.answers


def get_subject_vectorstore_path(subject_id: int) -> str:
    """Obtener la ruta del vectorstore para una asignatura específica"""
    return os.path.join(VECTORSTORE_DIRECTORY, f"subject_{subject_id}")


def get_or_create_vectorstore(subject_id: int, embeddings) -> FAISS:
    """
    Obtener el vectorstore existente para una asignatura o crear uno nuevo si no existe
    """
    vectorstore_path = get_subject_vectorstore_path(subject_id)
    os.makedirs(vectorstore_path, exist_ok=True)

    try:
        # Verificar si los archivos existen
        index_path = os.path.join(vectorstore_path, "index.faiss")
        pkl_path = os.path.join(vectorstore_path, "index.pkl")

        if not os.path.exists(index_path) or not os.path.exists(pkl_path):
            print(f"Archivos de vectorstore no encontrados en {vectorstore_path}")
            return None

        # Cargar el vectorstore con deserialización segura habilitada
        vectorstore = FAISS.load_local(
            vectorstore_path,
            embeddings,
            allow_dangerous_deserialization=True  # Permitir deserialización segura
        )

        # Verificar si el vectorstore tiene documentos
        if hasattr(vectorstore, 'index') and vectorstore.index.ntotal == 0:
            print(f"Vectorstore encontrado pero vacío para asignatura {subject_id}")
            return None

        print(f"Vectorstore cargado para asignatura {subject_id} con {vectorstore.index.ntotal} documentos")
        return vectorstore
    except Exception as e:
        print(f"Error al cargar vectorstore: {str(e)}")
        return None


# Función para generar IDs únicos para archivos
def resource_id_generator() -> str:
    return str(uuid.uuid4())


async def process_resource_with_langchain(resource: models.Resource, db: Session):
    """
    Procesar un recurso y añadirlo al vectorstore de su asignatura
    """
    print(f"Procesando recurso {resource.id} para asignatura {resource.subject_id}")

    embeddings = AzureOpenAIEmbeddings(
        azure_deployment='text-embedding-3-large',
        openai_api_key='9865ecf92f674bfcb272207a6ac5ae9d',
        azure_endpoint="https://eastus-gpt.openai.azure.com",
        openai_api_version="2024-02-01",
    )

    # Intentamos obtener el vectorstore existente
    vectorstore = get_or_create_vectorstore(resource.subject_id, embeddings)

    docs = []
    try:
        if resource.file_path:
            file_full_path = os.path.join(".", resource.file_path.lstrip("/"))
            print(f"Procesando archivo: {file_full_path}")

            loader = AzureAIDocumentIntelligenceLoader(
                api_key="cc371d440e444e599c51abb0340c30e7",
                api_endpoint="https://azuredocumentintelligencedemo.cognitiveservices.azure.com/",
                file_path=str(file_full_path),
            )

            raw_docs = loader.load()
            print(f"Documentos cargados del archivo: {len(raw_docs)}")
            print(f"Muestra del contenido: {raw_docs[0].page_content[:200] if raw_docs else 'No content'}")

            docs = raw_docs

        elif resource.notes:
            print(f"Procesando notas del recurso {resource.id}")
            docs = [Document(page_content=resource.notes)]
            print(f"Contenido de las notas: {docs[0].page_content[:200]}")

        if docs:
            markdown_text = "\n".join([doc.page_content for doc in docs])

            md_splitter = RecursiveCharacterTextSplitter.from_language(
                language=Language.MARKDOWN, chunk_size=450, chunk_overlap=150
            )
            md_docs = md_splitter.create_documents([markdown_text])
            # Enriquecer los metadatos
            for i, doc in enumerate(md_docs):
                doc.metadata.update({
                    "resource_id": resource.id,
                    "resource_title": resource.title,
                    "resource_type": resource.type,
                    "subject_id": resource.subject_id,
                    "chunk_index": i,
                    "total_chunks": len(docs)
                })

            # Crear nuevo vectorstore o añadir documentos al existente
            for lote_documentos in divide_en_lotes(md_docs, 450):
                vectorstore = get_or_create_vectorstore(resource.subject_id, embeddings)
                if vectorstore is None:
                    print("Creando nuevo vectorstore con los documentos")
                    vectorstore = FAISS.from_documents(lote_documentos, embeddings)
                else:
                    print("Añadiendo documentos al vectorstore existente")
                    vectorstore.add_documents(lote_documentos)

            # Guardar el vectorstore actualizado
            vectorstore_path = get_subject_vectorstore_path(resource.subject_id)
            vectorstore.save_local(
                vectorstore_path
            )

            print(f"Vectorstore guardado en {vectorstore_path}")
            if hasattr(vectorstore, 'index'):
                print(f"Total de documentos en el vectorstore: {vectorstore.index.ntotal}")

        else:
            print("No se encontraron documentos para procesar")
            raise ValueError("No hay contenido para procesar")

    except Exception as e:
        print(f"Error durante el procesamiento: {str(e)}")
        raise e


# Función para procesar recursos pendientes
async def process_pending_resources():
    print("Verificando recursos pendientes...")
    db = next(get_db())
    pending_resources = db.query(models.Resource).filter(models.Resource.status == "pending").all()
    for resource in pending_resources:
        try:
            await process_resource_with_langchain(resource, db)
            resource.status = "processed"
            print(f"Recurso {resource.id} procesado exitosamente.")
        except Exception as e:
            resource.status = "error"
            print(f"Error al procesar el recurso {resource.id}: {e}")
        finally:
            db.add(resource)
            db.commit()
    db.close()


# Iniciar el scheduler al arrancar la aplicación
@app.on_event("startup")
async def startup_event():
    scheduler.add_job(
        process_pending_resources,
        trigger=IntervalTrigger(minutes=1),
        id='process_pending_resources',
        name='Procesar recursos pendientes cada 1 minuto',
        replace_existing=True
    )
    scheduler.start()
    print("Scheduler iniciado.")


# CRUD Endpoints

@app.post("/subjects/", response_model=schemas.SubjectOut)
def create_subject(subject: schemas.SubjectCreate, db: Session = Depends(get_db)):
    db_subject = models.Subject(name=subject.name, description=subject.description)
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject


@app.get("/subjects/", response_model=List[schemas.SubjectOut])
def get_subjects(db: Session = Depends(get_db)):
    return db.query(models.Subject).all()


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


@app.delete("/subjects/{subject_id}", status_code=204)
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    db.delete(db_subject)
    db.commit()
    return {"message": "Subject deleted successfully"}

@app.post("/get-correct-answer")
async def get_correct_answer_endpoint(
    data: QuestionWithSubject,
    db: Session = Depends(get_db)
):
    try:
        # Verify subject exists
        db_subject = db.query(models.Subject).filter(models.Subject.id == data.subject_id).first()
        if not db_subject:
            raise HTTPException(status_code=404, detail="Subject not found")

        command = GetCorrectAnswerCommand(
            question=data.question,
            subject_id=data.subject_id
        )
        service = SuggestAnswerService()
        correct_answer = service.get_correct_answer(command)

        return {"correct_answer": correct_answer}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/subjects/{subject_id}/resources", response_model=schemas.Resource)
async def create_resource_for_subject(
        subject_id: int = Path(...),  # Uso correcto de Path de fastapi
        title: str = Form(...),
        type: str = Form(...),
        url: str = Form(None),
        notes: str = Form(None),
        file: UploadFile = File(None),
        db: Session = Depends(get_db)
):
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    file_path = None
    if file and (type in ["Libro", "Apunte"]):
        os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
        unique_id = resource_id_generator()
        filename = f"{unique_id}{os.path.splitext(file.filename)[1]}"
        file_location = os.path.join(UPLOAD_DIRECTORY, filename)
        with open(file_location, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        file_path = f"/uploaded_files/{filename}"

    db_resource = models.Resource(
        title=title,
        url=url,
        type=type,
        notes=notes,
        file_path=file_path,
        subject_id=subject_id,
        status="pending"
    )
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    return db_resource


@app.get("/subjects/{subject_id}/resources", response_model=List[schemas.Resource])
def get_resources_for_subject(subject_id: int = Path(...), db: Session = Depends(get_db)):
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return db_subject.resources


@app.delete("/resources/{resource_id}")
async def delete_resource(resource_id: int, db: Session = Depends(get_db)):
    db_resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    if not db_resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    if db_resource.file_path:
        file_full_path = os.path.join(".", db_resource.file_path.lstrip("/"))
        if os.path.exists(file_full_path):
            os.remove(file_full_path)

    db.delete(db_resource)
    db.commit()
    return {"message": "Resource deleted successfully"}


def divide_en_lotes(iterable, tamano_lote):
            iterador = iter(iterable)
            while True:
                lote = list(islice(iterador, tamano_lote))
                if not lote:
                    break
                yield lote
# Modificar el endpoint de búsqueda
@app.get("/subjects/{subject_id}/search")
async def search_in_subject(
        subject_id: int = Path(...),  # Uso correcto de Path de fastapi
        query: str = '',
        limit: int = 5,
        db: Session = Depends(get_db)
):
    embeddings = AzureOpenAIEmbeddings(
        azure_deployment='text-embedding-3-large',
        openai_api_key='YOUR_OPENAI_API_KEY',
        azure_endpoint="https://YOUR_AZURE_ENDPOINT",
        openai_api_version="2024-02-01",
    )

    try:
        vectorstore = get_or_create_vectorstore(subject_id, embeddings)

        # Si no hay vectorstore o no hay documentos procesados aún
        if not vectorstore:
            return {
                "results": [],
                "total_results": 0,
                "message": "No hay documentos procesados para buscar"
            }

        results = vectorstore.similarity_search_with_score(query, k=limit)

        # Verificar si los resultados son válidos
        formatted_results = []
        for doc, score in results:
            # Solo incluir resultados con contenido
            if doc.page_content.strip():
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "relevance_score": float(score)
                })

        return {
            "results": formatted_results,
            "total_results": len(formatted_results)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en la búsqueda: {str(e)}"
        )


@app.post("/process-resources/manual")
async def process_resources_manually(db: Session = Depends(get_db)):
    pending_resources = db.query(models.Resource).filter(models.Resource.status == "pending").all()
    processed_resources = []
    for resource in pending_resources:
        try:
            await process_resource_with_langchain(resource, db)
            resource.status = "processed"
            print(f"Recurso {resource.id} procesado exitosamente.")
        except Exception as e:
            resource.status = "error"
            print(f"Error al procesar el recurso {resource.id}: {e}")
        finally:
            db.add(resource)
            db.commit()
            processed_resources.append(resource)
    return {"message": f"Processed {len(processed_resources)} resources"}
