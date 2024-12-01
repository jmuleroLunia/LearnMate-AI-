from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

load_dotenv('.env')

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Importar los modelos aquí después de crear Base

# Función para crear todas las tablas
def create_tables():
    Base.metadata.create_all(bind=engine)

# Dependencia para obtener la sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Crear las tablas al importar el módulo
create_tables()