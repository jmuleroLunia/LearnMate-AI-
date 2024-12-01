// src/app/interfaces/batch-exam-response.ts
import {IExam} from "./exam";

export interface IBatchExamResponse {
  exams: IExam[];
  errors: string[];
}
