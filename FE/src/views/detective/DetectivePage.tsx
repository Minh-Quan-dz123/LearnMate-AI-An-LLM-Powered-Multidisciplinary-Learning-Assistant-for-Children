
/**
 * FILE: src/views/detective/DetectivePage.tsx
 *
 * LEARNMATE AI — MODULE 3 V3.0
 *
 * Chức năng:
 * 1. Trang chủ Thám tử khoa học.
 * 2. Chọn chủ đề và sinh vụ án mới.
 * 3. Tự động phân biệt gameplay V2 và V3.
 * 4. Lưu case_id để tiếp tục vụ án dở.
 * 5. Khôi phục tiến trình từ Backend.
 * 6. Xem lịch sử 5 vụ án đã kết thúc.
 * 7. Chơi lại không sinh lại ảnh hoặc gọi AI.
 * 8. Hiển thị kết quả solved / unsolved.
 *
 * FE chỉ giao tiếp Backend qua detectiveService.
 * Không lưu lời giải trong localStorage.
 */

import { useEffect, useRef, useState } from 'react';

import type { CSSProperties } from 'react';

import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  ChevronDown,
  ChevronUp,
  CircleAlert,
  FolderOpen,
  Lightbulb,
  LoaderCircle,
  Play,
  RefreshCw,
  RotateCcw,
  Sparkles,
  Trophy,
  X,
} from 'lucide-react';

import type { ChildProfile } from '../../types/child';

import {
  DETECTIVE_TOPICS,
  type DetectiveTopicId,
} from '../../constants/detectiveTopics';

import type {
  DetectiveCaseData,
  DetectiveHistoryItem,
  DetectiveSolveData,
} from '../../types/detective';

import type {
  DetectiveCaseV3,
} from '../../types/detectiveV3';

import { detectiveService } from '../../services/detectiveService';

import { DetectiveGame } from './DetectiveGame';
import { DetectiveGameV3 } from './DetectiveGameV3';


import {
  DetectiveAudioPlayer,
} from './DetectiveAudioPlayer';

import {
  DetectiveCelebration,
} from './DetectiveCelebration';

import {
  unlockCelebrationAudio,
  playCelebrationSound,
} from './detectiveCelebrationAudio';


import './Detective.css';

// ============================================================
// 1. TYPES
// ============================================================

type Screen =
  | 'home'
  | 'topics'
  | 'history'
  | 'game'
  | 'result';

type AnyDetectiveCase =
  | DetectiveCaseData
  | DetectiveCaseV3;

interface Props {
  child: ChildProfile;
  onBackToActivities: () => void;
}

// ============================================================
// 2. HELPER FUNCTIONS
// ============================================================

/**
 * Mỗi hồ sơ bé có một khóa localStorage riêng.
 *
 * Ví dụ:
 * learnmate_detective_draft_101
 */
function storageKey(childId: number): string {
  return `learnmate_detective_draft_${childId}`;
}

/**
 * Đọc case_id đang chơi dở.
 *
 * Chỉ lưu ID, không lưu kịch bản hoặc lời giải.
 * Backend là nơi quản lý trạng thái thật.
 */
function readDraft(childId: number): string | null {
  try {
    if (typeof window === 'undefined') {
      return null;
    }

    return window.localStorage.getItem(
      storageKey(childId)
    );
  } catch {
    return null;
  }
}

/**
 * Phân biệt vụ án V3 và V2.
 *
 * V3:
 *   case_data.schema_version = 3
 *
 * V2:
 *   Không có schema_version hoặc schema_version = 2
 *
 * Type guard giúp TypeScript xác định đúng kiểu dữ liệu.
 * Không bắt buộc phải chỉnh sửa type V2 hiện có.
 */
function isDetectiveV3(
  data: AnyDetectiveCase
): data is DetectiveCaseV3 {
  return (
    'schema_version' in data &&
    data.schema_version === 3
  );
}

// ============================================================
// 3. MAIN COMPONENT
// ============================================================

