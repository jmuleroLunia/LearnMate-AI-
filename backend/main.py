# src/main.py

from typing import List
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from langchain_community.document_loaders import TextLoader, UnstructuredMarkdownLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import AzureOpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from llama_parse import LlamaParse

from sqlalchemy.orm import Session
import os
import uuid
import asyncio

from starlette.middleware.cors import CORSMiddleware

from src import database, schemas
from src import models
from src.database import engine

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore


# Crear las tablas en la base de datos si no existen
models.Base.metadata.create_all(bind=engine)

UPLOAD_DIRECTORY = "./uploaded_files"  # Directorio para almacenar archivos
VECTORSTORE_DIRECTORY = "./vectorstores"  # Directorio para almacenar embeddings

# Crear los directorios si no existen
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(VECTORSTORE_DIRECTORY, exist_ok=True)

app = FastAPI()

# Configuración de CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Cambia esto a los orígenes permitidos en producción
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


# Función para generar IDs únicos para archivos
def resource_id_generator() -> str:
    return str(uuid.uuid4())


# Función para procesar un solo recurso con LangChain y LlamaParse
async def process_resource_with_langchain(resource: models.Resource, db: Session):
    # Configurar embeddings de Azure OpenAI
    embeddings = AzureOpenAIEmbeddings(
        azure_deployment='text-embedding-3-large',
        openai_api_key='9865ecf92f674bfcb272207a6ac5ae9d',
        azure_endpoint="https://eastus-gpt.openai.azure.com",
        openai_api_version="2024-02-01",
    )

    # Configurar LlamaParse
    parser = LlamaParse(result_type="markdown")  # O usa "text" si prefieres solo texto plano

    if resource.file_path:
        file_full_path = os.path.join(".", resource.file_path.lstrip("/"))
        # Cargar datos con LlamaParse
        llama_parse_documents = await parser.aload_data(file_full_path)

        with open('./uploaded_files/output.md', 'a') as f:  # Open the file in append mode ('a')
            for doc in llama_parse_documents:
                f.write(doc.text + '\n')

        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]

        markdown_path = "./uploaded_files/output.md"
        loader = MarkdownHeaderTextSplitter(markdown_path,
                                            mode="elements",
                                            strategy="fast",
                                            )
        documents = loader.split_text()
        # Split loaded documents into chunks
        print("Splitting documents...")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
        docs = text_splitter.split_documents(documents)

        # Crear o actualizar el vector store
        db_vectorstore_path = os.path.join(VECTORSTORE_DIRECTORY, f"resource_{resource.id}")
        os.makedirs(db_vectorstore_path, exist_ok=True)
        db_vectorstore = FAISS.from_documents(docs, embeddings)
        db_vectorstore.save_local(db_vectorstore_path)
    else:
        # Procesamiento adicional para recursos sin archivo
        if resource.url:
            # Implementa lógica de extracción de contenido desde la URL
            pass
        elif resource.notes:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            text = resource.notes
            documents = [Document(page_content=text)]
            docs = text_splitter.split_documents(documents)

            db_vectorstore_path = os.path.join(VECTORSTORE_DIRECTORY, f"resource_{resource.id}")
            os.makedirs(db_vectorstore_path, exist_ok=True)
            db_vectorstore = FAISS.from_documents(docs, embeddings)
            db_vectorstore.save_local(db_vectorstore_path)
        else:
            raise ValueError("No hay contenido para procesar")


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
        trigger=IntervalTrigger(minutes=1),  # Ejecutar cada 1 minuto
        id='process_pending_resources',
        name='Procesar recursos pendientes cada 1 minuto',
        replace_existing=True
    )
    scheduler.start()
    print("Scheduler iniciado.")


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
    # Implementa la lógica para obtener sugerencias de IA
    return {"suggestions": ["Sugerencia 1", "Sugerencia 2", "Sugerencia 3"]}


# Endpoint para crear un recurso en una asignatura específica con archivo opcional
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
    file_size = None
    if file and (type in ["Libro", "Apunte"]):
        os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
        # Generar un nombre de archivo único para evitar sobrescribir
        unique_id = resource_id_generator()
        filename = f"{unique_id}{os.path.splitext(file.filename)[1]}"
        file_location = os.path.join(UPLOAD_DIRECTORY, filename)
        with open(file_location, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            file_size = len(content)
        file_path = f"/uploaded_files/{filename}"

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


# Endpoint para eliminar un recurso y su archivo asociado
@app.delete("/resources/{resource_id}", response_model=schemas.Resource)
def delete_resource(resource_id: int, db: Session = Depends(get_db)):
    db_resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    if not db_resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Si hay un archivo asociado, eliminarlo del sistema de archivos
    if db_resource.file_path:
        file_full_path = os.path.join(".", db_resource.file_path.lstrip("/"))
        if os.path.exists(file_full_path):
            os.remove(file_full_path)
        else:
            print(f"El archivo {file_full_path} no existe.")

    # Eliminar el recurso de la base de datos
    db.delete(db_resource)
    db.commit()
    return db_resource


# Endpoint para ejecutar manualmente el procesamiento de recursos pendientes
@app.post("/process-resources/manual", response_model=List[schemas.Resource])
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
    return processed_resources
