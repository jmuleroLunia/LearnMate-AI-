// src/app/subject-exams/subject-exams.component.ts
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { SubjectService } from '../subject.service';
import { IExam } from '../interfaces/exam';
import { IBatchExamResponse } from '../interfaces/batch-exam-response';

@Component({
  selector: 'app-subject-exams',
  templateUrl: './subject-exams.component.html',
  styleUrls: ['./subject-exams.component.css']
})
export class SubjectExamsComponent implements OnInit {
  subjectId: number | undefined;
  exams: IExam[] = [];
  newExam: { date: string } = { date: '' };
  selectedFiles: File[] = [];
  errors: string[] = [];

  constructor(
    private subjectService: SubjectService,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.route.paramMap.subscribe(params => {
      const idParam = params.get('id');
      if (idParam) {
        this.subjectId = +idParam;
        this.loadExams();
      }
    });
  }

  loadExams() {
    if (this.subjectId) {
      this.subjectService.getExams(this.subjectId).subscribe({
        next: (exams) => {
          this.exams = exams;
        },
        error: (error) => {
          console.error('Error loading exams:', error);
        }
      });
    }
  }

  onFileSelected(event: any) {
    this.selectedFiles = Array.from(event.target.files);
  }

  addExam() {
    if (this.subjectId && this.newExam.date && this.selectedFiles.length > 0) {
      this.subjectService.addExam(this.subjectId, this.newExam.date, this.selectedFiles).subscribe({
        next: (response: IBatchExamResponse) => {
          this.exams = this.exams.concat(response.exams);
          this.errors = response.errors;
          this.newExam = { date: '' };
          this.selectedFiles = [];
        },
        error: (error) => {
          console.error('Error adding exams:', error);
        }
      });
    } else {
      console.error('Missing required data:', {
        subjectId: this.subjectId,
        date: this.newExam.date,
        hasFiles: this.selectedFiles.length > 0
      });
    }
  }

  deleteExam(examId: string) {
    if (confirm('¿Estás seguro de que deseas eliminar este examen?')) {
      this.subjectService.deleteExam(examId).subscribe({
        next: () => {
          this.exams = this.exams.filter(exam => exam.id !== examId);
        },
        error: (error) => {
          console.error('Error deleting exam:', error);
        }
      });
    }
  }
}
