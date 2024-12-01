from dataclasses import dataclass
from typing import Optional, List

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain.vectorstores.faiss import FAISS

from src.domain.model.exam.exam import Question
import os


@dataclass
class GetCorrectAnswerCommand:
    question: Question
    subject_id: int  # Added subject_id to fetch relevant context

    def validate(self) -> None:
        if not self.question.text.strip():
            raise ValueError("El texto de la pregunta no puede estar vacío.")
        if not self.question.answers or len(self.question.answers) == 0:
            raise ValueError("Debe proporcionar al menos una respuesta.")
        for answer in self.question.answers:
            if not answer.text.strip():
                raise ValueError("El texto de la respuesta no puede estar vacío.")


class SuggestAnswerService:
    def __init__(
            self,
            llm: Optional[AzureChatOpenAI] = None,
            embeddings: Optional[AzureOpenAIEmbeddings] = None
    ):
        self.llm = llm or self._create_default_llm()
        self.embeddings = embeddings or self._create_default_embeddings()
        self.output_parser = StrOutputParser()

    def get_correct_answer(self, command: GetCorrectAnswerCommand) -> str:
        command.validate()
        try:
            # Format the question and answers
            question_text = command.question.text
            answers_text = "\n".join([f"{i + 1}. {ans.text}" for i, ans in enumerate(command.question.answers)])

            # Get relevant context from vectorstore
            context = self._get_relevant_context(command.subject_id, question_text)

            # Create the chain
            chain = self._create_chain()

            # Prepare the input
            chain_input = {
                "context": context,
                "question": question_text,
                "answers": answers_text
            }

            # Execute the chain
            response = chain.invoke(chain_input)

            return response.strip()

        except Exception as e:
            raise RuntimeError(f"No se pudo obtener la respuesta correcta: {str(e)}") from e

    def _get_relevant_context(self, subject_id: int, question: str, k: int = 5) -> str:
        """Retrieve relevant context from the subject's vectorstore"""
        try:
            vectorstore_path = os.path.join("./vectorstores", f"subject_{subject_id}")

            if not os.path.exists(vectorstore_path):
                return "No se encontró contexto relevante para esta asignatura."

            vectorstore = FAISS.load_local(
                vectorstore_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )

            relevant_docs = vectorstore.similarity_search(question, k=k)

            # Combine the relevant documents into a single context string
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            print(f"Contexto relevante: {context}")
            return context if context.strip() else "No se encontró contexto relevante."

        except Exception as e:
            print(f"Error retrieving context: {str(e)}")
            return "Error al recuperar el contexto."

    def _create_chain(self):
        """Create the processing chain with context"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un asistente experto en educación que ayuda a identificar la respuesta correcta 
            a preguntas de opción múltiple. Utilizarás el contexto proporcionado para fundamentar tu respuesta,
            pero también puedes usar tu conocimiento general si el contexto no es suficiente."""),
            ("user", """Contexto relevante:
            {context}

            Pregunta: {question}

            Respuestas disponibles:
            {answers}

            Por favor, analiza cuidadosamente el contexto y la pregunta, luego proporciona:
            1. El número de la respuesta correcta
            2. Una explicación detallada basada en el contexto proporcionado y/o conocimiento general
            3. Si encontraste información relevante en el contexto, cítala para respaldar tu respuesta""")
        ])
        chain = (
                {"context": RunnablePassthrough(),
                 "question": RunnablePassthrough(),
                 "answers": RunnablePassthrough()}
                | prompt
                | self.llm
                | self.output_parser
        )

        return chain

    @staticmethod
    def _create_default_llm() -> AzureChatOpenAI:
        return AzureChatOpenAI(
            openai_api_key='9865ecf92f674bfcb272207a6ac5ae9d',
            azure_endpoint="https://eastus-gpt.openai.azure.com",
            openai_api_version="2024-02-01",
            deployment_name="gpt-4o",
            temperature=0.0,
        )

    @staticmethod
    def _create_default_embeddings() -> AzureOpenAIEmbeddings:
        return AzureOpenAIEmbeddings(
            azure_deployment="text-embedding-3-large",
            openai_api_key="9865ecf92f674bfcb272207a6ac5ae9d",
            azure_endpoint="https://eastus-gpt.openai.azure.com",
            openai_api_version="2024-02-01",
        )