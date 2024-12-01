/* src/app/app.module.ts */
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { SubjectCreateComponent } from './subject-create/subject-create.component';
import { SubjectListComponent } from './subject-list/subject-list.component';

import {FormsModule, ReactiveFormsModule} from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { SubjectEditComponent } from './subject-edit/subject-edit.component';
import { SubjectResourcesComponent } from './subject-resources/subject-resources.component';
import { SubjectExamsComponent } from './subject-exams/subject-exams.component';
import { SubjectMockExamComponent } from './subject-mock-exam/subject-mock-exam.component';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import {MatStepperModule} from "@angular/material/stepper";
import {MatButtonModule} from "@angular/material/button";
import {MatProgressBarModule} from "@angular/material/progress-bar";
import {MatCheckboxModule} from "@angular/material/checkbox";
import {MatRadioModule} from "@angular/material/radio";
import {MatIconModule} from "@angular/material/icon";
import {MatProgressSpinner} from "@angular/material/progress-spinner";
import { FilterMarkedPipe } from './pipes/filter-marked.pipe';

@NgModule({
  declarations: [
    AppComponent,
    SubjectCreateComponent,
    SubjectListComponent,
    SubjectEditComponent,
    SubjectResourcesComponent,
    SubjectExamsComponent,
    SubjectMockExamComponent,
    FilterMarkedPipe,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    FormsModule,
    HttpClientModule,
    MatStepperModule,
    MatButtonModule,
    MatProgressBarModule,
    MatCheckboxModule,
    MatRadioModule,
    MatIconModule,
    ReactiveFormsModule,
    MatProgressSpinner,
  ],
  providers: [
    provideAnimationsAsync()
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
