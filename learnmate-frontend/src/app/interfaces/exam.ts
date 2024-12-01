// src/app/interfaces/exam.ts
export interface IAnswer {
  id?: string;
  text: string;
}

export interface IQuestion {
  id?: string;
  text: string;
  answers: IAnswer[];
}

export interface IExam {
  id?: string;
  date: string;
  subject_id?: number;
  questions: IQuestion[];
}
