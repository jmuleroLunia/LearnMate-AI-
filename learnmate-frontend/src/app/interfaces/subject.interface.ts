// src/app/interfaces/subject.interface.ts

export interface ISubject {
  id: number;
  name: string;
  description: string;
}

export interface CreateSubjectDTO {
  name: string;
  description?: string;
}
