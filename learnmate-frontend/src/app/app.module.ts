/* src/app/app.module.ts */
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { SubjectCreateComponent } from './subject-create/subject-create.component';
import { SubjectListComponent } from './subject-list/subject-list.component';

import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { SubjectEditComponent } from './subject-edit/subject-edit.component';
import { SubjectResourcesComponent } from './subject-resources/subject-resources.component';

@NgModule({
  declarations: [
    AppComponent,
    SubjectCreateComponent,
    SubjectListComponent,
    SubjectEditComponent,
    SubjectResourcesComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    FormsModule,
    HttpClientModule,
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
