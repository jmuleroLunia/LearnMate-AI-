// src/app/subject-list/subject-list.component.ts

import { Component, OnInit } from '@angular/core';
import { SubjectService } from '../subject.service';
import { ISubject } from '../interfaces/subject.interface';

@Component({
  selector: 'app-subject-list',
  templateUrl: './subject-list.component.html',
  styleUrls: ['./subject-list.component.css'],
})
export class SubjectListComponent implements OnInit {
  subjects: ISubject[] = [];

  constructor(private subjectService: SubjectService) {}

  ngOnInit(): void {
    this.loadSubjects();
  }

  // Cargar todas las asignaturas
  loadSubjects() {
    this.subjectService.getSubjects().subscribe(
      (response) => {
        this.subjects = response;
      },
      (error) => {
        console.error('Error al obtener las asignaturas:', error);
      }
    );
  }

  // Eliminar una asignatura
  deleteSubject(subjectId: number) {
    if (confirm('¿Estás seguro de que deseas eliminar esta asignatura?')) {
      this.subjectService.deleteSubject(subjectId).subscribe(
        () => {
          this.subjects = this.subjects.filter((subject) => subject.id !== subjectId);
        },
        (error) => {
          console.error('Error al eliminar la asignatura:', error);
        }
      );
    }
  }
}
