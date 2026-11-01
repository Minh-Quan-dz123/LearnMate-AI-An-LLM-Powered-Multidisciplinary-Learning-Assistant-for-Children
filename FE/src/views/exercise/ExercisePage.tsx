
import { useState, type CSSProperties } from 'react';
import { House } from 'lucide-react';

import type { ChildProfile } from '../../types/child';

import type {
  Subject, Level, QuestionType,
  QuizGenerateData, OpenGenerateData, OpenEvaluateData,
} from '../../types/exercise';

import { SUBJECT_TOPICS } from '../../constants/subjects';
import { exerciseService } from '../../services/exerciseService';
import {
  gradeQuiz,
  type QuizGradingSummary,
} from '../../utils/grader';

interface Props {
  child: ChildProfile;

  // Hàm điều hướng về màn hình chọn hồ sơ trẻ.
  // Hàm này được truyền từ App.tsx.
  onGoHome: () => void;
}

type Stage = 'config' | 'doing' | 'result';

type QuizType =
  | 'Trắc nghiệm một đáp án'
  | 'Trắc nghiệm nhiều đáp án';

// CSS đơn giản, tái sử dụng theme đang có của FE
const panel: CSSProperties = {
  background: 'white',
  borderRadius: 20,
  padding: 24,
  boxShadow: 'var(--shadow-sm)',
  marginBottom: 20,
};

const field: CSSProperties = {
  width: '100%',
  padding: 12,
  borderRadius: 12,
  border: '2px solid var(--color-border)',
  font: 'inherit',
};

const label: CSSProperties = {
  display: 'block',
  fontWeight: 700,
  marginBottom: 6,
};

