// src/app/subject-mock-exam/subject-mock-exam.component.ts

import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { IExam, IQuestion } from '../interfaces/exam';
import { FormBuilder, FormGroup } from '@angular/forms';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import {SubjectService} from "../subject.service";

@Component({
  selector: 'app-subject-mock-exam',
  templateUrl: './subject-mock-exam.component.html',
  styleUrls: ['./subject-mock-exam.component.scss']
})
export class SubjectMockExamComponent implements OnInit, OnDestroy {
  // Essential properties
  subjectId!: number;
  exam?: IExam;
  numQuestions: number = 15;

  // UI state properties
  loading: boolean = false;
  errorMessage: string = '';
  progressPercentage: number = 0;
  showResults: boolean = false;

  // Form and question tracking
  examForm!: FormGroup;
  markedQuestions: { [key: number]: boolean } = {};
  selectedAnswers: { [key: number]: number } = {};

  // Answer verification properties
  correctAnswers: { [key: number]: string } = {};
  explanations: { [key: number]: string } = {};
  confidenceScores: { [key: number]: number } = {};
  sources: { [key: number]: string[] } = {};
  isAnswerLoading: { [key: number]: boolean } = {};

  // Results tracking
  score: number = 0;
  totalQuestions: number = 0;

  // Component lifecycle
  private destroy$ = new Subject<void>();

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private subjectService: SubjectService,
    private fb: FormBuilder
  ) {}

  ngOnInit(): void {
    this.subjectId = Number(this.route.snapshot.paramMap.get('id'));
    if (!this.subjectId) {
      this.errorMessage = 'ID de asignatura no válido';
      return;
    }
    this.generateMockExam();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  generateMockExam(): void {
    this.resetExamState();
    this.loading = true;

    this.subjectService.generateMockExam(this.subjectId, this.numQuestions)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response: any) => {
          this.exam = response;
          this.initializeForm();
          this.loading = false;
        },
        error: (error: any) => {
          console.error('Error generando examen:', error);
          this.errorMessage = 'Error al generar el examen. Por favor, inténtelo de nuevo.';
          this.loading = false;
        }
      });
  }

  private resetExamState(): void {
    this.loading = false;
    this.errorMessage = '';
    this.exam = undefined;
    this.progressPercentage = 0;
    this.markedQuestions = {};
    this.correctAnswers = {};
    this.explanations = {};
    this.confidenceScores = {};
    this.sources = {};
    this.isAnswerLoading = {};
    this.showResults = false;
    this.score = 0;
  }

  initializeForm(): void {
    if (!this.exam) return;

    const group: { [key: string]: any } = {};
    this.exam.questions.forEach((_, index) => {
      group[`question${index}`] = [null];
      this.markedQuestions[index] = false;
    });
    this.examForm = this.fb.group(group);

    // Subscribe to form changes
    this.examForm.valueChanges
      .pipe(takeUntil(this.destroy$))
      .subscribe(values => {
        this.updateProgress();
        this.updateSelectedAnswers(values);
      });
  }

  private updateSelectedAnswers(values: any): void {
    Object.keys(values).forEach(key => {
      const index = parseInt(key.replace('question', ''));
      if (!isNaN(index)) {
        this.selectedAnswers[index] = values[key];
      }
    });
  }

  updateProgress(): void {
    if (!this.exam) return;

    const totalQuestions = this.exam.questions.length;
    const answeredQuestions = Object.values(this.examForm.value)
      .filter(value => value !== null).length;
    this.progressPercentage = (answeredQuestions / totalQuestions) * 100;
  }

  toggleMarkQuestion(index: number): void {
    this.markedQuestions[index] = !this.markedQuestions[index];
  }

  scrollToQuestion(index: number): void {
    const element = document.getElementById(`question${index}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  // En el componente TypeScript
getCorrectAnswer(questionIndex: number): void {
    // Si ya está cargando o ya tiene respuesta, no hacer nada
    if (this.isAnswerLoading[questionIndex] || this.correctAnswers[questionIndex]) {
      return;
    }

    const question = this.exam?.questions[questionIndex];
    if (!question) return;

    this.isAnswerLoading[questionIndex] = true;

    const questionPayload: IQuestion = {
      text: question.text,
      answers: question.answers.map((ans) => ({ text: ans.text })),
    };

    // Subscribirse una sola vez y manejar la limpieza
    this.subjectService.getCorrectAnswer(questionPayload, this.subjectId)
      .subscribe({
        next: (response) => {
          if (response && response.correct_answer) {
            this.correctAnswers[questionIndex] = response.correct_answer;
          }
          this.isAnswerLoading[questionIndex] = false;
        },
        error: (error) => {
          console.error('Error al obtener la respuesta correcta:', error);
          this.isAnswerLoading[questionIndex] = false;
        },
        complete: () => {
          this.isAnswerLoading[questionIndex] = false;
        }
      });
  }
  private parseAnswerResponse(response: string): {
    answer: string;
    explanation: string;
    confidenceScore?: number;
    sources?: string[];
  } {
    // Extract the answer number from the beginning of the response
    const answerMatch = response.match(/^(\d+)/);
    if (!answerMatch) {
      return {
        answer: response,
        explanation: 'No se pudo extraer una explicación.'
      };
    }

    const answer = answerMatch[1];
    let remainingText = response.substring(answerMatch[0].length).trim();

    // Look for confidence score
    const confidenceMatch = remainingText.match(/Confianza:\s*(\d+(?:\.\d+)?)/i);
    let confidenceScore: number | undefined;
    if (confidenceMatch) {
      confidenceScore = parseFloat(confidenceMatch[1]);
      remainingText = remainingText.replace(confidenceMatch[0], '').trim();
    }

    // Look for sources
    const sourcesMatch = remainingText.match(/Fuentes:\s*([^\n]+)/i);
    let sources: string[] | undefined;
    if (sourcesMatch) {
      sources = sourcesMatch[1].split(',').map(s => s.trim());
      remainingText = remainingText.replace(sourcesMatch[0], '').trim();
    }

    return {
      answer,
      explanation: remainingText,
      confidenceScore,
      sources
    };
  }

  submitExam(): void {
    if (!this.exam || !this.examForm.valid) return;

    this.showResults = true;
    this.totalQuestions = this.exam.questions.length;

    // Get all correct answers before showing results
    this.exam.questions.forEach((_, index) => {
      if (!this.correctAnswers[index]) {
        this.getCorrectAnswer(index);
      }
    });

    // Calculate score
    this.calculateScore();
  }

  private calculateScore(): void {
    if (!this.exam) return;

    let correct = 0;
    Object.entries(this.selectedAnswers).forEach(([index, selectedAnswer]) => {
      const correctAnswer = this.correctAnswers[Number(index)];
      if (correctAnswer && selectedAnswer === Number(correctAnswer) - 1) {
        correct++;
      }
    });

    this.score = (correct / this.exam.questions.length) * 100;
  }

  restartExam(): void {
    this.generateMockExam();
  }

  goToSubject(): void {
    this.router.navigate(['/subjects', this.subjectId]);
  }
}
