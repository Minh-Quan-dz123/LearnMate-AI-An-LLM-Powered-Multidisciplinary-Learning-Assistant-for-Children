
/**
 * Màn hình chọn hoạt động sau khi chọn hồ sơ bé.
 * Không gọi API. App.tsx quyết định chuyển sang Module 1–2 hoặc Module 3.
 */
import { ArrowRight, BookOpen, Compass, FlaskConical, Sparkles } from 'lucide-react';
import type { ChildProfile } from '../../types/child';
import '../detective/Detective.css';

interface Props {
  child: ChildProfile;
  onChooseLearning: () => void;
  onChooseDetective: () => void;
}

export function ActivitySelect({ child, onChooseLearning, onChooseDetective }: Props) {
  return (
    <main className="lm-choice-screen">
      <div className="lm-choice-heading">
        <span className="lm-detective-eyebrow"><Sparkles size={16} /> LEARNMATE AI</span>
        <h1>Xin chào, {child.name}! <span aria-hidden="true">👋</span></h1>
        <p>Hôm nay con muốn học điều hay hay giải mã một bí ẩn?</p>
      </div>

      <div className="lm-choice-grid">
        <button className="lm-choice-card lm-choice-learn" type="button" onClick={onChooseLearning}>
          <span className="lm-choice-art" aria-hidden="true">
            <span className="lm-choice-art-main">📚</span>
            <span className="lm-choice-art-mini lm-choice-art-top">✏️</span>
            <span className="lm-choice-art-mini lm-choice-art-bottom">⭐</span>
          </span>
          <span className="lm-choice-tag"><BookOpen size={15} /> HỌC TẬP</span>
          <span className="lm-choice-title">Học cùng AI</span>
          <span className="lm-choice-description">Trả lời câu hỏi, luyện suy nghĩ và khám phá kiến thức.</span>
          <span className="lm-choice-action">Vào học ngay <ArrowRight size={19} /></span>
        </button>

        <button className="lm-choice-card lm-choice-detective" type="button" onClick={onChooseDetective}>
          <span className="lm-choice-art" aria-hidden="true">
            <span className="lm-choice-art-main">🕵️</span>
            <span className="lm-choice-art-mini lm-choice-art-top">🔎</span>
            <span className="lm-choice-art-mini lm-choice-art-bottom">🧪</span>
          </span>
          <span className="lm-choice-tag"><FlaskConical size={15} /> TRÒ CHƠI KHOA HỌC</span>
          <span className="lm-choice-title">Thám tử khoa học</span>
          <span className="lm-choice-description">Tìm manh mối, thử nghiệm và giải mã vụ án bí ẩn.</span>
          <span className="lm-choice-action">Đi điều tra <Compass size={19} /></span>
        </button>
      </div>
      <p className="lm-choice-note">Mỗi cuộc khám phá đều có điều thú vị đang chờ con! ✨</p>
    </main>
  );
}
