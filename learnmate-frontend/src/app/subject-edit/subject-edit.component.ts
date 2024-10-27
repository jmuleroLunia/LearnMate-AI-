// src/app/subject-edit/subject-edit.component.ts

import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { SubjectService } from '../subject.service';
import { ISubject, CreateSubjectDTO } from '../interfaces/subject.interface';

@Component({
  selector: 'app-subject-edit',
  templateUrl: './subject-edit.component.html',
  styleUrls: ['./subject-edit.component.css']
})
export class SubjectEditComponent implements OnInit {
  subjectId: number | undefined = undefined;
  subject: CreateSubjectDTO = { name: '', description: '' };

  constructor(
    private subjectService: SubjectService,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');

    // Validar si el parámetro existe y es un número válido
    if (idParam !== null) {
      this.subjectId = +idParam;
      this.loadSubject();
    } else {
      console.error('El parámetro id no está definido o no es válido.');
      this.router.navigate(['/subjects']);  // Redirigir si el ID no es válido
    }
  }

  // Cargar los datos de la asignatura para editar
  loadSubject() {
    if (this.subjectId !== undefined) {
      this.subjectService.getSubjects().subscribe(
        (subjects) => {
          const subject = subjects.find(s => s.id === this.subjectId);
          if (subject) {
            this.subject = { name: subject.name, description: subject.description };
          } else {
            console.error('Asignatura no encontrada');
          }
        },
        (error) => {
          console.error('Error al cargar la asignatura:', error);
        }
      );
    }
  }

  // Guardar los cambios en la asignatura
  onSubmit() {
    if (this.subjectId !== undefined) {
      this.subjectService.updateSubject(this.subjectId, this.subject).subscribe(
        () => {
          this.router.navigate(['/subjects']);
        },
        (error) => {
          console.error('Error al actualizar la asignatura:', error);
        }
      );
    }
  }
}
