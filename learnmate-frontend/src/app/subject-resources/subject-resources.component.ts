// src/app/subject-resources/subject-resources.component.ts

import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { SubjectService } from '../subject.service';
import {CreateResourceDTO, IResource} from "../interfaces/resource";

@Component({
  selector: 'app-subject-resources',
  templateUrl: './subject-resources.component.html',
  styleUrls: ['./subject-resources.component.css']
})
export class SubjectResourcesComponent implements OnInit {
  subjectId: number | undefined;
  resources: IResource[] = [];
  newResource: CreateResourceDTO = { title: '', type: 'Libro' };
  selectedFile: File | null = null;

  constructor(
    private subjectService: SubjectService,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.subjectId = +idParam;
      this.loadResources();
    } else {
      console.error('No se pudo obtener el ID de la asignatura');
    }
  }

  // Cargar recursos de la asignatura
  loadResources() {
    if (this.subjectId !== undefined) {
      this.subjectService.getResources(this.subjectId).subscribe(
        (response) => {
          this.resources = response;
        },
        (error) => {
          console.error('Error al cargar recursos:', error);
        }
      );
    }
  }

  // Manejar la selección del archivo
  onFileSelected(event: any) {
    this.selectedFile = event.target.files[0];
  }

  // Agregar un nuevo recurso
  addResource() {
    if (this.subjectId !== undefined && this.newResource.title) {
      this.subjectService.addResource(this.subjectId, this.newResource, this.selectedFile).subscribe(
        (resource) => {
          this.resources.push(resource);
          this.newResource = { title: '', type: 'Libro' };
          this.selectedFile = null;
        },
        (error) => {
          console.error('Error al agregar el recurso:', error);
        }
      );
    } else {
      console.error('No se puede agregar el recurso sin un título o subjectId');
    }
  }

  // Obtener el nombre del archivo desde la ruta
  getFileName(filePath: string): string {
    return filePath.split('/').pop() || filePath;
  }

  // Obtener extensión del archivo desde su nombre
  getFileExtension(filePath: string): string {
    return filePath.split('.').pop() || '';
  }

  // Obtener información del archivo adjunto (tamaño y extensión)
  getFileInfo(resource: IResource): string | null {
    if (resource.file_path) {
      const extension = this.getFileExtension(resource.file_path);
      // Aquí podrías hacer una solicitud al backend para obtener el tamaño real del archivo.
      // Usamos un tamaño simulado como ejemplo.
      const simulatedSize = '1.2 MB';
      return `${simulatedSize} (${extension.toUpperCase()})`;
    }
    return null;
  }
}
