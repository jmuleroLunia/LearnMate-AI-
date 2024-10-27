# backend/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema si es necesario
RUN apt-get update && apt-get install -y build-essential

COPY pyproject.toml poetry.lock /app/

# Instalar Poetry
RUN pip install poetry

# Instalar dependencias
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

COPY .. /app

EXPOSE 8000

CMD ["uvicorn", "main:app","--reload", "--host", "0.0.0.0", "--port", "8000"]
