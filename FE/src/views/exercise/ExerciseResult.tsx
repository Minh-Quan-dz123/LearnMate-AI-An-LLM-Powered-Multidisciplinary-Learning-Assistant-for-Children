
/**
 * FILE: ExerciseResult.tsx
 *
 * MỤC ĐÍCH:
 * - Hiển thị điểm tổng kết.
 * - Hiển thị lời khen.
 * - Hiển thị kết quả từng câu hỏi.
 * - Điều hướng làm bài mới / về trang chính.
 */

import {
  House,
  RotateCcw,
  Volume2,
} from 'lucide-react';

import type { CSSProperties } from 'react';

import type {
  QuizGenerateData,
  OpenGenerateData,
  OpenEvaluateData,
} from '../../types/exercise';

import type {
  QuizGradingSummary,
} from '../../utils/grader';

const panel: CSSProperties = {
  background: 'white',
  borderRadius: 20,
  padding: 24,
  boxShadow: 'var(--shadow-sm)',
  marginBottom: 20,
};

interface Props {
  childName: string;
  finalScore: number;
  total: number;

  praise: {
    title: string;
    detail: string;
  };

  quiz: QuizGenerateData | null;
  open: OpenGenerateData | null;
  quizResult: QuizGradingSummary | null;

  openResults: Record<
    string,
    OpenEvaluateData
  >;

  written: Record<string, string>;

  onReadPraise: () => void;
  onNewExercise: () => void;
  onGoHome: () => void;
}

export function ExerciseResult({
  childName,
  finalScore,
  total,
  praise,
  quiz,
  open,
  quizResult,
  openResults,
  written,
  onReadPraise,
  onNewExercise,
  onGoHome,
}: Props) {
  return (
    <>
      {/* =========================================
          TỔNG KẾT ĐIỂM
      ========================================= */}

      <section style={panel}>
        <h2>
          Kết quả của {childName} 🎉
        </h2>

        <p
          style={{
            fontSize: 32,
            fontWeight: 800,
            marginTop: 12,
          }}
        >
          {finalScore} / 10 điểm
        </p>

        {quiz && (
          <p>
            Con trả lời đúng{' '}
            {quizResult?.correct_count}/
            {quizResult?.total_questions} câu.
          </p>
        )}

        {open && (
          <p>
            Điểm trung bình của {total} câu
            (AI đánh giá tham khảo).
          </p>
        )}

        {/* LỜI KHEN */}

        <div className="lesson-praise">
          <h3>{praise.title}</h3>

          <p>{praise.detail}</p>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={onReadPraise}
          >
            <Volume2 size={18} />
            Nghe lại lời khen
          </button>
        </div>
      </section>

      {/* =========================================
          KẾT QUẢ TRẮC NGHIỆM
      ========================================= */}

      {quiz?.questions.map((q, index) => {
        const result =
          quizResult?.results[q.question_id];

        return (
          <section
            key={q.question_id}
            style={panel}
          >
            <h3>
              Câu {index + 1}: {q.content}
            </h3>

            <p
              style={{
                color: result?.is_correct
                  ? '#2B8A3E'
                  : '#C92A2A',
                fontWeight: 700,
                marginTop: 12,
              }}
            >
              {result?.is_correct
                ? '✓ Chính xác!'
                : '✗ Chưa đúng'}
            </p>

            <p>
              <strong>Con chọn: </strong>
              {result?.selected_option_ids.join(', ')
                || 'Chưa chọn'}
            </p>

            <p>
              <strong>Đáp án đúng: </strong>
              {q.correct_option_ids.join(', ')}
            </p>

            <p>
              <strong>Giải thích: </strong>
              {q.explanation}
            </p>
          </section>
        );
      })}

      {/* =========================================
          KẾT QUẢ CÂU TRẢ LỜI MỞ
      ========================================= */}

      {open?.questions.map((q, index) => {
        const result =
          openResults[q.question_id];

        return (
          <section
            key={q.question_id}
            style={panel}
          >
            <h3>
              Câu {index + 1}: {q.content}
            </h3>

            <p style={{ marginTop: 12 }}>
              <strong>Con trả lời: </strong>
              {written[q.question_id]}
            </p>

            <p>
              <strong>
                Điểm: {result?.score}/10
              </strong>
            </p>

            {result?.feedback && (
              <p>
                <strong>Nhận xét: </strong>
                {result.feedback}
              </p>
            )}

            {result?.strengths?.length > 0 && (
              <p>
                <strong>Điểm mạnh: </strong>
                {result.strengths.join('; ')}
              </p>
            )}

            {result?.suggestions?.length > 0 && (
              <p>
                <strong>Gợi ý: </strong>
                {result.suggestions.join('; ')}
              </p>
            )}

            {result?.sample_answer && (
              <p>
                <strong>
                  Trả lời tham khảo:
                </strong>
                {' '}
                {result.sample_answer}
              </p>
            )}
          </section>
        );
      })}

      {/* =========================================
          ĐIỀU HƯỚNG
      ========================================= */}

      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <button
          type="button"
          className="btn btn-primary"
          onClick={onNewExercise}
        >
          <RotateCcw size={18} />
          Làm bài mới
        </button>

        <button
          type="button"
          className="btn btn-outline"
          onClick={onGoHome}
        >
          <House size={18} />
          Về màn hình chính
        </button>
      </div>
    </>
  );
}
