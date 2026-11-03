
/**
 * FILE: ExerciseSetup.tsx
 *
 * MỤC ĐÍCH:
 * - Hiển thị môn học bằng các thẻ có hình minh họa.
 * - Hiển thị chủ đề theo môn học.
 * - Mặc định chỉ hiện một phần danh sách chủ đề.
 * - Có nút Xem thêm / Thu gọn sinh động.
 * - Cấu hình mức độ, dạng bài và số câu.
 *
 * Không xử lý API hoặc logic chấm điểm.
 */

import { useId, useState } from 'react';

import {
  Check,
  ChevronDown,
  House,
  Sparkles,
} from 'lucide-react';

import type {
  Level,
  QuestionType,
  Subject,
} from '../../types/exercise';

import { SUBJECT_TOPICS } from '../../constants/subjects';

import {
  CUSTOM_ART,
  ExerciseArtwork,
  getTopicArt,
  RANDOM_ART,
  SUBJECT_ART,
} from './ExerciseArtwork';

import './ExerciseSetup.css';

// =====================================================
// 1. PROPS NHẬN TỪ EXERCISE PAGE
// =====================================================

interface Props {
  subject: Subject;
  topicChoice: string;
  customTopic: string;
  level: Level;
  questionType: QuestionType;
  questionCount: number;
  busy: boolean;
  status: string;

  onGoHome: () => void;

  onSubjectChange: (subject: Subject) => void;
  onTopicChange: (topic: string) => void;
  onCustomTopicChange: (text: string) => void;

  onLevelChange: (level: Level) => void;
  onQuestionTypeChange: (type: QuestionType) => void;
  onQuestionCountChange: (count: number) => void;

  onStart: () => void;
}

// =====================================================
// 2. COMPONENT CHÍNH
// =====================================================

