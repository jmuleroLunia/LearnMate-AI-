// src/app/subject.service.ts

import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Observable} from 'rxjs';

import {ISubject, CreateSubjectDTO} from './interfaces/subject.interface';
import {CreateResourceDTO, IResource} from "./interfaces/resource";
import {IExam, IQuestion} from "./interfaces/exam";
import {IBatchExamResponse} from "./interfaces/batch-exam-response";

@Injectable({
  providedIn: 'root',
})
export class SubjectService {
  private apiUrl = 'http://localhost:8000/subjects/';
  private baseapiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {
  }

  // Nuevo método para buscar en los recursos
  searchResources(subjectId: number, query: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}${subjectId}/search`, {
      params: {
        query: query,
        limit: '5'
      }
    });
  }

  getCorrectAnswer(question: IQuestion, subjectId: number): Observable<{ correct_answer: string }> {
    return this.http.post<{ correct_answer: string }>(
      `${this.baseapiUrl}/get-correct-answer`,
      {question, subject_id: subjectId}
    );
  }


  // Método para generar un examen ficticio
  generateMockExam(subjectId: number, numQuestions: number): Observable<IExam> {
    return this.http.get<IExam>(`${this.apiUrl}${subjectId}/generate-exam`, {
      params: {
        num_questions: numQuestions.toString(),
      },
    });
  }

  // Método para crear una asignatura
  createSubject(subjectData: CreateSubjectDTO): Observable<ISubject> {
    return this.http.post<ISubject>(this.apiUrl, subjectData);
  }

  // Método para obtener todas las asignaturas
  getSubjects(): Observable<ISubject[]> {
    return this.http.get<ISubject[]>(this.apiUrl);
  }

  // Método para obtener sugerencias de IA
  getSuggestions(subjectData: CreateSubjectDTO): Observable<{ suggestions: string }> {
    return this.http.post<{ suggestions: string }>(`${this.apiUrl}suggestions/`, subjectData);
  }

  // Método para editar una asignatura
  updateSubject(subjectId: number, subjectData: CreateSubjectDTO): Observable<ISubject> {
    return this.http.put<ISubject>(`${this.apiUrl}${subjectId}`, subjectData);
  }

  // Método para eliminar una asignatura
  deleteSubject(subjectId: number): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.apiUrl}${subjectId}`);
  }

  // Método para obtener los recursos de una asignatura
  getResources(subjectId: number): Observable<IResource[]> {
    return this.http.get<IResource[]>(`${this.apiUrl}${subjectId}/resources`);
  }

// Método para eliminar un recurso
  deleteResource(resourceId: number): Observable<IResource> {
    return this.http.delete<IResource>(`http://localhost:8000/resources/${resourceId}`);
  }

  // Método para agregar un recurso con archivo adjunto opcional
  addResource(subjectId: number, resourceData: CreateResourceDTO, file?: File | null): Observable<IResource> {
    const formData = new FormData();
    formData.append('title', resourceData.title);
    formData.append('type', resourceData.type);
    if (resourceData.url) formData.append('url', resourceData.url);
    if (resourceData.notes) formData.append('notes', resourceData.notes);
    if (file) formData.append('file', file);

    return this.http.post<IResource>(`${this.apiUrl}${subjectId}/resources`, formData);
  }

  // Fixed exam management methods
  getExams(subjectId: number): Observable<IExam[]> {
    return this.http.get<IExam[]>(`${this.baseapiUrl}/subjects/${subjectId}/exams`);
  }

  addExam(subjectId: number, date: string, files: File[]): Observable<IBatchExamResponse> {
    const formData = new FormData();
    formData.append('date', date);
    files.forEach(file => {
      formData.append('files', file);
    });

    return this.http.post<IBatchExamResponse>(
      `${this.baseapiUrl}/subjects/${subjectId}/exams`,
      formData
    );
  }


  deleteExam(examId: string): Observable<any> {
    return this.http.delete(`${this.baseapiUrl}/exams/${examId}`);
  }

  getExamDetails(examId: string): Observable<IExam> {
    return this.http.get<IExam>(`${this.baseapiUrl}/exams/${examId}`);
  }
}
