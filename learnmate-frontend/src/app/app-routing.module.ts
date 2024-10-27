// src/app/app-routing.module.ts

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { SubjectListComponent } from './subject-list/subject-list.component';
import { SubjectCreateComponent } from './subject-create/subject-create.component';
import { SubjectEditComponent } from './subject-edit/subject-edit.component';
import { SubjectResourcesComponent } from './subject-resources/subject-resources.component';

const routes: Routes = [
  { path: '', redirectTo: '/subjects', pathMatch: 'full' },
  { path: 'subjects', component: SubjectListComponent },
  { path: 'subjects/create', component: SubjectCreateComponent },
  { path: 'subjects/edit/:id', component: SubjectEditComponent },
  { path: 'subjects/:id/resources', component: SubjectResourcesComponent },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