export function ExerciseSetup(props: Props) {
  const {
    subject,
    topicChoice,
    customTopic,
    level,
    questionType,
    questionCount,
    busy,
    status,
    onGoHome,
    onSubjectChange,
    onTopicChange,
    onCustomTopicChange,
    onLevelChange,
    onQuestionTypeChange,
    onQuestionCountChange,
    onStart,
  } = props;

  // ===================================================
  // 2.1. STATE MỞ RỘNG / THU GỌN CHỦ ĐỀ
  // ===================================================

  /**
   * false: Chỉ hiện một phần danh sách.
   * true:  Hiển thị toàn bộ chủ đề.
   *
   * Số lượng mặc định được CSS kiểm soát:
   * - Desktop: 6 lựa chọn.
   * - Mobile: 4 lựa chọn.
   */
  const [showAllTopics, setShowAllTopics] =
    useState(false);

  // ID duy nhất giúp nút mở rộng liên kết
  // với danh sách chủ đề qua aria-controls.
  const topicGridId = useId();

  // ===================================================
  // 2.2. DANH SÁCH MÔN HỌC / CHỦ ĐỀ
  // ===================================================

  const subjects =
    Object.keys(SUBJECT_TOPICS) as Subject[];

  const topics = SUBJECT_TOPICS[subject];

  const allTopics = [
    ...topics,
    'Ngẫu nhiên',
    'Chủ đề khác',
  ];

  // Số lựa chọn không hiển thị lúc ban đầu.
  const hiddenDesktop = Math.max(
    0,
    allTopics.length - 6
  );

  const hiddenMobile = Math.max(
    0,
    allTopics.length - 4
  );

  // Chỉ cần nút mở rộng khi danh sách
  // dài hơn giới hạn hiển thị.
  const hasMoreTopics = allTopics.length > 4;

  // ===================================================
  // 2.3. CÁC HÀM XỬ LÝ GIAO DIỆN
  // ===================================================

  /**
   * Khi đổi môn học:
   * - Cập nhật môn học thông qua component cha.
   * - Thu gọn danh sách chủ đề của môn mới.
   *
   * Việc chọn chủ đề đầu tiên của môn mới
   * do ExercisePage xử lý như trước.
   */
  const handleSubjectChange = (next: Subject) => {
    setShowAllTopics(false);
    onSubjectChange(next);
  };

  /**
   * Đảo trạng thái mở rộng / thu gọn.
   *
   * Không làm thay đổi chủ đề đang chọn.
   */
  const toggleTopics = () => {
    setShowAllTopics((prev) => !prev);
  };

  return (
    <section
      className="setup-panel"
      aria-label="Cấu hình bài tập"
    >
      {/* =========================================
          NÚT TRỞ VỀ
      ========================================= */}

      <button
        className="btn btn-outline setup-home"
        type="button"
        onClick={onGoHome}
        disabled={busy}
      >
        <House size={18} />
        Về màn hình chính
      </button>

      {/* =========================================
          TIÊU ĐỀ
      ========================================= */}

      <div className="setup-heading">
        <span className="setup-heading-icon">
          <Sparkles size={29} />
        </span>

        <div>
          <h2>Hôm nay con muốn học gì?</h2>

          <p>
            Chạm vào hình con thích để bắt đầu
            khám phá nhé!
          </p>
        </div>
      </div>

      {/* =========================================
          BƯỚC 1: CHỌN MÔN HỌC
      ========================================= */}

      <div className="setup-section">
        <h3>
          <span className="setup-step">1</span>
          Chọn môn học
        </h3>

        <div
          className="setup-subject-grid"
          role="group"
          aria-label="Môn học"
        >
          {subjects.map((name) => {
            const art = SUBJECT_ART[name];
            const active = subject === name;

            return (
              <button
                key={name}
                type="button"
                disabled={busy}
                className={
                  `setup-card setup-subject ${
                    active ? 'is-selected' : ''
                  }`
                }
                aria-pressed={active}
                onClick={() =>
                  handleSubjectChange(name)
                }
              >
                {active && (
                  <span className="setup-check">
                    <Check size={17} />
                  </span>
                )}

                <ExerciseArtwork art={art} />

                <strong>{name}</strong>

                <small>{art.caption}</small>
              </button>
            );
          })}
        </div>
      </div>

      {/* =========================================
          BƯỚC 2: CHỌN CHỦ ĐỀ
      ========================================= */}

      <div className="setup-section">
        <h3>
          <span className="setup-step">2</span>
          Chọn chủ đề
        </h3>

        <p className="setup-help">
          Con muốn tìm hiểu điều gì trong môn {subject}?
        </p>

        {/* DANH SÁCH CHỦ ĐỀ */}

        <div
          id={topicGridId}
          className={
            `setup-topic-grid ${
              showAllTopics ? 'is-expanded' : ''
            }`
          }
          role="group"
          aria-label="Chủ đề"
        >
          {allTopics.map((name, index) => {
            // Lấy hình minh họa tương ứng.
            const art =
              name === 'Ngẫu nhiên'
                ? RANDOM_ART
                : name === 'Chủ đề khác'
                  ? CUSTOM_ART
                  : getTopicArt(name, index);

            const active = topicChoice === name;

            return (
              <button
                key={name}
                type="button"
                disabled={busy}
                className={
                  `setup-card setup-topic ${
                    active ? 'is-selected' : ''
                  }`
                }
                aria-pressed={active}
                onClick={() =>
                  onTopicChange(name)
                }
              >
                {active && (
                  <span className="setup-check">
                    <Check size={17} />
                  </span>
                )}

                <ExerciseArtwork art={art} />

                <strong>{name}</strong>
              </button>
            );
          })}
        </div>

        {/* =====================================
            NÚT XEM THÊM / THU GỌN CHỦ ĐỀ
        ===================================== */}

        {hasMoreTopics && (
          <div
            className={
              `setup-more-wrapper ${
                allTopics.length <= 6
                  ? 'setup-more-mobile-only'
                  : ''
              }`
            }
          >
            <button
              type="button"
              className={
                `setup-more-button ${
                  showAllTopics ? 'is-expanded' : ''
                }`
              }
              onClick={toggleTopics}
              disabled={busy}
              aria-expanded={showAllTopics}
              aria-controls={topicGridId}
            >
              {/* Biểu tượng trang trí */}
              <span className="setup-more-sparkle">
                <Sparkles size={23} />
              </span>

              {/* Nội dung của nút */}
              <span className="setup-more-content">
                <strong>
                  {showAllTopics
                    ? 'Thu gọn chủ đề'
                    : 'Khám phá thêm chủ đề'}
                </strong>

                <small>
                  {showAllTopics ? (
                    'Hiển thị ít lựa chọn hơn'
                  ) : (
                    <>
                      <span className="setup-count-desktop">
                        Còn {hiddenDesktop} lựa chọn thú vị nữa!
                      </span>

                      <span className="setup-count-mobile">
                        Còn {hiddenMobile} lựa chọn thú vị nữa!
                      </span>
                    </>
                  )}
                </small>
              </span>

              {/* Mũi tên có hiệu ứng chuyển động */}
              <span className="setup-more-arrow">
                <ChevronDown
                  size={25}
                  strokeWidth={2.6}
                />
              </span>
            </button>
          </div>
        )}

        {/* =====================================
            CHỦ ĐỀ TÙY CHỈNH
        ===================================== */}

        {topicChoice === 'Chủ đề khác' && (
          <div className="setup-custom-topic">
            <label htmlFor="customTopic">
              Con muốn học về chủ đề gì?
            </label>

            <input
              id="customTopic"
              className="setup-input"
              type="text"
              maxLength={100}
              value={customTopic}
              disabled={busy}
              placeholder="Ví dụ: Các hành tinh"
              onChange={(e) =>
                onCustomTopicChange(e.target.value)
              }
            />
          </div>
        )}
      </div>

      {/* =========================================
          BƯỚC 3: CẤU HÌNH CÁCH HỌC
      ========================================= */}

      <div className="setup-section">
        <h3>
          <span className="setup-step">3</span>
          Chọn cách học
        </h3>

        <div className="setup-options">
          {/* MỨC ĐỘ */}
          <div>
            <label htmlFor="level">
              Mức độ
            </label>

            <select
              id="level"
              className="setup-input"
              value={level}
              disabled={busy}
              onChange={(e) =>
                onLevelChange(
                  e.target.value as Level
                )
              }
            >
              <option>Cơ bản</option>
              <option>Nâng cao</option>
            </select>
          </div>

          {/* DẠNG BÀI */}
          <div>
            <label htmlFor="questionType">
              Dạng bài
            </label>

            <select
              id="questionType"
              className="setup-input"
              value={questionType}
              disabled={busy}
              onChange={(e) =>
                onQuestionTypeChange(
                  e.target.value as QuestionType
                )
              }
            >
              <option>
                Trắc nghiệm một đáp án
              </option>

              <option>
                Trắc nghiệm nhiều đáp án
              </option>

              <option>
                Câu trả lời mở
              </option>
            </select>
          </div>

          {/* SỐ CÂU */}
          <div>
            <label htmlFor="questionCount">
              Số câu (1–5)
            </label>

            <input
              id="questionCount"
              className="setup-input"
              type="number"
              min={1}
              max={5}
              value={questionCount}
              disabled={busy}
              onChange={(e) =>
                onQuestionCountChange(
                  Number(e.target.value)
                )
              }
            />
          </div>
        </div>
      </div>

      {/* =========================================
          NÚT TẠO BÀI
      ========================================= */}

      <button
        type="button"
        className="btn btn-primary setup-start"
        disabled={busy}
        onClick={onStart}
      >
        {busy
          ? status
          : '🚀 Bắt đầu học thôi!'}
      </button>
    </section>
  );
}
