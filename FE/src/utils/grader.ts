import type { QuizQuestion } from '../types/exercise';

export interface QuestionGradingResult {
  question_id: string;
  is_correct: boolean;
  selected_option_ids: string[];
  correct_option_ids: string[];
  explanation: string;
}

export interface QuizGradingSummary {
  total_questions: number;
  correct_count: number;
  score: number; // Thang 10, làm tròn 1 chữ số thập phân
  results: Record<string, QuestionGradingResult>;
}

/**
 * Thuật toán FE tự chấm điểm trắc nghiệm theo tài liệu README mục 6.4:
 * - So sánh tập hợp ID đã chọn với correct_option_ids, không phân biệt thứ tự
 * - Đúng hoàn toàn -> 1 điểm; Sai, thiếu hoặc thừa -> 0 điểm
 * - score = 10 * (số câu đúng / tổng số câu)
 */
export function gradeQuiz(
  questions: QuizQuestion[],
  answers: Record<string, string[]>
): QuizGradingSummary {
  let correctCount = 0;
  const results: Record<string, QuestionGradingResult> = {};

  for (const q of questions) {
    const selected = answers[q.question_id] || [];
    const correct = q.correct_option_ids || [];

    const selectedSet = new Set(selected);
    const correctSet = new Set(correct);

    const isMatch =
      selectedSet.size === correctSet.size &&
      [...selectedSet].every((id) => correctSet.has(id));

    if (isMatch) {
      correctCount++;
    }

    results[q.question_id] = {
      question_id: q.question_id,
      is_correct: isMatch,
      selected_option_ids: selected,
      correct_option_ids: correct,
      explanation: q.explanation || '',
    };
  }

  const total = questions.length;
  const score = total > 0 ? Math.round((10 * correctCount / total) * 10) / 10 : 0;

  return {
    total_questions: total,
    correct_count: correctCount,
    score,
    results,
  };
}
