from dataclasses import dataclass
from datetime import datetime
from pathlib import Path as PathlibPath
from typing import Optional
from uuid import UUID

from langchain_community.document_loaders import AzureAIDocumentIntelligenceLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from sqlalchemy.orm import Session

from src.database import SessionLocal, create_tables
from src.domain.model.exam.exam import Exam
from src.infrastructure.persistence.repositories.exam_repository import ExamRepository


@dataclass
class ExtractExamCommand:
    pdf_path: PathlibPath
    session: Session
    subject_id: int
    date: str  # Añadido la fecha

    def validate(self) -> None:
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found at {self.pdf_path}")
        if self.pdf_path.suffix.lower() != '.pdf':
            raise ValueError(f"File must be a PDF, got {self.pdf_path.suffix}")
        if self.subject_id <= 0:
            raise ValueError(f"Invalid subject_id: {self.subject_id}")
        # Validar el formato de la fecha
        try:
            datetime.strptime(self.date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {self.date}, expected YYYY-MM-DD")


class ExamExtractionService:
    def __init__(self, llm: Optional[AzureChatOpenAI] = None):
        self.llm = llm or self._create_default_llm()
        self.prompt = self._create_prompt()

    def extract(self, command: ExtractExamCommand) -> UUID:
        """Extract exam information and persist it to database"""
        command.validate()
        create_tables()

        try:
            # Cargar y extraer texto del PDF
            loader = AzureAIDocumentIntelligenceLoader(
                api_key="cc371d440e444e599c51abb0340c30e7",
                api_endpoint="https://azuredocumentintelligencedemo.cognitiveservices.azure.com/",
                file_path=str(command.pdf_path),
            )

            documents = loader.load()
            text = "\n".join([doc.page_content for doc in documents])

            if not text.strip():
                raise ValueError("Could not extract any text from the PDF file")

            # Usar el LLM para extraer datos del exam
            runnable = self.prompt | self.llm.with_structured_output(schema=Exam)
            exam = runnable.invoke({"text": text})

            # Asignar la fecha y el subject_id al exam
            exam.date = command.date
            exam.subject_id = command.subject_id

            # Guardar el exam en la base de datos
            repository = ExamRepository(command.session)
            exam_id = repository.save(exam)

            return exam_id

        except Exception as e:
            raise RuntimeError(f"Failed to extract exam information: {str(e)}") from e

    @staticmethod
    def _create_default_llm() -> AzureChatOpenAI:
        return AzureChatOpenAI(
            openai_api_key='9865ecf92f674bfcb272207a6ac5ae9d',
            azure_endpoint="https://eastus-gpt.openai.azure.com",
            openai_api_version="2024-02-01",
            deployment_name="gpt-4o",
        )

    @staticmethod
    def _create_prompt() -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an expert extraction algorithm. "
                "Uuids are unique identifiers and you should autogenerate them. "
                "Only extract relevant information from the text. "
                "If you do not know the value of an attribute asked to extract, "
                "return null for the attribute's value.",
            ),
            ("human", "{text}"),
        ])


# Example usage:
if __name__ == "__main__":
    db = SessionLocal()
    try:
        command = ExtractExamCommand(
            pdf_path=PathlibPath("./E710130290A24F1.pdf"),
            session=db,
            subject_id=1
        )
        service = ExamExtractionService()
        exam_id = service.extract(command)
        print(f"Exam saved with ID: {exam_id}")
    finally:
        db.close()