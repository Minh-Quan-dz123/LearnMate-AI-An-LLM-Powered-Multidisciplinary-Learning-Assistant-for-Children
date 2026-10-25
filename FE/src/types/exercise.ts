export type Subject = 'Khoa học tự nhiên' | 'Đạo đức' | 'Kỹ năng sống';
export type Level = 'Cơ bản' | 'Nâng cao';
export type QuestionType = 'Trắc nghiệm một đáp án' | 'Trắc nghiệm nhiều đáp án' | 'Câu trả lời mở';

export interface QuizOption {
  option_id: string; // "A", "B", "C", ...
  text: string;
}

export interface QuizQuestion {
  question_id: string;
  content: string;
  options: QuizOption[];
  correct_option_ids: string[];
  explanation: string;
}

export interface QuizGenerateRequest {
  child_id: number;
  subject: Subject | string;
  topic: string;
  level: Level;
  question_type: 'Trắc nghiệm một đáp án' | 'Trắc nghiệm nhiều đáp án';
  question_count: number;
}

export interface QuizGenerateData {
  exercise_id: string;
  subject: string;
  topic: string;
  level: string;
  question_type: string;
  questions: QuizQuestion[];
}

export interface OpenQuestion {
  question_id: string;
  content: string;
  answer_hint: string;
  evaluation_criteria: string[];
}

export interface OpenGenerateRequest {
  child_id: number;
  subject: Subject | string;
  topic: string;
  level: Level;
  question_type: 'Câu trả lời mở';
  question_count: number;
}

export interface OpenGenerateData {
  exercise_id: string;
  question_type: string;
  questions: OpenQuestion[];
}

export interface OpenEvaluateRequest {
  child_id: number;
  question_id: string;
  question: string;
  answer: string;
  evaluation_criteria: string[];
  subject: string;
  topic: string;
  level: string;
}

export interface OpenEvaluateData {
  question_id: string;
  score: number;
  is_appropriate: boolean;
  feedback: string;
  strengths: string[];
  suggestions: string[];
  sample_answer: string;
}
