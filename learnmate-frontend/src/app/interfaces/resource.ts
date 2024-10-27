// src/app/interfaces/resource.interface.ts

export interface IResource {
  id?: number;
  title: string;
  url?: string;
  type: string;  // "Libro", "Enlace Web", "Apunte"
  notes?: string;
  file_path?: string;
  subject_id?: number;
}

export interface CreateResourceDTO {
  title: string;
  url?: string;
  type: string;
  notes?: string;
}
