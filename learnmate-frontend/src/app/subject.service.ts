// src/app/subject.service.ts

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { ISubject, CreateSubjectDTO } from './interfaces/subject.interface';
import {CreateResourceDTO, IResource} from "./interfaces/resource";

@Injectable({
  providedIn: 'root',
})
export class SubjectService {
  private apiUrl = 'http://localhost:8000/subjects/';

  constructor(private http: HttpClient) {}

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
}
