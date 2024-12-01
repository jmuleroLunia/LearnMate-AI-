// src/app/app-routing.module.ts

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { SubjectListComponent } from './subject-list/subject-list.component';
import { SubjectCreateComponent } from './subject-create/subject-create.component';
import { SubjectEditComponent } from './subject-edit/subject-edit.component';
import { SubjectResourcesComponent } from './subject-resources/subject-resources.component';
import { SubjectExamsComponent } from './subject-exams/subject-exams.component';
import { SubjectMockExamComponent } from './subject-mock-exam/subject-mock-exam.component'; // Importar el nuevo componente

const routes: Routes = [
  { path: '', redirectTo: '/subjects', pathMatch: 'full' },
  { path: 'subjects', component: SubjectListComponent },
  { path: 'subjects/create', component: SubjectCreateComponent },
  { path: 'subjects/edit/:id', component: SubjectEditComponent },
  { path: 'subjects/:id/resources', component: SubjectResourcesComponent },
  { path: 'subjects/:id/exams', component: SubjectExamsComponent },
  { path: 'subjects/:id/mock-exam', component: SubjectMockExamComponent }, // Añadir esta línea
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
})
export class AppRoutingModule {}
