
/**
 * LEARNMATE AI — DETECTIVE GAME V3
 *
 * Gameplay:
 * - Một ảnh hiện trường do Cloudflare tạo.
 * - Gợi ý 1–3 lần.
 * - Khoanh vùng bằng tọa độ Gemini Vision.
 * - Bàn tay chỉ vùng quan sát.
 * - Đọc gợi ý bằng Web Speech.
 * - Không có tab thử nghiệm.
 * - Kết luận trắc nghiệm hoặc tự viết.
 * - Tối đa 2 lượt kết luận.
 *
 * Không ảnh hưởng gameplay V2.
 */

import {
  useEffect,
  useRef,
  useState,
} from 'react';

import type {
  CSSProperties,
} from 'react';

import {
  CheckCircle2,
  CircleAlert,
  Pointer,
  Lightbulb,
  LoaderCircle,
  Maximize2,
  Minimize2,
  Pause,
  Volume2,
} from 'lucide-react';

import type {
  DetectiveCaseV3,
  DetectiveHintV3,
  DetectiveSolveV3,
} from '../../types/detectiveV3';

import {
  detectiveServiceV3,
} from '../../services/detectiveServiceV3';

import {
  useDetectiveHintSpeech,
} from '../../hooks/useDetectiveHintSpeech';

import './DetectiveGameV3.css';

import {
  DetectiveAudioPlayer,
} from './DetectiveAudioPlayer';

import type {
  DetectiveNarrationVoice,
} from './DetectiveAudioPlayer';

import {
  unlockCelebrationAudio,
  playCelebrationSound,
} from './detectiveCelebrationAudio';

// ============================================================
// 1. TYPES
// ============================================================

type AnswerMode = 'choice' | 'open';

interface Props {
  childId: number;

  caseData: DetectiveCaseV3;

  onCaseChange: (
    next: DetectiveCaseV3
  ) => void;

  onSolved: (
    result: DetectiveSolveV3
  ) => void;

  onBusyChange: (
    busy: boolean
  ) => void;

  narrationVoice: DetectiveNarrationVoice;
  onSwitchToBrowser: () => void;
}

// ============================================================
// 2. HINT OVERLAY
// ============================================================

/**
 * Khoanh vùng dựa trên tọa độ Gemini Vision.
 *
 * Tọa độ là phần trăm của ảnh thực.
 * Không phải tọa độ của toàn màn hình.
 *
 * Không sử dụng icon/sprite vật thể V2.
 */
function HintOverlay({
  hint,
}: {
  hint: DetectiveHintV3 | null;
}) {

  if (!hint) {
    return null;
  }

  const {
    x,
    y,
    width,
    height,
    shape,
  } = hint.region;

  // Vùng khoanh.
  const regionStyle: CSSProperties = {
    left: `${x}%`,
    top: `${y}%`,
    width: `${width}%`,
    height: `${height}%`,

    borderRadius:
      shape === 'circle'
        ? '50%'
        : '16px',
  };

  // Đặt bàn tay gần vùng cần quan sát.
  const pointerStyle: CSSProperties = {
    left: `${
      Math.max(
        6,
        Math.min(94, x + width * 0.9)
      )
    }%`,

    top: `${
      Math.max(
        6,
        Math.min(94, y + height * 0.9)
      )
    }%`,
  };

  return (
    <div
      className="lm3-v3-overlay"
      aria-hidden="true"
    >

      <div
        className="lm3-v3-highlight"
        style={regionStyle}
      />

      <span
        className="lm3-v3-pointer"
        style={pointerStyle}
      >
        <Pointer size={30} />
      </span>

    </div>
  );
}

// ============================================================
// 3. MAIN GAME COMPONENT
// ============================================================