export function DetectivePage({
  child,
  onBackToActivities,
}: Props) {

  // ----------------------------------------------------------
  // 3.1. STATE — MÀN HÌNH
  // ----------------------------------------------------------

  const [screen, setScreen] =
    useState<Screen>('home');

  // ----------------------------------------------------------
  // 3.2. STATE — CHỦ ĐỀ
  // ----------------------------------------------------------

  const [selectedTopic, setSelectedTopic] =
    useState<DetectiveTopicId>('random');

  const [showAllTopics, setShowAllTopics] =
    useState(false);

  // ----------------------------------------------------------
  // 3.3. STATE — VỤ ÁN
  // ----------------------------------------------------------

  /**
   * Có thể chứa:
   * - DetectiveCaseData (V2)
   * - DetectiveCaseV3 (V3)
   */
  const [activeCase, setActiveCase] =
    useState<AnyDetectiveCase | null>(null);

  const [result, setResult] =
    useState<DetectiveSolveData | null>(null);

  // ----------------------------------------------------------
  // 3.4. STATE — VỤ ÁN ĐANG DỞ
  // ----------------------------------------------------------

  const [draftCaseId, setDraftCaseId] =
    useState<string | null>(
      () => readDraft(child.child_id)
    );

  // ----------------------------------------------------------
  // 3.5. STATE — LỊCH SỬ
  // ----------------------------------------------------------

  const [history, setHistory] =
    useState<DetectiveHistoryItem[]>([]);

  const [historyLoading, setHistoryLoading] =
    useState(false);

  const [historyReload, setHistoryReload] =
    useState(0);

  // ----------------------------------------------------------
  // 3.6. STATE — REQUEST / ERROR
  // ----------------------------------------------------------

  const [pending, setPending] =
    useState(false);

  const [gameBusy, setGameBusy] =
    useState(false);

  const [error, setError] =
    useState('');

  // ----------------------------------------------------------
  // 3.7. STATE — XÁC NHẬN RỜI GAME
  // ----------------------------------------------------------

  const [confirmLeave, setConfirmLeave] =
    useState(false);

  /**
   * Chống bấm liên tiếp khi React chưa cập nhật state.
   */
  const requestLock = useRef(false);

  // ----------------------------------------------------------
  // 3.8. DERIVED VALUES
  // ----------------------------------------------------------

  const topic =
    DETECTIVE_TOPICS.find(
      (item) => item.id === selectedTopic
    )!;

  const visibleTopics = showAllTopics
    ? DETECTIVE_TOPICS
    : DETECTIVE_TOPICS.slice(0, 6);

  // ==========================================================
  // 4. LOCAL STORAGE
  // ==========================================================

  /**
   * Ghi nhớ vụ án đang chơi.
   *
   * Chỉ lưu case_id.
   */
  function rememberDraft(caseId: string) {
    setDraftCaseId(caseId);

    try {
      window.localStorage.setItem(
        storageKey(child.child_id),
        caseId
      );
    } catch {
      // Không làm gián đoạn trò chơi.
    }
  }

  /**
   * Xóa case_id sau khi vụ án kết thúc.
   */
  function forgetDraft() {
    setDraftCaseId(null);

    try {
      window.localStorage.removeItem(
        storageKey(child.child_id)
      );
    } catch {
      // Không làm gián đoạn trò chơi.
    }
  }

  // ==========================================================
  // 5. NAVIGATION
  // ==========================================================

  /**
   * Chuyển màn hình.
   *
   * Không xóa activeCase.
   * Vụ án dở vẫn được lưu trong Supabase.
   */
  function navigate(to: Screen) {
    setError('');
    setConfirmLeave(false);
    setScreen(to);
  }

  // ==========================================================
  // 6. REQUEST LOCK
  // ==========================================================

  /**
   * Khóa các request:
   * - Generate
   * - Replay
   * - Continue
   *
   * Ngăn người dùng bấm nhiều lần.
   */
  function beginRequest(): boolean {
    if (requestLock.current) {
      return false;
    }

    requestLock.current = true;

    setPending(true);
    setError('');

    return true;
  }

  function endRequest() {
    requestLock.current = false;
    setPending(false);
  }

  // ==========================================================
  // 7. LOAD HISTORY
  // ==========================================================

  /**
   * Lấy lịch sử khi:
   * - Mở màn hình history.
   * - Bấm Thử tải lại.
   *
   * Backend trả tối đa 5 vụ án đã kết thúc.
   *
   * Bao gồm:
   * - solved
   * - unsolved
   */
  useEffect(() => {
    if (screen !== 'history') {
      return;
    }

    let active = true;

    setHistoryLoading(true);
    setError('');

    void (async () => {
      try {
        const response =
          await detectiveService.getHistory(
            child.child_id
          );

        if (!active) {
          return;
        }

        if (
          !response.success ||
          !response.data
        ) {
          setError(
            response.message ||
            'Không tải được vụ án cũ.'
          );

          return;
        }

        setHistory(
          response.data.cases.slice(0, 5)
        );
      } catch {
        if (active) {
          setError(
            'Không thể kết nối để lấy vụ án cũ.'
          );
        }
      } finally {
        if (active) {
          setHistoryLoading(false);
        }
      }
    })();

    return () => {
      active = false;
    };
  }, [
    screen,
    child.child_id,
    historyReload,
  ]);

  // ==========================================================
  // 8. BACK BUTTON
  // ==========================================================

  /**
   * Nếu đang chơi vụ án chưa kết thúc:
   *   Hiển thị xác nhận tạm dừng.
   *
   * Nếu đang ở trang chủ:
   *   Quay về danh sách hoạt động.
   */
  function handleBack() {
    if (pending || gameBusy) {
      return;
    }

    if (
      screen === 'game' &&
      activeCase &&
      !activeCase.completed
    ) {
      setConfirmLeave(true);
      return;
    }

    if (screen === 'home') {
      onBackToActivities();
    } else {
      navigate('home');
    }
  }

  // ==========================================================
  // 9. GENERATE NEW CASE
  // ==========================================================

  /**
   * Tạo vụ án mới V3.
   *
   * FE gửi:
   *   child_id
   *   topic_id
   *
   * Backend:
   *   1. Lấy hồ sơ bé.
   *   2. Gemini Text tạo kịch bản.
   *   3. Cloudflare tạo một ảnh.
   *   4. Gemini Vision định vị dấu vết.
   *   5. Lưu Supabase.
   *
   * FE nhận public case.
   *
   * Không nhận solution hoặc hint chưa mở.
   */
  async function generate() {
    if (!beginRequest()) {
      return;
    }

    try {
      const response =
        await detectiveService.generateCase(
          child.child_id,
          selectedTopic
        );

      if (
        !response.success ||
        !response.data
      ) {
        setError(
          response.message ||
          'Không tạo được vụ án. Con hãy thử lại nhé!'
        );

        return;
      }

      // Lưu dữ liệu V2 hoặc V3.
      setActiveCase(response.data);

      // Xóa kết quả cũ.
      setResult(null);

      // Lưu ID để có thể tiếp tục khi refresh.
      rememberDraft(
        response.data.case_id
      );

      // Mở gameplay.
      navigate('game');
    } catch {
      setError(
        'Có lỗi kết nối khi tạo vụ án. ' +
        'Con hãy thử lại nhé!'
      );
    } finally {
      endRequest();
    }
  }

  // ==========================================================
  // 10. CONTINUE DRAFT
  // ==========================================================

  /**
   * Tiếp tục vụ án đang dở.
   *
   * Không gọi Gemini Text.
   * Không gọi Cloudflare.
   * Không gọi Gemini Vision.
   *
   * Chỉ khôi phục state từ Backend.
   */
  async function continueDraft() {
    if (!draftCaseId || !beginRequest()) {
      return;
    }

    try {
      /**
       * Trường hợp activeCase vẫn còn trong React state.
       *
       * Không cần gọi lại BE.
       */
      if (
        activeCase?.case_id === draftCaseId &&
        !activeCase.completed
      ) {
        navigate('game');
        return;
      }

      /**
       * Trường hợp trang vừa refresh:
       * đọc state từ Supabase qua BE.
       */
      const response =
        await detectiveService.getCase(
          draftCaseId,
          child.child_id
        );

      if (
        !response.success ||
        !response.data
      ) {
        if (
          response.error?.code ===
          'CASE_NOT_FOUND'
        ) {
          forgetDraft();
        }

        setError(
          response.message ||
          'Không thể mở lại vụ án dở.'
        );

        return;
      }

      /**
       * Nếu vụ án đã hoàn thành ở phiên khác,
       * không tiếp tục game như vụ đang dở.
       */
      if (response.data.completed) {
        forgetDraft();

        setError(
          'Vụ án này đã hoàn thành. ' +
          'Con có thể chơi lại trong danh sách vụ án cũ.'
        );

        return;
      }

      setActiveCase(response.data);
      setResult(null);

      navigate('game');
    } catch {
      setError(
        'Không thể tải tiến trình. ' +
        'Kiểm tra kết nối rồi thử lại nhé!'
      );
    } finally {
      endRequest();
    }
  }

  // ==========================================================
  // 11. REPLAY
  // ==========================================================

  /**
   * Chơi lại vụ án cũ.
   *
   * Backend:
   * - Reset play_state.
   * - Reset hints đã mở.
   * - Reset attempts_used.
   * - Reset completed/outcome.
   *
   * Giữ nguyên:
   * - case_data.
   * - image_path.
   * - Kịch bản.
   *
   * Không gọi lại AI.
   */
  async function replay(caseId: string) {
    if (!beginRequest()) {
      return;
    }

    try {
      const response =
        await detectiveService.replayCase(
          caseId,
          child.child_id
        );

      if (
        !response.success ||
        !response.data
      ) {
        setError(
          response.message ||
          'Chưa thể chơi lại vụ án.'
        );

        return;
      }

      setActiveCase(response.data);
      setResult(null);

      rememberDraft(
        response.data.case_id
      );

      navigate('game');
    } catch {
      setError(
        'Không thể mở lại vụ án. ' +
        'Con hãy thử lại nhé!'
      );
    } finally {
      endRequest();
    }
  }

  // ==========================================================
  // 12. SOLVED / UNSOLVED
  // ==========================================================

  /**
   * Nhận kết quả từ DetectiveGame V2 hoặc V3.
   *
   * V3:
   * - Đúng lần 1 hoặc 2: solved.
   * - Sai lần 2: unsolved.
   *
   * Cả hai đều được coi là hoàn thành.
   */
  function handleSolved(
    data: DetectiveSolveData
  ) {
    setResult(data);

    setActiveCase((old) =>
      old
        ? {
            ...old,
            completed: true,
            outcome: data.outcome,
            attempts_used: data.attempts_used,
          }
        : old
    );

    // Vụ án đã kết thúc.
    forgetDraft();

    // Hiện kết quả.
    navigate('result');
  }

  // ==========================================================
  // 13. RENDER
  // ==========================================================

  return (
    <main className="lm-detective-page">
      <div className="lm-detective-wrap">

        {/* ==================================================
            13.1. TOOLBAR
        ================================================== */}

        <div className="lm-detective-toolbar">

          <button
            type="button"
            className="lm-detective-back"
            disabled={pending || gameBusy}
            onClick={handleBack}
          >
            <ArrowLeft size={18} />

            {screen === 'home'
              ? 'Chọn hoạt động'
              : 'Quay lại'}
          </button>

          <span className="lm-detective-player">
            🧢 Thám tử {child.name}
          </span>

        </div>

        {/* ==================================================
            13.2. HOME
        ================================================== */}

        {screen === 'home' && (
          <>

            {/* HERO */}

            <section className="lm-detective-hero">

              <div className="lm-detective-hero-text">

                <span className="lm-detective-eyebrow">
                  <Sparkles size={16} />
                  HỒ SƠ THÁM TỬ
                </span>

                <h1>
                  Thám tử khoa học{' '}
                  <span aria-hidden="true">
                    🔍
                  </span>
                </h1>

                <p>
                  Những bí ẩn thú vị đang chờ con!
                  Quan sát thật kỹ, thu thập manh mối
                  và tìm ra lời giải nhé.
                </p>

              </div>

              <div
                className="lm-detective-hero-art"
                aria-hidden="true"
              >
                <span className="lm-detective-hero-main">
                  🕵️
                </span>

                <span className="lm-detective-float lm-detective-float-one">
                  🔎
                </span>

                <span className="lm-detective-float lm-detective-float-two">
                  🧪
                </span>

                <span className="lm-detective-float lm-detective-float-three">
                  ❓
                </span>
              </div>

            </section>

            {/* HAI CHẾ ĐỘ CHÍNH */}

            <section
              className="lm-detective-home-actions"
              aria-label="Chọn chế độ chơi"
            >

              {/* CHƠI MỚI */}

              <button
                className="lm-detective-mode lm-detective-mode-new"
                type="button"
                disabled={pending}
                onClick={() => navigate('topics')}
              >

                <span className="lm-detective-mode-icon">
                  <Play
                    size={31}
                    fill="currentColor"
                  />
                </span>

                <span className="lm-detective-mode-copy">
                  <strong>
                    Chơi mới
                  </strong>

                  <small>
                    Khám phá một vụ án hoàn toàn mới
                  </small>
                </span>

                <ArrowRight
                  size={24}
                  className="lm-detective-mode-arrow"
                />

              </button>

              {/* CHƠI LẠI */}

              <button
                className="lm-detective-mode lm-detective-mode-old"
                type="button"
                disabled={pending}
                onClick={() => navigate('history')}
              >

                <span className="lm-detective-mode-icon">
                  <FolderOpen size={31} />
                </span>

                <span className="lm-detective-mode-copy">
                  <strong>
                    Chơi lại vụ án cũ
                  </strong>

                  <small>
                    Trở lại những bí ẩn con từng giải mã
                  </small>
                </span>

                <ArrowRight
                  size={24}
                  className="lm-detective-mode-arrow"
                />

              </button>

            </section>

            {/* VỤ ÁN ĐANG DỞ */}

            {draftCaseId && (
              <div className="lm4-resume">

                <span>
                  <BookOpen size={19} />
                  Con còn một vụ án đang điều tra dở!
                </span>

                <button
                  type="button"
                  onClick={() => void continueDraft()}
                  disabled={pending}
                >

                  {pending ? (
                    <LoaderCircle
                      size={17}
                      className="lm3-rotate"
                    />
                  ) : (
                    <RotateCcw size={17} />
                  )}

                  Tiếp tục điều tra

                </button>

              </div>
            )}

          </>
        )}

        {/* ==================================================
            13.3. TOPICS
        ================================================== */}

        {screen === 'topics' && (
          <section className="lm-detective-topic-section">

            {/* HEADING */}

            <div className="lm-detective-section-heading">

              <span className="lm-detective-eyebrow">
                <Lightbulb size={16} />
                CHỌN NHIỆM VỤ
              </span>

              <h1>
                Con muốn điều tra bí ẩn nào?
              </h1>

              <p>
                Chọn chủ đề yêu thích,
                hoặc để AI chọn bất ngờ cho con.
              </p>

            </div>

            {/* DANH SÁCH CHỦ ĐỀ */}

            <div className="lm-detective-topic-grid">

              {visibleTopics.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  disabled={pending}
                  className={
                    `lm-detective-topic ${
                      selectedTopic === item.id
                        ? 'is-selected'
                        : ''
                    }`
                  }
                  onClick={() =>
                    setSelectedTopic(item.id)
                  }
                  aria-pressed={
                    selectedTopic === item.id
                  }
                  style={
                    {
                      '--lm-topic-color':
                        item.color,
                    } as CSSProperties
                  }
                >

                  <span
                    className="lm-detective-topic-emoji"
                    aria-hidden="true"
                  >
                    {item.emoji}
                  </span>

                  <strong>
                    {item.name}
                  </strong>

                  <small>
                    {item.description}
                  </small>

                  <span
                    className="lm-detective-topic-check"
                    aria-hidden="true"
                  >
                    ✓
                  </span>

                </button>
              ))}

            </div>

            {/* XEM THÊM / THU GỌN */}

            <button
              type="button"
              className="lm-detective-expand"
              disabled={pending}
              aria-expanded={showAllTopics}
              onClick={() =>
                setShowAllTopics(
                  (value) => !value
                )
              }
            >

              {showAllTopics ? (
                <ChevronUp size={18} />
              ) : (
                <ChevronDown size={18} />
              )}

              {showAllTopics
                ? 'Thu gọn chủ đề'
                : 'Xem thêm chủ đề'}

            </button>

            {/* BẮT ĐẦU ĐIỀU TRA */}

            <div className="lm-detective-start-panel">

              <span className="lm-detective-selection">
                Đã chọn:{' '}

                <strong>
                  {topic.emoji} {topic.name}
                </strong>
              </span>

              <button
                className="lm-detective-start"
                type="button"
                disabled={pending}
                onClick={() => void generate()}
              >

                {pending ? (
                  <LoaderCircle
                    size={20}
                    className="lm3-rotate"
                  />
                ) : (
                  <ArrowRight size={20} />
                )}

                {pending
                  ? 'Đang tạo vụ án...'
                  : 'Bắt đầu điều tra'}

              </button>

            </div>

            {/* LOADING */}

            {pending && (
              <div
                className="lm3-generating"
                role="status"
              >

                <strong>
                  <LoaderCircle
                    size={20}
                    className="lm3-rotate"
                  />

                  Đang chuẩn bị vụ án bí ẩn...
                </strong>

                <p>
                  AI đang tạo kịch bản, một ảnh
                  hiện trường và xác minh các dấu vết.
                </p>

                <div
                  className="lm3-generating-dots"
                  aria-hidden="true"
                >
                  <i />
                  <i />
                  <i />
                </div>

              </div>
            )}

          </section>
        )}

        {/* ==================================================
            13.4. GAMEPLAY V2 / V3
        ================================================== */}

        {screen === 'game' && activeCase && (

          isDetectiveV3(activeCase) ? (

            /*
             * GAMEPLAY V3
             *
             * - Một ảnh hiện trường.
             * - Không có sprite/hotspot V2.
             * - Không có tab thử nghiệm.
             * - 1–3 gợi ý.
             * - Vùng khoanh và bàn tay chỉ.
             * - Web Speech API.
             * - Choice hoặc Open.
             * - Tối đa hai lượt.
             */
            <DetectiveGameV3
              key={activeCase.case_id}
              childId={child.child_id}
              caseData={activeCase}
              onCaseChange={setActiveCase}
              onSolved={handleSolved}
              onBusyChange={setGameBusy}
            />

          ) : (

            /*
             * GAMEPLAY V2 LEGACY
             *
             * Giữ nguyên game cũ để replay
             * những vụ án chưa có schema_version=3.
             */
            <DetectiveGame
              key={activeCase.case_id}
              childId={child.child_id}
              caseData={activeCase}
              onCaseChange={setActiveCase}
              onSolved={handleSolved}
              onBusyChange={setGameBusy}
            />

          )
        )}

        {/* ==================================================
            13.5. HISTORY
        ================================================== */}

        {screen === 'history' && (

          <section className="lm-detective-topic-section">

            <div className="lm-detective-section-heading">

              <span className="lm-detective-eyebrow">
                <FolderOpen size={16} />
                HỒ SƠ ĐÃ HOÀN THÀNH
              </span>

              <h1>
                Những vụ án con đã giải mã
              </h1>

              <p>
                Chọn một vụ án để điều tra lại
                mà không phải tạo mới bằng AI.
              </p>

            </div>

            {/* LOADING LỊCH SỬ */}

            {historyLoading ? (

              <p
                className="lm4-center-status"
                role="status"
              >
                <LoaderCircle
                  className="lm3-rotate"
                  size={21}
                />

                Đang lấy danh sách vụ án...
              </p>

            ) : error ? (

              /* LỖI LẤY LỊCH SỬ */

              <div className="lm4-history-retry">

                <CircleAlert size={24} />

                <p>
                  {error}
                </p>

                <button
                  type="button"
                  onClick={() =>
                    setHistoryReload(
                      (n) => n + 1
                    )
                  }
                >
                  <RefreshCw size={17} />
                  Thử tải lại
                </button>

              </div>

            ) : history.length === 0 ? (

              /* CHƯA CÓ LỊCH SỬ */

              <div className="lm-detective-history-empty">

                <span aria-hidden="true">
                  🗂️
                </span>

                <h2>
                  Chưa có vụ án hoàn thành
                </h2>

                <p>
                  Giải mã vụ án đầu tiên để
                  lưu vào bộ sưu tập nhé!
                </p>

                <button
                  className="lm-detective-start"
                  type="button"
                  onClick={() =>
                    navigate('topics')
                  }
                >
                  Chơi mới
                  <ArrowRight size={18} />
                </button>

              </div>

            ) : (

              /* DANH SÁCH TỐI ĐA 5 VỤ ÁN */

              <div className="lm-detective-history-grid">

                {history.map((item) => {

                  const name =
                    DETECTIVE_TOPICS.find(
                      (t) =>
                        t.id === item.topic_id
                    )?.name ?? 'Khoa học';

                  const isSolved =
                    item.outcome === 'solved';

                  return (
                    <article
                      className="lm-detective-history-card"
                      key={item.case_id}
                    >

                      <span aria-hidden="true">
                        {isSolved ? '🏆' : '📘'}
                      </span>

                      <div>

                        <strong>
                          {item.title}
                        </strong>

                        <small>
                          {name} ·{' '}

                          {new Date(
                            item.last_completed_at
                          ).toLocaleDateString(
                            'vi-VN'
                          )}
                        </small>

                        <small>
                          {isSolved
                            ? 'Đã phá án'
                            : 'Đã xem lời giải'}
                        </small>

                      </div>

                      <button
                        className="lm-detective-history-play"
                        type="button"
                        disabled={pending}
                        onClick={() =>
                          void replay(
                            item.case_id
                          )
                        }
                      >

                        {pending ? (
                          <LoaderCircle
                            size={17}
                            className="lm3-rotate"
                          />
                        ) : (
                          <RotateCcw size={17} />
                        )}

                        Chơi lại

                      </button>

                    </article>
                  );
                })}

              </div>
            )}

            {pending && (
              <p
                className="lm4-center-status"
                role="status"
              >
                Đang mở vụ án cũ...
              </p>
            )}

          </section>
        )}

        {/* ==================================================
            13.6. RESULT
        ================================================== */}

        
        {screen === 'result' &&
          result &&
          activeCase && (

          <section
            className="lm-detective-result"
            style={{
              position: 'relative',
              overflow: 'hidden',
            }}
          >

            {/* Chỉ ăn mừng khi phá án thành công V3. */}

            {isDetectiveV3(activeCase) &&
              result.outcome === 'solved' && (
                <DetectiveCelebration />
              )}


            {/* BIỂU TƯỢNG KẾT QUẢ */}

            <span
              className="lm-detective-result-trophy"
              aria-hidden="true"
            >
              {result.outcome === 'solved'
                ? '🏆'
                : '📘'}
            </span>

            {/* TRẠNG THÁI */}

            <span className="lm-detective-eyebrow">

              {result.outcome === 'solved' ? (
                <Trophy size={16} />
              ) : (
                <BookOpen size={16} />
              )}

              {result.outcome === 'solved'
                ? 'PHÁ ÁN THÀNH CÔNG'
                : 'CÙNG XEM LỜI GIẢI'}

            </span>

            {/* TIÊU ĐỀ */}

            <h1>

              {result.outcome === 'solved'
                ? 'Con đã giải mã vụ án!'
                : 'Mỗi lần quan sát là một bài học mới!'}

            </h1>

            <h2>
              {activeCase.title}
            </h2>

            {/* PHẢN HỒI */}

            <p className="lm-detective-result-feedback">
              {result.feedback}
            </p>

            {/* LỜI GIẢI */}

            <div className="lm-detective-result-explanation">

              <strong>
                🔎 Lời giải khoa học
              </strong>

              <p>
                {result.explanation}
              </p>

            </div>

            {/* BA NÚT ĐIỀU HƯỚNG */}
            
            {/* =========================================
                GEMINI TTS — KẾT LUẬN V3

                Đọc cho cả hai trường hợp:
                - solved
                - unsolved

                Backend lấy phản hồi + lời giải
                đã lưu trong Supabase.
            ========================================= */}

            {isDetectiveV3(activeCase) && (
              <DetectiveAudioPlayer
                key={
                  `final-${activeCase.case_id}`
                }
                caseId={activeCase.case_id}
                childId={child.child_id}
                segmentType="final_explanation"
                text={
                  `${result.feedback} ${result.explanation ?? ''}`
                }
                label="Nghe cô Gemini giải thích"
                showCaption={false}
                autoPlayOnStart
              />
            )}

            {/* =========================================
                NGHE LẠI TIẾNG CHIẾN THẮNG
                Chỉ xuất hiện khi solved.
            ========================================= */}

            {isDetectiveV3(activeCase) &&
              result.outcome === 'solved' && (

              <button
                type="button"
                className="lm3-v3-celebration-replay"
                onClick={() => {
                  unlockCelebrationAudio();

                  void playCelebrationSound();
                }}
              >
                🎵 Nghe lại tiếng chiến thắng
              </button>

            )}


            <div className="lm-detective-result-actions">

              {/* CHƠI LẠI VỤ ÁN NÀY */}

              <button
                type="button"
                disabled={pending}
                onClick={() =>
                  void replay(
                    activeCase.case_id
                  )
                }
              >
                <RotateCcw size={19} />
                Chơi lại vụ án này
              </button>

              {/* CHƠI VÁN MỚI */}

              <button
                type="button"
                disabled={pending}
                onClick={() =>
                  navigate('topics')
                }
              >
                <Play size={19} />
                Chơi ván mới
              </button>

              {/* VỤ ÁN CŨ */}

              <button
                type="button"
                disabled={pending}
                onClick={() =>
                  navigate('history')
                }
              >
                <FolderOpen size={19} />
                Chọn các vụ án cũ
              </button>

            </div>

            {/* LOADING REPLAY */}

            {pending && (
              <p
                className="lm4-center-status"
                role="status"
              >
                <LoaderCircle
                  size={18}
                  className="lm3-rotate"
                />

                Đang mở lại vụ án...
              </p>
            )}

          </section>
        )}

        {/* ==================================================
            13.7. ERROR
        ================================================== */}

        {error && screen !== 'history' && (

          <div
            className="lm-detective-page-error"
            role="alert"
          >

            <strong>
              Chưa thực hiện được!
            </strong>

            <p>
              {error}
            </p>

          </div>

        )}

      </div>

      {/* ====================================================
          14. CONFIRM LEAVE MODAL
      ==================================================== */}

      {confirmLeave && (

        <div
          className="lm4-modal-backdrop"
          role="presentation"
        >

          <div
            className="lm4-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="lm4-leave-title"
          >

            {/* ĐÓNG */}

            <button
              type="button"
              className="lm4-modal-x"
              aria-label="Đóng"
              onClick={() =>
                setConfirmLeave(false)
              }
            >
              <X size={20} />
            </button>

            {/* BIỂU TƯỢNG */}

            <span
              className="lm4-modal-art"
              aria-hidden="true"
            >
              🔎
            </span>

            {/* NỘI DUNG */}

            <h2 id="lm4-leave-title">
              Con muốn tạm dừng điều tra?
            </h2>

            <p>
              Những manh mối đã tìm được vẫn
              được lưu lại. Con có thể quay
              lại chơi tiếp sau nhé!
            </p>

            {/* HAI LỰA CHỌN */}

            <div className="lm4-modal-actions">

              <button
                type="button"
                className="lm4-modal-continue"
                autoFocus
                onClick={() =>
                  setConfirmLeave(false)
                }
              >
                Tiếp tục điều tra
              </button>

              <button
                type="button"
                className="lm4-modal-leave"
                onClick={() =>
                  navigate('home')
                }
              >
                Về trang Thám tử
              </button>

            </div>

          </div>

        </div>
      )}

    </main>
  );
}
