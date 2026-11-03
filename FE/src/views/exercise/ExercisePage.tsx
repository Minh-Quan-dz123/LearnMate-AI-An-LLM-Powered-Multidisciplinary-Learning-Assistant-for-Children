
/**
 * FILE: ExercisePage.tsx
 *
 * MỤC ĐÍCH:
 * - Quản lý state bài tập.
 * - Gọi API tạo bài.
 * - Xử lý nộp từng câu.
 * - Tính điểm và nhận xét.
 * - Điều phối ba màn hình:
 *   ExerciseSetup / ExerciseDoing / ExerciseResult.
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react';

import type { ChildProfile } from '../../types/child';

import type {
  Level,
  OpenEvaluateData,
  OpenGenerateData,
  QuestionType,
  QuizGenerateData,
  Subject,
} from '../../types/exercise';

import { SUBJECT_TOPICS } from '../../constants/subjects';
import { exerciseService } from '../../services/exerciseService';

import {
  gradeQuiz,
  type QuizGradingSummary,
} from '../../utils/grader';

import { useVoiceInput } from '../../hooks/useVoiceInput';

import { ExerciseSetup } from './ExerciseSetup';
import { ExerciseDoing } from './ExerciseDoing';
import { ExerciseResult } from './ExerciseResult';

import './ExercisePage.css';

// =====================================================
// 1. KIỂU DỮ LIỆU
// =====================================================

interface Props {
  child: ChildProfile;
  onGoHome: () => void;
}

type Stage = 'config' | 'doing' | 'result';

type QuizType =
  | 'Trắc nghiệm một đáp án'
  | 'Trắc nghiệm nhiều đáp án';

// =====================================================
// 2. LỜI KHEN THEO ĐIỂM
// =====================================================

function getPraise(score: number) {
  if (score >= 9) {
    return {
      title: '🏆 Xuất sắc!',
      detail:
        'Con làm rất giỏi! Hãy tiếp tục khám phá những điều thú vị nhé!',
    };
  }

  if (score >= 7) {
    return {
      title: '🌟 Tốt lắm!',
      detail:
        'Con đã nắm được nhiều kiến thức rồi đấy! Cố gắng phát huy nhé!',
    };
  }

  if (score >= 5) {
    return {
      title: '💪 Cố gắng rất tốt!',
      detail:
        'Con đã có tiến bộ! Hãy luyện tập thêm để ngày càng giỏi hơn nhé!',
    };
  }

  return {
    title: '🌱 Cùng thử lại nhé!',
    detail:
      'Con đã hoàn thành bài tập rồi! Đừng ngại thử lại và học thêm điều mới nhé!',
  };
}

// =====================================================
// 3. TEXT-TO-SPEECH
// =====================================================


function speak(text: string) {
  if (
    typeof window === 'undefined' ||
    !('speechSynthesis' in window)
  ) {
    return;
  }

  const synth = window.speechSynthesis;
  synth.cancel();

  const utterance = new SpeechSynthesisUtterance(text);

  // Giọng đọc phù hợp với trẻ em
  utterance.lang = 'vi-VN';
  utterance.rate = 0.87;
  utterance.pitch = 1.12;
  utterance.volume = 1;

  const voices = synth.getVoices();

  const vietnameseVoices = voices.filter(
    (voice) => voice.lang.toLowerCase().startsWith('vi')
  );

  // Ưu tiên giọng nữ tiếng Việt nếu có
  const femaleVoice = vietnameseVoices.find(
    (voice) =>
      /hoaimy|hoài my|female|thao|thảo|linh|nữ/i.test(
        voice.name
      )
  );

  const selectedVoice =
    femaleVoice ?? vietnameseVoices[0];

  if (selectedVoice) {
    utterance.voice = selectedVoice;
  }

  synth.speak(utterance);
}


function stopReading() {
  if (
    typeof window !== 'undefined' &&
    'speechSynthesis' in window
  ) {
    window.speechSynthesis.cancel();
  }
}

// =====================================================
// 4. COMPONENT CHÍNH
// =====================================================

export function ExercisePage({
  child,
  onGoHome,
}: Props) {
  // ===================================================
  // 4.1. STATE CẤU HÌNH
  // ===================================================

  const [subject, setSubject] = useState<Subject>(
    'Khoa học tự nhiên'
  );

  const [topicChoice, setTopicChoice] = useState(
    SUBJECT_TOPICS['Khoa học tự nhiên'][0]
  );

  const [customTopic, setCustomTopic] = useState('');

  const [level, setLevel] = useState<Level>(
    'Cơ bản'
  );

  const [questionType, setQuestionType] =
    useState<QuestionType>(
      'Trắc nghiệm một đáp án'
    );

  const [questionCount, setQuestionCount] =
    useState(2);

  // ===================================================
  // 4.2. STATE BÀI TẬP
  // ===================================================

  const [stage, setStage] =
    useState<Stage>('config');

  const [quiz, setQuiz] =
    useState<QuizGenerateData | null>(null);

  const [open, setOpen] =
    useState<OpenGenerateData | null>(null);

  const [currentIndex, setCurrentIndex] =
    useState(0);

  const [completedCount, setCompletedCount] =
    useState(0);

  const [selected, setSelected] =
    useState<Record<string, string[]>>({});

  const [written, setWritten] =
    useState<Record<string, string>>({});

  const [quizResult, setQuizResult] =
    useState<QuizGradingSummary | null>(null);

  const [openResults, setOpenResults] =
    useState<Record<string, OpenEvaluateData>>({});

  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const [autoRead, setAutoRead] = useState(true);

  const [
    finishedSpeechQuestionId,
    setFinishedSpeechQuestionId,
  ] = useState<string | null>(null);

  // ===================================================
  // 4.3. SPEECH-TO-TEXT
  // ===================================================

  const onSpeechText = useCallback(
    (questionId: string, text: string) => {
      setWritten((prev) => ({
        ...prev,
        [questionId]: text,
      }));
    },
    []
  );

  const voice = useVoiceInput(onSpeechText);

  const { abort: abortVoice } = voice;

  // ===================================================
  // 4.4. GIÁ TRỊ TÍNH TOÁN
  // ===================================================

  const topic =
    topicChoice === 'Chủ đề khác'
      ? customTopic.trim()
      : topicChoice;

  const isOpen =
    questionType === 'Câu trả lời mở';

  const questions =
    quiz?.questions ?? open?.questions ?? [];

  const total = questions.length;

  const current = questions[currentIndex];

  const reviewing =
    currentIndex < completedCount;

  const isMulti =
    quiz?.question_type ===
    'Trắc nghiệm nhiều đáp án';

  // ===================================================
  // 5. TẠO NỘI DUNG ĐỌC CÂU HỎI
  // ===================================================

  const readingText = useMemo(() => {
    if (!current || stage !== 'doing') {
      return '';
    }

    if (quiz) {
      return [
        `Câu ${currentIndex + 1}. ${
          quiz.questions[currentIndex].content
        }`,

        ...quiz.questions[currentIndex].options.map(
          (option) =>
            `Đáp án ${option.option_id}. ${option.text}.`
        ),

        isMulti
          ? 'Con hãy chọn tất cả đáp án đúng nhé!'
          : 'Con hãy chọn một đáp án đúng nhé!',
      ].join(' ');
    }

    return (
      `Câu ${currentIndex + 1}. ${current.content}. ` +
      'Con hãy nói hoặc viết câu trả lời nhé!'
    );
  }, [
    current,
    currentIndex,
    quiz,
    isMulti,
    stage,
  ]);

  // Tự động đọc khi chuyển câu.
  useEffect(() => {
    if (
      stage !== 'doing' ||
      !autoRead ||
      !readingText
    ) {
      stopReading();
      return;
    }

    speak(readingText);

    return () => stopReading();
  }, [stage, autoRead, readingText]);

  // ===================================================
  // 6. SINH BÀI TẬP
  // ===================================================

  const generate = async () => {
    // Kiểm tra chủ đề.
    if (!topic || topic.length > 100) {
      setError(
        'Chủ đề phải có từ 1 đến 100 ký tự.'
      );

      return;
    }

    // Kiểm tra số câu.
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

    stopReading();
    abortVoice();

    try {
      const common = {
        child_id: child.child_id,
        subject,
        topic,
        level,
        question_count: questionCount,
      };

      // Câu hỏi mở.
      if (isOpen) {
        const res =
          await exerciseService.generateOpen({
            ...common,
            question_type: 'Câu trả lời mở',
          });

        if (
          !res.success ||
          !res.data?.questions?.length
        ) {
          throw new Error(
            res.message ||
            'Không nhận được câu hỏi.'
          );
        }

        setOpen(res.data);
        setQuiz(null);
      } else {
        // Trắc nghiệm.
        const res =
          await exerciseService.generateQuiz({
            ...common,
            question_type:
              questionType as QuizType,
          });

        if (
          !res.success ||
          !res.data?.questions?.length
        ) {
          throw new Error(
            res.message ||
            'Không nhận được câu hỏi.'
          );
        }

        setQuiz(res.data);
        setOpen(null);
      }

      // Reset bài tập trước.
      setCurrentIndex(0);
      setCompletedCount(0);
      setSelected({});
      setWritten({});
      setFinishedSpeechQuestionId(null);

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

  // ===================================================
  // 7. CHỌN ĐÁP ÁN
  // ===================================================

  const selectAnswer = (
    questionId: string,
    optionId: string
  ) => {
    if (reviewing || busy) {
      return;
    }

    setSelected((prev) => {
      const old = prev[questionId] ?? [];

      const next = isMulti
        ? old.includes(optionId)
          ? old.filter((id) => id !== optionId)
          : [...old, optionId]
        : [optionId];

      return {
        ...prev,
        [questionId]: next,
      };
    });
  };

  // ===================================================
  // 8. CHUYỂN CÂU HỎI
  // ===================================================

  const goToQuestion = (index: number) => {
    if (
      busy ||
      index < 0 ||
      index >= total ||
      index > completedCount
    ) {
      return;
    }

    abortVoice();
    stopReading();

    setError('');
    setCurrentIndex(index);
  };

  // ===================================================
  // 9. NỘP MỘT CÂU HỎI
  // ===================================================

  const submitCurrent = async () => {
    if (
      !current ||
      busy ||
      reviewing ||
      voice.listening ||
      voice.stopping
    ) {
      return;
    }

    setError('');

    // -----------------------------------------------
    // 9.1. TRẮC NGHIỆM
    // -----------------------------------------------

    if (quiz) {
      const answer =
        selected[current.question_id] ?? [];

      if (!answer.length) {
        setError(
          'Con hãy chọn ít nhất một đáp án nhé!'
        );

        return;
      }

      const done = completedCount + 1;

      setCompletedCount(done);

      if (done === total) {
        const result = gradeQuiz(
          quiz.questions,
          selected
        );

        setQuizResult(result);
        setStage('result');
      } else {
        setCurrentIndex(done);
      }

      return;
    }

    // -----------------------------------------------
    // 9.2. CÂU TRẢ LỜI MỞ
    // -----------------------------------------------

    if (!open) {
      return;
    }

    const q = open.questions[currentIndex];

    const answer = (
      written[q.question_id] ?? ''
    ).trim();

    if (!answer) {
      setError(
        'Con hãy viết hoặc nói câu trả lời nhé!'
      );

      return;
    }

    setBusy(true);

    setStatus(
      `AI đang chấm câu ${
        currentIndex + 1
      }/${total}...`
    );

    try {
      const res =
        await exerciseService.evaluateOpen({
          child_id: child.child_id,
          question_id: q.question_id,
          question: q.content,
          answer,
          evaluation_criteria:
            q.evaluation_criteria,
          subject,
          topic,
          level,
        });

      if (!res.success || !res.data) {
        throw new Error(
          res.message ||
          'Không thể chấm câu trả lời.'
        );
      }

      setOpenResults((prev) => ({
        ...prev,
        [q.question_id]: res.data!,
      }));

      const done = completedCount + 1;

      setCompletedCount(done);

      if (done === total) {
        setStage('result');
      } else {
        setCurrentIndex(done);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Không thể chấm bài. Hãy thử lại nhé!'
      );
    } finally {
      setBusy(false);
      setStatus('');
    }
  };

  // ===================================================
  // 10. TÍNH ĐIỂM VÀ LỜI KHEN
  // ===================================================

  const openScore = useMemo(() => {
    if (!open?.questions.length) {
      return 0;
    }

    const sum = open.questions.reduce(
      (acc, q) =>
        acc +
        (openResults[q.question_id]?.score ?? 0),
      0
    );

    return Math.round(
      (sum / open.questions.length) * 10
    ) / 10;
  }, [open, openResults]);

  const finalScore = quiz
    ? (quizResult?.score ?? 0)
    : openScore;

  const praise = getPraise(finalScore);

  const praiseSpeech =
    `Chúc mừng ${child.name}! ` +
    `Con được ${finalScore} trên 10 điểm. ` +
    `${praise.title} ${praise.detail}`;

  // Đọc nhận xét khi hoàn thành.
  useEffect(() => {
    if (stage !== 'result') {
      return;
    }

    speak(praiseSpeech);

    return () => stopReading();
  }, [stage, praiseSpeech]);

  useEffect(() => {
    return () => stopReading();
  }, []);

  // ===================================================
  // 11. ĐIỀU HƯỚNG
  // ===================================================

  const goToConfig = () => {
    abortVoice();
    stopReading();

    setError('');
    setStage('config');
  };

  const goHome = () => {
    abortVoice();
    stopReading();

    onGoHome();
  };

  // ===================================================
  // 12. ĐIỀU PHỐI 3 MÀN HÌNH
  // ===================================================

  return (
    <main
      className="exercise-page"
      style={{
        maxWidth: 850,
        margin: '24px auto',
        padding: '0 16px 40px',
      }}
    >
      <h1 style={{ marginBottom: 20 }}>
        Học cùng {child.name} 🌟
      </h1>

      {/* THÔNG BÁO LỖI */}

      {error && (
        <div
          role="alert"
          style={{
            padding: 24,
            background: '#fff5f5',
            borderRadius: 20,
            color: '#c92a2a',
            marginBottom: 20,
          }}
        >
          {error}
        </div>
      )}

      {/* =========================================
          MÀN HÌNH CẤU HÌNH
      ========================================= */}

      {stage === 'config' && (
        <ExerciseSetup
          subject={subject}
          topicChoice={topicChoice}
          customTopic={customTopic}
          level={level}
          questionType={questionType}
          questionCount={questionCount}
          busy={busy}
          status={status}
          onGoHome={goHome}

          onSubjectChange={(next) => {
            setSubject(next);

            // Đổi môn -> chọn chủ đề đầu tiên.
            setTopicChoice(
              SUBJECT_TOPICS[next][0]
            );

            setCustomTopic('');
            setError('');
          }}

          onTopicChange={(next) => {
            setTopicChoice(next);
            setError('');
          }}

          onCustomTopicChange={
            setCustomTopic
          }

          onLevelChange={setLevel}

          onQuestionTypeChange={
            setQuestionType
          }

          onQuestionCountChange={
            setQuestionCount
          }

          onStart={generate}
        />
      )}

      {/* =========================================
          MÀN HÌNH LÀM BÀI
      ========================================= */}

      {stage === 'doing' && current && (
        <ExerciseDoing
          current={current}
          currentIndex={currentIndex}
          total={total}
          completedCount={completedCount}
          reviewing={reviewing}
          isMulti={isMulti}
          quiz={quiz}
          open={open}
          selected={selected}
          written={written}
          voice={voice}
          busy={busy}
          status={status}
          autoRead={autoRead}

          finishedSpeechQuestionId={
            finishedSpeechQuestionId
          }

          onToggleAutoRead={() =>
            setAutoRead((prev) => !prev)
          }

          onReadAgain={() =>
            speak(readingText)
          }

          onStopReading={stopReading}

          onSelectAnswer={selectAnswer}

          onWrittenChange={(id, value) =>
            setWritten((prev) => ({
              ...prev,
              [id]: value,
            }))
          }

          onFinishedSpeechChange={
            setFinishedSpeechQuestionId
          }

          onGoToQuestion={goToQuestion}
          onSubmitCurrent={submitCurrent}
        />
      )}

      {/* =========================================
          MÀN HÌNH KẾT QUẢ
      ========================================= */}

      {stage === 'result' && (
        <ExerciseResult
          childName={child.name}
          finalScore={finalScore}
          total={total}
          praise={praise}
          quiz={quiz}
          open={open}
          quizResult={quizResult}
          openResults={openResults}
          written={written}

          onReadPraise={() =>
            speak(praiseSpeech)
          }

          onNewExercise={goToConfig}
          onGoHome={goHome}
        />
      )}
    </main>
  );
}