export function DetectiveGameV3({
  childId,
  caseData,
  onCaseChange,
  onSolved,
  onBusyChange,
  narrationVoice,
  onSwitchToBrowser,
}: Props) {

  // ----------------------------------------------------------
  // 3.1. HINT STATE
  // ----------------------------------------------------------

  const [hints, setHints] =
    useState<DetectiveHintV3[]>(
      caseData.revealed_hints
    );

  const [used, setUsed] =
    useState(caseData.hints_used);

  const [
    selectedHintId,
    setSelectedHintId,
  ] = useState<string | null>(
    caseData.revealed_hints.at(-1)?.id ?? null
  );

  const [hintBusy, setHintBusy] =
    useState(false);

  // ----------------------------------------------------------
  // 3.2. ANSWER STATE
  // ----------------------------------------------------------

  const [mode, setMode] =
    useState<AnswerMode>('choice');

  const [hypothesisId, setHypothesisId] =
    useState('');

  const [answerText, setAnswerText] =
    useState('');

  const [solveBusy, setSolveBusy] =
    useState(false);

  // Khôi phục phản hồi khi tiếp tục vụ án dở.
  const [feedback, setFeedback] =
    useState<string>(() => {
      if (
        caseData.completed ||
        caseData.attempts_used === 0
      ) {
        return '';
      }

      return (
        caseData.last_submission_result?.feedback ?? ''
      );
    });

  // Tự động đọc khi nhận phản hồi sai lượt đầu.
  // Không tự đọc lại chỉ vì vừa restore vụ án.
  const [announceRetry, setAnnounceRetry] =
    useState(false);

  // Tăng giá trị để yêu cầu dừng Gemini TTS.
  const [geminiStopSignal, setGeminiStopSignal] =
    useState(0);

  const [error, setError] =
    useState('');

  // ----------------------------------------------------------
  // 3.3. IMAGE STATE
  // ----------------------------------------------------------

  const [imageRatio, setImageRatio] =
    useState<number | null>(null);

  const [imageError, setImageError] =
    useState(false);

  const [expanded, setExpanded] =
    useState(false);

  // ----------------------------------------------------------
  // 3.4. IDEMPOTENCY
  // ----------------------------------------------------------

  /**
   * UUID của yêu cầu mở hint.
   *
   * Nếu request timeout, gửi lại cùng UUID.
   */
  const hintRequest =
    useRef<string | null>(null);

  /**
   * UUID của kết luận đang gửi.
   *
   * Retry không tăng lượt lần thứ hai.
   */
  const solveRequest = useRef<{
    signature: string;
    id: string;
  } | null>(null);

  /**
   * Khóa chống double-click.
   */
  const lock = useRef(false);

  // ----------------------------------------------------------
  // 3.5. WEB SPEECH
  // ----------------------------------------------------------

  const {
    supported,
    speaking,
    speak,
    stop,
  } = useDetectiveHintSpeech();

  // ----------------------------------------------------------
  // 3.6. DERIVED STATE
  // ----------------------------------------------------------

  const busy =
    hintBusy || solveBusy;

  const completed =
    caseData.completed;

  const activeHint =
    hints.find(
      (hint) => hint.id === selectedHintId
    ) ?? null;

  // ==========================================================
  // 4. EFFECTS
  // ==========================================================

  /**
   * Thông báo trạng thái busy lên DetectivePage.
   */
  useEffect(() => {
    onBusyChange(busy);
  }, [busy, onBusyChange]);

  useEffect(() => {
    return () => {
      onBusyChange(false);
    };
  }, [onBusyChange]);

  /**
   * Khi ảnh thay đổi:
   * - Reset tỷ lệ.
   * - Reset lỗi tải ảnh.
   * - Dừng audio cũ.
   */
  useEffect(() => {
    setImageRatio(null);
    setImageError(false);
    stop();
  }, [caseData.image_url, stop]);

  /**
   * Chế độ xem ảnh toàn màn hình.
   */
  useEffect(() => {

    if (!expanded) {
      return;
    }

    const oldOverflow =
      document.body.style.overflow;

    document.body.style.overflow = 'hidden';

    const onEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setExpanded(false);
      }
    };

    window.addEventListener(
      'keydown',
      onEscape
    );

    return () => {
      document.body.style.overflow = oldOverflow;

      window.removeEventListener(
        'keydown',
        onEscape
      );
    };

  }, [expanded]);

  // ==========================================================
  // 5. SELECT OLD HINT
  // ==========================================================

  /**
   * Xem lại gợi ý đã mở.
   *
   * Không gọi API.
   * Không trừ lượt gợi ý.
   */
  function chooseHint(
    hint: DetectiveHintV3
  ) {
    setSelectedHintId(hint.id);

    setError('');

    // Nếu Gemini đang đọc giới thiệu hoặc nhận xét,
    // yêu cầu dừng trước khi đọc gợi ý.
    setGeminiStopSignal(
      (value) => value + 1
    );

    // Gợi ý vẫn dùng Web Speech API.
    // Không gọi Gemini TTS cho nội dung này.
    speak(hint.content);
  }

  // ==========================================================
  // 6. USE NEW HINT
  // ==========================================================

  async function useHint() {

    if (
      lock.current ||
      completed ||
      used >= caseData.hint_count
    ) {
      return;
    }

    lock.current = true;
    setHintBusy(true);
    setError('');

    /**
     * Giữ nguyên UUID nếu request trước bị timeout.
     */
    const requestId =
      hintRequest.current ??
      crypto.randomUUID();

    hintRequest.current = requestId;

    try {

      const response =
        await detectiveServiceV3.useHint(
          caseData.case_id,
          childId,
          requestId
        );

      if (
        !response.success ||
        !response.data
      ) {
        setError(
          response.message ||
          'Chưa mở được gợi ý. Con thử lại nhé!'
        );

        return;
      }

      const data = response.data;

      /**
       * Gộp hint mới với các hint cũ.
       *
       * Không cho ID trùng.
       */
      const nextHints = [
        ...hints.filter(
          (hint) => hint.id !== data.hint.id
        ),
        data.hint,
      ].sort(
        (a, b) => a.order - b.order
      );

      setHints(nextHints);

      setUsed(data.hints_used);

      /**
       * Đồng bộ dữ liệu lên DetectivePage.
       */
      onCaseChange({
        ...caseData,
        revealed_hints: nextHints,
        hints_used: data.hints_used,
      });

      // Yêu cầu đã thành công.
      hintRequest.current = null;

      /**
       * Khoanh vùng và đọc gợi ý.
       */
      chooseHint(data.hint);

    } catch {

      setError(
        'Đường truyền bị gián đoạn. ' +
        'Bấm lại để thử cùng yêu cầu nhé!'
      );

    } finally {

      lock.current = false;
      setHintBusy(false);

    }
  }

  // ==========================================================
  // 7. CHANGE ANSWER MODE
  // ==========================================================

  /**
   * Chuyển giữa:
   * - Trắc nghiệm.
   * - Tự viết kết luận.
   *
   * Không gọi API khi chuyển chế độ.
   */
  function switchMode(
    next: AnswerMode
  ) {
    if (busy) {
      return;
    }

    stop();

    setMode(next);
    setError('');
    setFeedback('');
  }

  // ==========================================================
  // 8. SUBMIT CONCLUSION
  // ==========================================================

  async function submit() {

    if (
      lock.current ||
      completed
    ) {
      return;
    }

    const answer =
      mode === 'choice'
        ? hypothesisId
        : answerText.trim();

    if (!answer) {
      setError(
        'Con hãy chọn hoặc viết kết luận của mình nhé!'
      );

      return;
    }

    if (
      mode === 'open' &&
      answer.length > 1000
    ) {
      setError(
        'Kết luận cần ngắn hơn 1000 ký tự.'
      );

      return;
    }

    const signature = `${mode}:${answer}`;

    /**
     * Nếu request trước chưa được xác nhận,
     * không cho gửi một câu trả lời khác.
     *
     * Vì request trước có thể đã được BE ghi nhận,
     * gửi câu mới có thể tiêu thêm lượt.
     */
    if (
      solveRequest.current !== null &&
      solveRequest.current.signature !== signature
    ) {
      setError(
        'Kết luận trước chưa được xác nhận. ' +
        'Con hãy gửi lại đúng kết luận trước, ' +
        'hoặc tải lại vụ án để cập nhật tiến trình.'
      );

      return;
    }

    /**
     * Retry cùng nội dung luôn sử dụng
     * submission_id của request trước.
     */
    const submissionId =
      solveRequest.current?.id ??
      crypto.randomUUID();

    solveRequest.current = {
      signature,
      id: submissionId,
    };

    lock.current = true;

    setSolveBusy(true);
    setError('');
    setFeedback('');

    // Dừng Web Speech đang đọc gợi ý.
    stop();

    // Gọi ngay trong luồng sự kiện bấm nộp,
    // giúp trình duyệt cho phép phát tiếng ăn mừng.
    unlockCelebrationAudio();

    // Dừng giọng Gemini đang phát.
    setGeminiStopSignal(
      (value) => value + 1
    );

    try {

      const response =
        mode === 'choice'
          ? await detectiveServiceV3.solveChoice(
              caseData.case_id,
              childId,
              hypothesisId,
              submissionId
            )
          : await detectiveServiceV3.solveOpen(
              caseData.case_id,
              childId,
              answer,
              submissionId
            );

      if (
        !response.success ||
        !response.data
      ) {

        setError(
          response.message ||
          'Chưa kiểm tra được kết luận. Con thử lại nhé!'
        );

        if (
          response.error?.code ===
          'CASE_STATE_CHANGED'
        ) {
          setError(
            'Vụ án vừa thay đổi ở một nơi khác. ' +
            'Con hãy mở lại vụ án để cập nhật.'
          );
        }

        return;
      }

      // Nộp thành công.
      solveRequest.current = null;

      const result = response.data;

      /**
       * Đồng bộ trạng thái sau khi nộp.
       */
      onCaseChange({
        ...caseData,

        attempts_used: result.attempts_used,
        completed: result.completed,
        outcome: result.outcome,

        // Giữ lại phản hồi để khôi phục khi
        // trẻ rời màn hình rồi quay lại.
        last_submission_result: result,

        ...(result.completed
          ? {
              explanation: result.explanation,
            }
          : {}),
      });

      /**
       * Nếu vụ án đã kết thúc:
       * chuyển sang trang kết quả.
       */
      if (result.completed) {
        // Đúng lần 1 hoặc lần 2:
        // có tiếng chiến thắng.
        if (result.outcome === 'solved') {
          void playCelebrationSound();
        }

        // Chuyển sang trang kết quả.
        // Trang kết quả sẽ tự phát Gemini TTS.
        onSolved(result);

      } else {
        // Sai lần 1:
        // ở lại gameplay và hiện nhận xét.
        setFeedback(result.feedback);

        // Bật tự động phát Gemini TTS
        // khi phần nhận xét xuất hiện.
        setAnnounceRetry(true);
      }

    } catch {

      setError(
        'Kết nối chậm. ' +
        'Con bấm lại để gửi đúng kết luận này nhé!'
      );

    } finally {

      lock.current = false;
      setSolveBusy(false);

    }
  }

  // ==========================================================
  // 9. RENDER
  // ==========================================================

  return (
    <section className="lm3-v3-game">

      {/* ====================================================
          9.1. TITLE
      ==================================================== */}

      <div className="lm3-v3-titlebar">

        <div>

          <span className="lm3-v3-eyebrow">
            🔎 THÁM TỬ KHOA HỌC
          </span>

          <h1>
            {caseData.title}
          </h1>

          <p>
            {caseData.introduction}
          </p>

        </div>

        {/* GEMINI TTS — GIỚI THIỆU VỤ ÁN */}

        <DetectiveAudioPlayer
          caseId={caseData.case_id}
          childId={childId}
          segmentType="introduction"
          text={
            `${caseData.title}. ${caseData.introduction}`
          }
          label="Nghe giới thiệu"
          autoPlayOnStart
          stopSignal={geminiStopSignal}
          showCaption={false}
          voiceMode={narrationVoice}
          onSwitchToBrowser={onSwitchToBrowser}
        />

      </div>

      {/* ====================================================
          9.2. MAIN LAYOUT
      ==================================================== */}

      <div className="lm3-v3-columns">

        {/* ==================================================
            LEFT — SCENE
        ================================================== */}

        <div className="lm3-v3-scene-panel">

          <div className="lm3-v3-scene-head">

            <strong>
              📷 Ảnh hiện trường
            </strong>

            <button
              type="button"
              disabled={imageError}
              aria-label="Xem ảnh toàn màn hình"
              onClick={() =>
                setExpanded(
                  (value) => !value
                )
              }
            >
              <Maximize2 size={18} />
            </button>

          </div>

          {/* ẢNH HIỆN TRƯỜNG */}

          <div
            className={
              expanded
                ? 'lm3-v3-fullscreen'
                : 'lm3-v3-picture-area'
            }
          >

            {expanded && (
              <button
                className="lm3-v3-close-full"
                type="button"
                onClick={() =>
                  setExpanded(false)
                }
              >
                <Minimize2 size={20} />
                Thu nhỏ
              </button>
            )}

            {imageError ? (

              /* LỖI TẢI ẢNH */

              <div
                className="lm3-v3-image-error"
                role="alert"
              >

                <CircleAlert size={22} />

                Không tải được ảnh hiện trường.

                <button
                  type="button"
                  onClick={() => {
                    setImageError(false);
                    setImageRatio(null);
                  }}
                >
                  Thử tải lại
                </button>

              </div>

            ) : (

              /* ẢNH THẬT + OVERLAY */

              <div
                className="lm3-v3-photo-wrap"
                style={
                  {
                    aspectRatio:
                      imageRatio ?? 16 / 9,

                    '--v3-ratio':
                      imageRatio ?? 16 / 9,
                  } as CSSProperties
                }
              >

                <img
                  src={caseData.image_url}
                  alt={
                    `Ảnh hiện trường: ${caseData.title}`
                  }
                  onLoad={(event) => {

                    const img =
                      event.currentTarget;

                    if (
                      img.naturalWidth &&
                      img.naturalHeight
                    ) {
                      setImageRatio(
                        img.naturalWidth /
                        img.naturalHeight
                      );
                    }

                  }}
                  onError={() =>
                    setImageError(true)
                  }
                />

                {imageRatio !== null && (
                  <HintOverlay
                    hint={activeHint}
                  />
                )}

              </div>

            )}

          </div>

          <p className="lm3-v3-scene-note">
            Hãy quan sát ảnh thật kỹ.
            Các vùng khoanh chỉ xuất hiện
            khi con mở gợi ý.
          </p>

        </div>

        {/* ==================================================
            RIGHT — HINTS & CONCLUSION
        ================================================== */}

        <div className="lm3-v3-side">

          {/* ================================================
              9.3. HINT PANEL
          ================================================ */}

          <section className="lm3-v3-panel">

            <div className="lm3-v3-panel-title">

              <Lightbulb size={22} />

              <h2>
                Tìm manh mối
              </h2>

            </div>

            {/* SỐ GỢI Ý */}

            <p className="lm3-v3-count">
              Đã dùng{' '}

              <strong>
                {used}/{caseData.hint_count}
              </strong>

              {' '}gợi ý
            </p>

            {/* NÚT DÙNG GỢI Ý */}

            <button
              type="button"
              className="lm3-v3-primary"
              disabled={
                busy ||
                completed ||
                used >= caseData.hint_count
              }
              onClick={() =>
                void useHint()
              }
            >

              {hintBusy ? (
                <LoaderCircle
                  className="lm3-v3-spin"
                  size={19}
                />
              ) : (
                <Lightbulb size={19} />
              )}

              {hintBusy
                ? 'Đang tìm gợi ý...'
                : used >= caseData.hint_count
                  ? 'Đã dùng hết gợi ý'
                  : 'Dùng gợi ý'}

            </button>

            {/* LỊCH SỬ HINT ĐÃ MỞ */}

            {hints.length > 0 && (

              <div
                className="lm3-v3-hint-history"
                aria-label="Những gợi ý đã mở"
              >

                {hints.map((hint) => (

                  <button
                    type="button"
                    key={hint.id}
                    aria-pressed={
                      selectedHintId === hint.id
                    }
                    className={
                      selectedHintId === hint.id
                        ? 'active'
                        : ''
                    }
                    onClick={() =>
                      chooseHint(hint)
                    }
                  >
                    {hint.order}. {hint.title}
                  </button>

                ))}

              </div>

            )}

            {/* VÙNG VĂN BẢN GỢI Ý CỐ ĐỊNH */}

            <div
              className="lm3-v3-hint-box"
              aria-live="polite"
            >

              <strong>
                👩‍🏫 Cô giáo gợi ý
              </strong>

              {activeHint ? (

                <>

                  <p>
                    {activeHint.content}
                  </p>

                  <div className="lm3-v3-audio-actions">

                    <button
                      type="button"
                      disabled={!supported}
                      onClick={() =>
                        speak(
                          activeHint.content
                        )
                      }
                    >
                      <Volume2 size={17} />
                      Nghe lại
                    </button>

                    <button
                      type="button"
                      disabled={!speaking}
                      onClick={stop}
                    >
                      <Pause size={17} />
                      Dừng đọc
                    </button>

                  </div>

                </>

              ) : (

                <p>
                  Con có thể tự suy luận ngay,
                  hoặc bấm “Dùng gợi ý”
                  để được cô hướng dẫn nhé!
                </p>

              )}

            </div>

            {!supported && (

              <small>
                Thiết bị chưa hỗ trợ đọc thành tiếng.
                Con vẫn xem được đầy đủ lời gợi ý.
              </small>

            )}

          </section>

          {/* ================================================
              9.4. CONCLUSION PANEL
          ================================================ */}

          <section className="lm3-v3-panel">

            <div className="lm3-v3-panel-title">

              <CheckCircle2 size={22} />

              <h2>
                Đưa ra kết luận
              </h2>

            </div>

            {/* SỐ LƯỢT */}

            <p className="lm3-v3-count">

              Lượt{' '}

              <strong>
                {Math.min(
                  caseData.attempts_used + 1,
                  2
                )}/2
              </strong>

              {' '}· Con không bắt buộc
              dùng hết gợi ý.

            </p>

            {/* CHUYỂN CHẾ ĐỘ */}

            <div
              className="lm3-v3-switch"
              role="group"
              aria-label="Cách kết luận"
            >

              <button
                type="button"
                className={
                  mode === 'choice'
                    ? 'active'
                    : ''
                }
                aria-pressed={
                  mode === 'choice'
                }
                disabled={busy}
                onClick={() =>
                  switchMode('choice')
                }
              >
                Chọn đáp án
              </button>

              <button
                type="button"
                className={
                  mode === 'open'
                    ? 'active'
                    : ''
                }
                aria-pressed={
                  mode === 'open'
                }
                disabled={busy}
                onClick={() =>
                  switchMode('open')
                }
              >
                Tự viết kết luận
              </button>

            </div>

            {/* ============================================
                CHẾ ĐỘ CHỌN ĐÁP ÁN
            ============================================ */}

            {mode === 'choice' ? (

              <fieldset
                className="lm3-v3-choices"
                disabled={
                  busy || completed
                }
              >

                <legend>
                  Con nghĩ nguyên nhân
                  của bí ẩn là gì?
                </legend>

                {caseData.hypotheses.map(
                  (hypothesis) => (

                    <label
                      key={hypothesis.id}
                      className={
                        hypothesisId === hypothesis.id
                          ? 'selected'
                          : ''
                      }
                    >

                      <input
                        type="radio"
                        name={
                          `lm3-v3-answer-${caseData.case_id}`
                        }
                        value={hypothesis.id}
                        checked={
                          hypothesisId === hypothesis.id
                        }
                        onChange={() =>
                          setHypothesisId(
                            hypothesis.id
                          )
                        }
                      />

                      <span>
                        {hypothesis.label}
                      </span>

                    </label>

                  )
                )}

              </fieldset>

            ) : (

              /* ==========================================
                  CHẾ ĐỘ TỰ VIẾT
              ========================================== */

              <div className="lm3-v3-open">

                <label htmlFor="lm3-v3-answer">
                  Con hãy viết nguyên nhân
                  và điều con quan sát được nhé:
                </label>

                <textarea
                  id="lm3-v3-answer"
                  value={answerText}
                  maxLength={1000}
                  rows={4}
                  disabled={
                    busy || completed
                  }
                  onChange={(event) =>
                    setAnswerText(
                      event.target.value
                    )
                  }
                  placeholder={
                    'Con nghĩ nguyên nhân là... ' +
                    'vì con quan sát thấy...'
                  }
                />

                <small>
                  {answerText.length}/1000 ký tự
                </small>

              </div>

            )}

            {/* PHẢN HỒI SAI LẦN 1 */}

            {/* PHẢN HỒI SAU KHI NỘP SAI LẦN 1 */}

            {feedback && (
              <>
                <p
                  className="lm3-v3-feedback"
                  role="status"
                >
                  {feedback}
                  {' '}
                  Con còn một lượt để thử lại nhé!
                </p>

                {/* Gemini đọc phản hồi.
                    Không gọi TTS cho hint. */}

                <DetectiveAudioPlayer
                  key={
                    `retry-${caseData.case_id}-${caseData.attempts_used}`
                  }
                  caseId={caseData.case_id}
                  childId={childId}
                  segmentType="retry_feedback"
                  label="Nghe cô nhận xét"
                  text={feedback}
                  autoPlayOnStart={announceRetry}
                  stopSignal={geminiStopSignal}
                  showCaption={false}
                  voiceMode={narrationVoice}
                  onSwitchToBrowser={onSwitchToBrowser}
                />
              </>
            )}

            {/* ERROR */}

            {error && (

              <p
                className="lm3-v3-error"
                role="alert"
              >
                <CircleAlert size={18} />
                {error}
              </p>

            )}

            {/* NÚT NỘP KẾT LUẬN */}

            <button
              type="button"
              className="lm3-v3-submit"
              disabled={
                busy ||
                completed ||
                (
                  mode === 'choice'
                    ? !hypothesisId
                    : !answerText.trim()
                )
              }
              onClick={() =>
                void submit()
              }
            >

              {solveBusy ? (

                <LoaderCircle
                  size={19}
                  className="lm3-v3-spin"
                />

              ) : (

                <CheckCircle2 size={19} />

              )}

              {solveBusy
                ? 'Cô đang kiểm tra...'
                : 'Nộp kết luận'}

            </button>

          </section>

        </div>

      </div>

    </section>
  );
}