export function ExercisePage({ child, onGoHome }: Props) {  // 1. STATE CẤU HÌNH
  const [subject, setSubject] =
    useState<Subject>('Khoa học tự nhiên');

  const [topicChoice, setTopicChoice] = useState(
    SUBJECT_TOPICS['Khoa học tự nhiên'][0]
  );

  const [customTopic, setCustomTopic] = useState('');
  const [level, setLevel] = useState<Level>('Cơ bản');

  const [questionType, setQuestionType] =
    useState<QuestionType>('Trắc nghiệm một đáp án');

  const [questionCount, setQuestionCount] = useState(2);

  // 2. STATE BÀI TẬP
  const [stage, setStage] = useState<Stage>('config');

  const [quiz, setQuiz] = useState<QuizGenerateData | null>(null);
  const [open, setOpen] = useState<OpenGenerateData | null>(null);

  const [selected, setSelected] =
    useState<Record<string, string[]>>({});

  const [written, setWritten] =
    useState<Record<string, string>>({});

  // 3. STATE KẾT QUẢ
  const [quizResult, setQuizResult] =
    useState<QuizGradingSummary | null>(null);

  const [openResults, setOpenResults] =
    useState<Record<string, OpenEvaluateData>>({});

  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const topic =
    topicChoice === 'Chủ đề khác'
      ? customTopic.trim()
      : topicChoice;

  const isOpen = questionType === 'Câu trả lời mở';

  /**
   * 4. SINH BÀI TẬP
   * - Gọi Module 1 nếu là trắc nghiệm.
   * - Gọi Module 2 nếu là câu hỏi mở.
   */
  const generate = async () => {
    if (!topic || topic.length > 100) {
      setError('Chủ đề phải có từ 1 đến 100 ký tự.');
      return;
    }

    if (
      !Number.isInteger(questionCount) ||
      questionCount < 1 ||
      questionCount > 5
    ) {
      setError('Số câu phải từ 1 đến 5.');
      return;
    }

    setError('');
    setBusy(true);
    setStatus('Đang tạo bài tập...');

    try {
      const common = {
        child_id: child.child_id,
        subject,
        topic,
        level,
        question_count: questionCount,
      };

      if (isOpen) {
        const res = await exerciseService.generateOpen({
          ...common,
          question_type: 'Câu trả lời mở',
        });

        if (!res.success || !res.data) {
          throw new Error(res.message);
        }

        setOpen(res.data);
        setQuiz(null);
      } else {
        const res = await exerciseService.generateQuiz({
          ...common,
          question_type: questionType as QuizType,
        });

        if (!res.success || !res.data) {
          throw new Error(res.message);
        }

        setQuiz(res.data);
        setOpen(null);
      }

      // Xóa đáp án và kết quả của bài trước
      setSelected({});
      setWritten({});
      setQuizResult(null);
      setOpenResults({});

      setStage('doing');
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Không tạo được bài tập.'
      );
    } finally {
      setBusy(false);
      setStatus('');
    }
  };

  /**
   * 5. CHỌN ĐÁP ÁN
   * - Một đáp án: thay lựa chọn cũ.
   * - Nhiều đáp án: thêm hoặc bỏ lựa chọn.
   */
  const selectAnswer = (
    questionId: string,
    optionId: string
  ) => {
    setSelected((prev) => {
      const values = prev[questionId] ?? [];

      const next =
        questionType === 'Trắc nghiệm một đáp án'
          ? [optionId]
          : values.includes(optionId)
            ? values.filter((id) => id !== optionId)
            : [...values, optionId];

      return {
        ...prev,
        [questionId]: next,
      };
    });
  };

  /**
   * 6. NỘP BÀI
   * - Module 1: gradeQuiz() chạy trên FE.
   * - Module 2: gọi BE chấm lần lượt từng câu.
   */
  const submit = async () => {
    setError('');

    if (quiz) {
      setQuizResult(gradeQuiz(quiz.questions, selected));
      setStage('result');
      return;
    }

    if (!open) return;

    const missing = open.questions.find(
      (q) => !(written[q.question_id] ?? '').trim()
    );

    if (missing) {
      setError('Con hãy trả lời đầy đủ các câu trước khi nộp nhé.');
      return;
    }

    setBusy(true);

    try {
      const results: Record<string, OpenEvaluateData> = {};

      for (let i = 0; i < open.questions.length; i++) {
        const q = open.questions[i];

        setStatus(
          `AI đang chấm câu ${i + 1}/${open.questions.length}...`
        );

        const res = await exerciseService.evaluateOpen({
          child_id: child.child_id,
          question_id: q.question_id,
          question: q.content,
          answer: written[q.question_id].trim(),
          evaluation_criteria: q.evaluation_criteria,
          subject,
          topic,
          level,
        });

        if (!res.success || !res.data) {
          throw new Error(res.message);
        }

        results[q.question_id] = res.data;
      }

      setOpenResults(results);
      setStage('result');
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Không thể chấm bài.'
      );
    } finally {
      setBusy(false);
      setStatus('');
    }
  };

  // Điểm trung bình các câu trả lời mở
  const openScore = open
    ? Math.round(
        (
          open.questions.reduce(
            (sum, q) =>
              sum + (openResults[q.question_id]?.score ?? 0),
            0
          ) / open.questions.length
        ) * 10
      ) / 10
    : 0;

  return (
    <main
      style={{
        maxWidth: 850,
        margin: '24px auto',
        padding: '0 16px 40px',
      }}
    >
      <h1 style={{ marginBottom: 16 }}>
        Học cùng {child.name} 🌟
      </h1>

      {error && (
        <div
          role="alert"
          style={{
            ...panel,
            color: '#C92A2A',
            background: '#FFF5F5',
          }}
        >
          {error}
        </div>
      )}

        {/* MÀN HÌNH CẤU HÌNH */}
        {stage === 'config' && (
        <section style={panel}>

            {/* NÚT QUAY VỀ MÀN HÌNH CHÍNH */}
            <button
            type="button"
            className="btn btn-outline"
            onClick={onGoHome}
            disabled={busy}
            style={{
                marginBottom: 20,
                padding: '9px 14px',
            }}
            >
            <House size={18} aria-hidden="true" />
            Về màn hình chính
            </button>

            {/* TIÊU ĐỀ CẤU HÌNH */}
            <h2 style={{ marginBottom: 16 }}>
            Cấu hình bài tập
            </h2>

          <div style={{ display: 'grid', gap: 16 }}>
            <div>
              <label style={label}>Môn học</label>

              <select
                style={field}
                value={subject}
                onChange={(e) => {
                  const next = e.target.value as Subject;
                  setSubject(next);
                  setTopicChoice(SUBJECT_TOPICS[next][0]);
                }}
              >
                {(Object.keys(SUBJECT_TOPICS) as Subject[]).map(
                  (s) => <option key={s}>{s}</option>
                )}
              </select>
            </div>

            <div>
              <label style={label}>Chủ đề</label>

              <select
                style={field}
                value={topicChoice}
                onChange={(e) => setTopicChoice(e.target.value)}
              >
                {SUBJECT_TOPICS[subject].map(
                  (t) => <option key={t}>{t}</option>
                )}

                <option>Ngẫu nhiên</option>
                <option>Chủ đề khác</option>
              </select>
            </div>

            {topicChoice === 'Chủ đề khác' && (
              <div>
                <label style={label}>Nhập chủ đề</label>

                <input
                  style={field}
                  maxLength={100}
                  value={customTopic}
                  placeholder="Ví dụ: Các hành tinh"
                  onChange={(e) => setCustomTopic(e.target.value)}
                />
              </div>
            )}

            <div>
              <label style={label}>Mức độ</label>

              <select
                style={field}
                value={level}
                onChange={(e) =>
                  setLevel(e.target.value as Level)
                }
              >
                <option>Cơ bản</option>
                <option>Nâng cao</option>
              </select>
            </div>

            <div>
              <label style={label}>Dạng bài</label>

              <select
                style={field}
                value={questionType}
                onChange={(e) =>
                  setQuestionType(e.target.value as QuestionType)
                }
              >
                <option>Trắc nghiệm một đáp án</option>
                <option>Trắc nghiệm nhiều đáp án</option>
                <option>Câu trả lời mở</option>
              </select>
            </div>

            <div>
              <label style={label}>Số câu (1–5)</label>

              <input
                style={field}
                type="number"
                min={1}
                max={5}
                value={questionCount}
                onChange={(e) =>
                  setQuestionCount(Number(e.target.value))
                }
              />
            </div>

            <button
              className="btn btn-primary"
              disabled={busy}
              onClick={generate}
            >
              {busy ? status : 'Tạo bài tập'}
            </button>
          </div>
        </section>
      )}

      {/* MÀN HÌNH LÀM BÀI */}
      {stage === 'doing' && (
        <>
          <h2 style={{ marginBottom: 16 }}>
            {quiz?.question_type ?? open?.question_type}
          </h2>

          {quiz?.questions.map((q, index) => (
            <section key={q.question_id} style={panel}>
              <h3>
                Câu {index + 1}: {q.content}
              </h3>

              {quiz.question_type ===
                'Trắc nghiệm nhiều đáp án' && (
                <p>Chọn tất cả đáp án đúng.</p>
              )}

              {q.options.map((opt) => (
                <label
                  key={opt.option_id}
                  style={{
                    display: 'flex',
                    gap: 10,
                    padding: 10,
                    cursor: 'pointer',
                  }}
                >
                  <input
                    type={
                      quiz.question_type === 'Trắc nghiệm một đáp án'
                        ? 'radio'
                        : 'checkbox'
                    }
                    name={q.question_id}
                    checked={
                      (selected[q.question_id] ?? []).includes(
                        opt.option_id
                      )
                    }
                    onChange={() =>
                      selectAnswer(q.question_id, opt.option_id)
                    }
                  />

                  {opt.option_id}. {opt.text}
                </label>
              ))}
            </section>
          ))}

          {open?.questions.map((q, index) => (
            <section key={q.question_id} style={panel}>
              <h3>
                Câu {index + 1}: {q.content}
              </h3>

              <p style={{ color: 'var(--color-text-muted)' }}>
                {q.answer_hint}
              </p>

              <textarea
                style={{ ...field, marginTop: 12 }}
                rows={3}
                maxLength={1000}
                placeholder="Con hãy viết câu trả lời ở đây..."
                value={written[q.question_id] ?? ''}
                onChange={(e) =>
                  setWritten((old) => ({
                    ...old,
                    [q.question_id]: e.target.value,
                  }))
                }
              />
            </section>
          ))}

          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 12,
            }}
          >
            <button
              className="btn btn-outline"
              disabled={busy}
              onClick={() => setStage('config')}
            >
              Quay lại
            </button>

            <button
              className="btn btn-primary"
              disabled={busy}
              onClick={submit}
            >
              {busy ? status : 'Nộp bài'}
            </button>
          </div>
        </>
      )}

      {/* MÀN HÌNH KẾT QUẢ */}
      {stage === 'result' && (
        <>
          <section style={panel}>
            <h2>Kết quả của {child.name} 🎉</h2>

            <p
              style={{
                fontSize: 28,
                fontWeight: 800,
                marginTop: 8,
              }}
            >
              {quiz ? quizResult?.score : openScore} / 10 điểm
            </p>

            {quiz && (
              <p>
                Đúng {quizResult?.correct_count}/
                {quizResult?.total_questions} câu
              </p>
            )}

            {open && (
              <p>
                Điểm trung bình các câu trả lời mở
                (AI đánh giá tham khảo).
              </p>
            )}
          </section>

          {quiz?.questions.map((q, i) => {
            const result = quizResult?.results[q.question_id];

            return (
              <section key={q.question_id} style={panel}>
                <h3>
                  Câu {i + 1}: {q.content}
                </h3>

                <p
                  style={{
                    color: result?.is_correct
                      ? '#2B8A3E'
                      : '#C92A2A',
                  }}
                >
                  {result?.is_correct ? '✓ Đúng' : '✗ Chưa đúng'}
                </p>

                <p>
                  Con chọn:
                  {' '}{result?.selected_option_ids.join(', ') || 'Chưa chọn'}
                </p>

                <p>
                  Đáp án đúng: {q.correct_option_ids.join(', ')}
                </p>

                <p>Giải thích: {q.explanation}</p>
              </section>
            );
          })}

          {open?.questions.map((q, i) => {
            const result = openResults[q.question_id];

            return (
              <section key={q.question_id} style={panel}>
                <h3>
                  Câu {i + 1}: {q.content}
                </h3>

                <p>Con trả lời: {written[q.question_id]}</p>

                <p>
                  <strong>Điểm: {result?.score}/10</strong>
                </p>

                <p>{result?.feedback}</p>

                {result?.strengths?.length > 0 && (
                  <p>
                    Điểm mạnh: {result.strengths.join('; ')}
                  </p>
                )}

                {result?.suggestions?.length > 0 && (
                  <p>
                    Gợi ý: {result.suggestions.join('; ')}
                  </p>
                )}

                {result?.sample_answer && (
                  <p>
                    Trả lời tham khảo: {result.sample_answer}
                  </p>
                )}
              </section>
            );
          })}

            {/* NHÓM NÚT ĐIỀU HƯỚNG SAU KHI LÀM BÀI */}
            <div
            style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 12,
            }}
            >
            {/* NÚT LÀM BÀI MỚI */}
            <button
                type="button"
                className="btn btn-primary"
                onClick={() => {
                setError('');
                setStage('config');
                }}
            >
                Làm bài mới
            </button>

            {/* NÚT VỀ MÀN HÌNH CHÍNH */}
            <button
                type="button"
                className="btn btn-outline"
                onClick={onGoHome}
            >
                <House size={18} aria-hidden="true" />
                Về màn hình chính
            </button>
            </div>
        </>
      )}
    </main>
  );
}