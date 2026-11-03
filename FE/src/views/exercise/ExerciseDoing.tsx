
/**
 * FILE: ExerciseDoing.tsx
 *
 * MỤC ĐÍCH:
 * - Hiển thị một câu hỏi tại một thời điểm.
 * - Hiển thị lựa chọn trắc nghiệm.
 * - Hiển thị ô trả lời mở và giao diện micro.
 * - Hiển thị tiến độ và nút chuyển câu.
 *
 * Không tự gọi API hoặc chấm bài.
 */

import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  LoaderCircle,
  Mic,
  RotateCcw,
  Square,
  Volume2,
  VolumeX,
} from 'lucide-react';

import type { CSSProperties } from 'react';

import type {
  OpenGenerateData,
  OpenQuestion,
  QuizGenerateData,
  QuizQuestion,
} from '../../types/exercise';

import type { useVoiceInput } from '../../hooks/useVoiceInput';

type Voice = ReturnType<typeof useVoiceInput>;

// Giữ lại style của màn hình làm bài cũ.
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

interface Props {
  current: QuizQuestion | OpenQuestion;
  currentIndex: number;
  total: number;
  completedCount: number;
  reviewing: boolean;
  isMulti: boolean;

  quiz: QuizGenerateData | null;
  open: OpenGenerateData | null;

  selected: Record<string, string[]>;
  written: Record<string, string>;

  voice: Voice;

  busy: boolean;
  status: string;
  autoRead: boolean;

  finishedSpeechQuestionId: string | null;

  onToggleAutoRead: () => void;
  onReadAgain: () => void;
  onStopReading: () => void;

  onSelectAnswer: (
    questionId: string,
    optionId: string
  ) => void;

  onWrittenChange: (
    questionId: string,
    text: string
  ) => void;

  onFinishedSpeechChange: (
    questionId: string | null
  ) => void;

  onGoToQuestion: (index: number) => void;
  onSubmitCurrent: () => void;
}

