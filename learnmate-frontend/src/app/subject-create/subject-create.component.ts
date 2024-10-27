/* src/app/subject-create/subject-create.component.ts */
import { Component } from '@angular/core';
import { SubjectService } from '../subject.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-subject-create',
  templateUrl: './subject-create.component.html',
  styleUrls: ['./subject-create.component.css'],
})
export class SubjectCreateComponent {
  subject = {
    name: '',
    description: '',
  };
  suggestions: string = '';

  constructor(private subjectService: SubjectService, private router: Router) {}

  onSubmit() {
    this.subjectService.createSubject(this.subject).subscribe(
      (response) => {
        // Redirigir al listado de asignaturas después de crear
        this.router.navigate(['/subjects']);
      },
      (error) => {
        console.error('Error al crear la asignatura:', error);
      }
    );
  }

  getSuggestions() {
    this.subjectService.getSuggestions(this.subject).subscribe(
      (response) => {
        this.suggestions = response.suggestions;
      },
      (error) => {
        console.error('Error al obtener sugerencias:', error);
      }
    );
  }
}