export function ExerciseDoing({
  current,
  currentIndex,
  total,
  completedCount,
  reviewing,
  isMulti,
  quiz,
  open,
  selected,
  written,
  voice,
  busy,
  status,
  autoRead,
  finishedSpeechQuestionId,
  onToggleAutoRead,
  onReadAgain,
  onStopReading,
  onSelectAnswer,
  onWrittenChange,
  onFinishedSpeechChange,
  onGoToQuestion,
  onSubmitCurrent,
}: Props) {
  const currentAnswer =
    written[current.question_id] ?? '';

  const speechFinished =
    finishedSpeechQuestionId === current.question_id;

  return (
    <>
      {/* =========================================
          THANH TIẾN ĐỘ
      ========================================= */}

      <section
        style={panel}
        className="lesson-progress"
      >
        <div className="lesson-progress-label">
          <h2>
            Câu {currentIndex + 1}/{total}
          </h2>

          <strong>
            Đã nộp {completedCount}/{total}
          </strong>
        </div>

        <div
          className="lesson-track"
          role="progressbar"
          aria-valuenow={completedCount}
          aria-valuemin={0}
          aria-valuemax={total}
        >
          <div
            style={{
              width: `${
                total
                  ? (completedCount / total) * 100
                  : 0
              }%`,
            }}
          />
        </div>

        <p>
          {quiz?.question_type ?? open?.question_type}
        </p>
      </section>

      {/* =========================================
          CÂU HỎI HIỆN TẠI
      ========================================= */}

      <section
        key={current.question_id}
        style={panel}
        className="lesson-question"
      >
        {/* THANH CÔNG CỤ */}

        <div className="lesson-toolbar">
          <span>
            🧩 Câu hỏi {currentIndex + 1}
          </span>

          <div className="lesson-buttons">
            <button
              type="button"
              className="btn btn-outline"
              disabled={
                voice.listening ||
                voice.stopping
              }
              onClick={onToggleAutoRead}
            >
              {autoRead
                ? <Volume2 size={18} />
                : <VolumeX size={18} />
              }

              {autoRead
                ? 'Tự đọc: Bật'
                : 'Tự đọc: Tắt'}
            </button>

            <button
              type="button"
              className="btn btn-secondary"
              disabled={
                voice.listening ||
                voice.stopping
              }
              onClick={onReadAgain}
            >
              <Volume2 size={18} />
              Nghe lại
            </button>
          </div>
        </div>

        <h2 className="lesson-title">
          {current.content}
        </h2>

        {reviewing && (
          <p className="lesson-reviewed">
            ✅ Câu này đã nộp. Con đang xem lại câu trả lời.
          </p>
        )}

        {/* =====================================
            TRẮC NGHIỆM
        ===================================== */}

        {quiz && (
          <>
            <p>
              {isMulti
                ? '✨ Chọn tất cả đáp án đúng.'
                : '✨ Chọn một đáp án đúng.'}
            </p>

            <div className="lesson-options">
              {quiz.questions[currentIndex].options.map(
                (option) => {
                  const checked = (
                    selected[current.question_id] ?? []
                  ).includes(option.option_id);

                  return (
                    <label
                      key={option.option_id}
                      className={
                        `lesson-option ${
                          checked
                            ? 'lesson-selected'
                            : ''
                        }`
                      }
                    >
                      <input
                        type={
                          isMulti
                            ? 'checkbox'
                            : 'radio'
                        }
                        name={current.question_id}
                        checked={checked}
                        disabled={reviewing || busy}
                        onChange={() =>
                          onSelectAnswer(
                            current.question_id,
                            option.option_id
                          )
                        }
                      />

                      <b>{option.option_id}</b>
                      <span>{option.text}</span>
                    </label>
                  );
                }
              )}
            </div>
          </>
        )}

        {/* =====================================
            CÂU TRẢ LỜI MỞ
        ===================================== */}

        {open && (
          <>
            <p>
              💡 {
                open.questions[currentIndex].answer_hint
              }
            </p>

            <label
              htmlFor="child-answer"
              style={label}
            >
              Câu trả lời của con
            </label>

            <textarea
              id="child-answer"
              style={field}
              rows={5}
              maxLength={1000}
              placeholder="Con có thể viết hoặc bấm micro để nói..."
              value={currentAnswer}
              readOnly={
                reviewing ||
                voice.listening ||
                voice.stopping
              }
              onChange={(e) =>
                onWrittenChange(
                  current.question_id,
                  e.target.value
                )
              }
            />

            {/* =================================
                GIAO DIỆN MICRO
            ================================= */}

            {!reviewing && (
              <div
                className={
                  `lesson-mic ${
                    voice.stopping
                      ? 'lesson-mic--processing'
                      : voice.listening
                        ? 'lesson-mic--listening'
                        : speechFinished &&
                            currentAnswer.trim()
                          ? 'lesson-mic--finished'
                          : 'lesson-mic--idle'
                  }`
                }
              >
                <div className="lesson-voice-heading">
                  <Mic
                    size={21}
                    aria-hidden="true"
                  />

                  <strong>
                    Trả lời bằng giọng nói
                  </strong>
                </div>

                {/* BIỂU TƯỢNG TRẠNG THÁI */}

                <div
                  className="lesson-voice-status"
                  role="status"
                  aria-live="polite"
                >
                  <div
                    className="lesson-voice-icon"
                    aria-hidden="true"
                  >
                    {voice.stopping ? (
                      <LoaderCircle
                        size={46}
                        className="lesson-voice-spinner"
                      />
                    ) : voice.listening ? (
                      <>
                        <span className="lesson-voice-pulse" />
                        <Mic size={46} />
                      </>
                    ) : speechFinished &&
                        currentAnswer.trim() ? (
                      <CheckCircle2 size={46} />
                    ) : (
                      <Mic size={46} />
                    )}
                  </div>

                  {/* TIÊU ĐỀ TRẠNG THÁI */}

                  <h3>
                    {!voice.supported
                      ? 'Micro chưa được hỗ trợ'
                      : voice.stopping
                        ? 'Đang hoàn tất câu trả lời...'
                        : voice.listening
                          ? 'Đang nghe con nói...'
                          : speechFinished &&
                              currentAnswer.trim()
                            ? 'Con đã nói xong! 🎉'
                            : speechFinished
                              ? 'Chưa nghe rõ lời con'
                              : 'Con đã sẵn sàng chưa?'}
                  </h3>

                  {/* HƯỚNG DẪN */}

                  <p>
                    {!voice.supported
                      ? 'Con có thể viết câu trả lời ở ô phía trên.'
                      : voice.stopping
                        ? 'Chờ một chút để ghi nhận lời con vừa nói nhé!'
                        : voice.listening
                          ? 'Micro đang bật. Con cứ nói tự nhiên nhé!'
                          : speechFinished &&
                              currentAnswer.trim()
                            ? 'Con có thể nói tiếp hoặc nói lại từ đầu.'
                            : 'Nhấn nút xanh rồi nói câu trả lời của con nhé!'}
                  </p>

                  {/* SÓNG ÂM MINH HỌA */}

                  {voice.listening &&
                    !voice.stopping && (
                      <div
                        className="lesson-voice-wave"
                        aria-hidden="true"
                      >
                        {Array.from(
                          { length: 11 },
                          (_, i) => (
                            <span
                              key={i}
                              style={{
                                animationDelay:
                                  `${i * 0.12}s`,
                              }}
                            />
                          )
                        )}
                      </div>
                    )}
                </div>

                {/* LỜI ĐANG NHẬN DIỆN */}

                {voice.listening &&
                  !voice.stopping &&
                  voice.interim && (
                    <p className="lesson-voice-interim">
                      <strong>Con đang nói:</strong>
                      {' '}
                      {voice.interim}
                    </p>
                  )}

                {/* CÁC NÚT MICRO */}

                <div className="lesson-voice-actions">
                  {voice.listening ||
                  voice.stopping ? (
                    <button
                      type="button"
                      className="btn lesson-voice-action lesson-voice-stop"
                      disabled={voice.stopping}
                      onClick={() => {
                        onFinishedSpeechChange(
                          current.question_id
                        );

                        // Dừng nhưng giữ kết quả cuối.
                        voice.finish();
                      }}
                    >
                      {voice.stopping ? (
                        <LoaderCircle
                          size={24}
                          className="lesson-voice-spinner"
                        />
                      ) : (
                        <Square
                          size={24}
                          fill="currentColor"
                        />
                      )}

                      {voice.stopping
                        ? 'Đang hoàn tất...'
                        : 'Con nói xong rồi'}
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="btn lesson-voice-action lesson-voice-start"
                      disabled={
                        !voice.supported || busy
                      }
                      onClick={() => {
                        onStopReading();

                        onFinishedSpeechChange(null);

                        // Giữ nội dung để nói tiếp.
                        voice.start(
                          current.question_id,
                          currentAnswer
                        );
                      }}
                    >
                      <Mic size={26} />

                      {currentAnswer.trim()
                        ? 'Nói tiếp'
                        : 'Bắt đầu nói'}
                    </button>
                  )}

                  {/* NÓI LẠI TỪ ĐẦU */}

                  {(voice.listening ||
                    Boolean(currentAnswer.trim()) ||
                    speechFinished) && (
                    <button
                      type="button"
                      className="btn lesson-voice-action lesson-voice-restart"
                      disabled={
                        !voice.supported ||
                        busy ||
                        voice.stopping
                      }
                      onClick={() => {
                        onStopReading();

                        onFinishedSpeechChange(null);

                        // reset = true: xóa chữ cũ.
                        voice.start(
                          current.question_id,
                          '',
                          true
                        );
                      }}
                    >
                      <RotateCcw size={22} />
                      Nói lại từ đầu
                    </button>
                  )}
                </div>

                {voice.error && (
                  <p
                    role="alert"
                    className="lesson-error"
                  >
                    {voice.error}
                  </p>
                )}
              </div>
            )}
          </>
        )}
      </section>

      {/* =========================================
          ĐIỀU HƯỚNG CÂU HỎI
      ========================================= */}

      <div className="lesson-navigation">
        <button
          type="button"
          className="btn btn-outline"
          disabled={
            busy ||
            currentIndex === 0 ||
            voice.listening ||
            voice.stopping
          }
          onClick={() =>
            onGoToQuestion(currentIndex - 1)
          }
        >
          <ArrowLeft size={18} />
          Câu trước
        </button>

        {reviewing ? (
          <button
            type="button"
            className="btn btn-primary"
            onClick={() =>
              onGoToQuestion(currentIndex + 1)
            }
          >
            Câu tiếp
            <ArrowRight size={18} />
          </button>
        ) : (
          <button
            type="button"
            className="btn btn-primary"
            disabled={
              busy ||
              voice.listening ||
              voice.stopping
            }
            onClick={onSubmitCurrent}
          >
            {busy
              ? status
              : currentIndex === total - 1
                ? 'Nộp và xem kết quả'
                : 'Nộp câu này'}

            <ArrowRight size={18} />
          </button>
        )}
      </div>
    </>
  );
}
