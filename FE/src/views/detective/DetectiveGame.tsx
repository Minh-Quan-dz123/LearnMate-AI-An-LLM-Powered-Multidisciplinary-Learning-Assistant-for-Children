
import { useRef, useState } from 'react';

import {
  BookOpen,
  Check,
  CircleAlert,
  FlaskConical,
  Lightbulb,
  LoaderCircle,
  Search,
  Sparkles,
  X,
} from 'lucide-react';

import { detectiveService } from '../../services/detectiveService';

import type {
  DetectiveCaseData,
  DetectiveClue,
  DetectiveSolveData,
} from '../../types/detective';

import { DetectiveSprite } from './DetectiveSprite';
import { DetectiveScene } from './DetectiveScene';
import { DetectiveClueModal } from './DetectiveClueModal';
import { DetectiveAudioPlayer } from './DetectiveAudioPlayer';

import './DetectiveGame.css';

interface Props {
  childId: number;
  caseData: DetectiveCaseData;
  onCaseChange: (next: DetectiveCaseData) => void;
  onSolved: (result: DetectiveSolveData) => void;
  onBusyChange: (busy: boolean) => void;
}

type Tab = 'notebook' | 'experiments' | 'conclusion';
type Action = 'inspect' | 'experiment' | 'solve' | null;

type CluePopup = {
  clue: DetectiveClue;
  experimentId?: string;
  title: string;
  detail?: string;
};

export function DetectiveGame({
  childId,
  caseData,
  onCaseChange,
  onSolved,
  onBusyChange,
}: Props) {
  const [tab, setTab] = useState<Tab>('notebook');
  const [action, setAction] = useState<Action>(null);

  // Ngăn hai thao tác API cùng chạy.
  const requestLock = useRef(false);

  // Retry cùng một request giữ nguyên submission_id.
  const pendingSolve = useRef<{
    signature: string;
    id: string;
  } | null>(null);

  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const [popup, setPopup] = useState<CluePopup | null>(null);

  const [inspectedIds, setInspectedIds] = useState<string[]>([]);

  const [hypothesisId, setHypothesisId] = useState(
    caseData.selected_hypothesis_id ?? ''
  );

  const [evidenceIds, setEvidenceIds] = useState<string[]>([]);

  const busy = action !== null;
  const locked = busy || caseData.completed;

  function begin(next: Exclude<Action, null>): boolean {
    if (requestLock.current || caseData.completed) {
      return false;
    }

    requestLock.current = true;
    onBusyChange(true);

    setAction(next);
    setError('');
    setNotice('');
    setPopup(null);

    return true;
  }

  function finish() {
    requestLock.current = false;
    setAction(null);
    onBusyChange(false);
  }

  // ==================================================
  // 1. KHÁM PHÁ VẬT THỂ
  // ==================================================

  async function inspect(objectId: string) {
    if (!begin('inspect')) return;

    try {
      const response = await detectiveService.inspectObject(
        caseData.case_id,
        childId,
        objectId
      );

      if (!response.success || !response.data) {
        setError(
          response.message || 'Chưa thể kiểm tra vật thể này.'
        );
        return;
      }

      const {
        clue,
        discovered_clue_ids,
        already_discovered,
      } = response.data;

      onCaseChange({
        ...caseData,
        discovered_clue_ids,
        discovered_clues: caseData.discovered_clues.some(
          (item) => item.id === clue.id
        )
          ? caseData.discovered_clues
          : [...caseData.discovered_clues, clue],
      });

      setInspectedIds((old) =>
        old.includes(objectId) ? old : [...old, objectId]
      );

      setPopup({
        clue,
        title: already_discovered
          ? 'Manh mối đã biết'
          : 'Tìm thấy manh mối mới!',
      });
    } catch {
      setError(
        'Không thể khám phá vật thể. Con hãy thử lại nhé!'
      );
    } finally {
      finish();
    }
  }

  // ==================================================
  // 2. THỰC HIỆN THỬ NGHIỆM
  // ==================================================

  async function experiment(experimentId: string) {
    if (!begin('experiment')) return;

    try {
      const response = await detectiveService.runExperiment(
        caseData.case_id,
        childId,
        experimentId
      );

      if (!response.success || !response.data) {
        setError(
          response.message || 'Chưa thể thực hiện thử nghiệm.'
        );
        return;
      }

      const {
        unlocked_clue,
        result,
        already_completed,
        discovered_clue_ids,
        completed_experiment_ids,
      } = response.data;

      onCaseChange({
        ...caseData,
        discovered_clue_ids,
        completed_experiment_ids,
        discovered_clues: caseData.discovered_clues.some(
          (item) => item.id === unlocked_clue.id
        )
          ? caseData.discovered_clues
          : [...caseData.discovered_clues, unlocked_clue],
      });

      setPopup({
        clue: unlocked_clue,
        title: already_completed
          ? 'Xem lại thử nghiệm'
          : 'Thử nghiệm thành công!',
        detail: result,
        experimentId,
      });
    } catch {
      setError(
        'Có lỗi khi thử nghiệm. Con hãy thử lại nhé!'
      );
    } finally {
      finish();
    }
  }

  // ==================================================
  // 3. CHỌN MANH MỐI (KHÔNG BẮT BUỘC)
  // ==================================================

  function toggleEvidence(id: string) {
    setEvidenceIds((old) =>
      old.includes(id)
        ? old.filter((item) => item !== id)
        : [...old, id]
    );
  }

  // ==================================================
  // 4. NỘP KẾT LUẬN — TỐI ĐA 2 LƯỢT
  // ==================================================

  async function solve() {
    if (!hypothesisId) {
      setError('Con hãy chọn một giả thuyết trước nhé!');
      return;
    }

    if (!begin('solve')) return;

    const signature = JSON.stringify([
      hypothesisId,
      [...evidenceIds].sort(),
    ]);

    if (pendingSolve.current?.signature !== signature) {
      const id =
        globalThis.crypto?.randomUUID?.() ??
        `${Date.now()}-${Math.random().toString(36).slice(2)}`;

      pendingSolve.current = { signature, id };
    }

    try {
      const response = await detectiveService.solveCase(
        caseData.case_id,
        childId,
        hypothesisId,
        evidenceIds,
        pendingSolve.current!.id
      );

      if (!response.success || !response.data) {
        setError(
          response.message || 'Chưa thể kiểm tra kết luận.'
        );
        return;
      }

      pendingSolve.current = null;

      if (response.data.completed) {
        onSolved(response.data);
      } else {
        onCaseChange({
          ...caseData,
          selected_hypothesis_id: hypothesisId,
          attempts_used: response.data.attempts_used,
          retry_feedback: response.data.feedback,
          outcome: response.data.outcome,
          completed: false,
        });

        setNotice(
          response.data.feedback ||
            'Con còn một cơ hội nữa nhé!'
        );
      }
    } catch {
      setError(
        'Không thể gửi kết luận. Con hãy thử lại nhé!'
      );
    } finally {
      finish();
    }
  }

  return (
    <section
      className="lm3-game"
      aria-label="Trò chơi Thám tử khoa học"
    >
      {/* ========== GIỚI THIỆU VỤ ÁN ========== */}
      <header className="lm3-intro">
        <span className="lm-detective-eyebrow">
          <Search size={16} />
          HỒ SƠ VỤ ÁN
        </span>

        <h1>{caseData.title}</h1>
        <p>{caseData.introduction}</p>

        <DetectiveAudioPlayer
          caseId={caseData.case_id}
          childId={childId}
          segmentType="introduction"
          autoPlayOnStart
          text={`${caseData.title}. ${caseData.introduction}`}
        />
      </header>

      <div className="lm3-layout">
        {/* ========== HIỆN TRƯỜNG ========== */}
        <div className="lm3-left">
          <DetectiveScene
            sceneId={caseData.scene_id}
            imageUrl={caseData.image_url}
            objects={caseData.objects}
            discoveredCount={
              caseData.discovered_clue_ids.length
            }
            inspectedIds={inspectedIds}
            locked={locked}
            action={action}
            onInspect={(objectId) => void inspect(objectId)}
          />

          <p className="lm3-help">
            <Sparkles size={17} />
            Chạm hoặc bấm vào đồ vật có viền sáng
            để khám phá!
          </p>

          {/* HƯỚNG DẪN CHƠI */}
          <details className="lm5-game-guide">
            <summary>
              📖 Con chưa biết cách chơi? Xem hướng dẫn nhé!
            </summary>

            <div className="lm5-game-guide-content">
              <div>
                <span aria-hidden="true">🔎</span>
                <p>
                  <strong>Bước 1 – Tìm manh mối</strong>
                  <small>
                    Bấm vào các vật thể có viền sáng
                    trong hiện trường để khám phá.
                  </small>
                </p>
              </div>

              <div>
                <span aria-hidden="true">🧪</span>
                <p>
                  <strong>Bước 2 – Làm thử nghiệm</strong>
                  <small>
                    Mở tab Thử nghiệm để kiểm tra
                    những dấu hiệu đáng ngờ.
                  </small>
                </p>
              </div>

              <div>
                <span aria-hidden="true">💡</span>
                <p>
                  <strong>Bước 3 – Đưa ra kết luận</strong>
                  <small>
                    Chọn giả thuyết. Con có thể chọn thêm
                    manh mối để giải thích suy nghĩ.
                  </small>
                </p>
              </div>
            </div>
          </details>

          {/* POPUP MANH MỐI */}
          {popup && (
            <DetectiveClueModal
              caseId={caseData.case_id}
              childId={childId}
              experimentId={popup.experimentId}
              clue={popup.clue}
              title={popup.title}
              detail={popup.detail}
              onClose={() => setPopup(null)}
            />
          )}
        </div>

        {/* ========== BỘ DỤNG CỤ THÁM TỬ ========== */}
        <aside
          className="lm3-tools"
          aria-label="Bộ dụng cụ thám tử"
        >
          <div
            className="lm3-tabs"
            role="group"
            aria-label="Chọn công cụ điều tra"
          >
            <button
              type="button"
              className={tab === 'notebook' ? 'active' : ''}
              onClick={() => setTab('notebook')}
              aria-pressed={tab === 'notebook'}
            >
              <BookOpen size={19} />
              <span>Sổ tay</span>
            </button>

            <button
              type="button"
              className={
                tab === 'experiments' ? 'active' : ''
              }
              onClick={() => setTab('experiments')}
              aria-pressed={tab === 'experiments'}
            >
              <FlaskConical size={19} />
              <span>Thử nghiệm</span>
            </button>

            <button
              type="button"
              className={
                tab === 'conclusion' ? 'active' : ''
              }
              onClick={() => setTab('conclusion')}
              aria-pressed={tab === 'conclusion'}
            >
              <Lightbulb size={19} />
              <span>Kết luận</span>
            </button>
          </div>

          <div className="lm3-panel">
            {/* ========== SỔ TAY ========== */}
            {tab === 'notebook' && (
              <>
                <h2>📒 Sổ manh mối</h2>

                <p>
                  Mỗi manh mối giúp con đến gần
                  lời giải hơn.
                </p>

                {caseData.discovered_clues.length === 0 ? (
                  <div className="lm3-empty">
                    🔎 Chưa có manh mối nào.
                    Hãy bấm vào đồ vật trong hiện trường!
                  </div>
                ) : (
                  caseData.discovered_clues.map((clue) => (
                    <button
                      type="button"
                      className="lm3-clue lm3-clue-card"
                      key={clue.id}
                      onClick={() =>
                        setPopup({
                          clue,
                          title: 'Xem lại manh mối',
                        })
                      }
                    >
                      {clue.visual?.image_url ? (
                        <img
                          src={clue.visual.image_url}
                          alt={clue.visual.alt}
                          className="lm3-clue-thumbnail"
                        />
                      ) : (
                        <span
                          className="lm3-clue-thumbnail-fallback"
                          aria-hidden="true"
                        >
                          {clue.reference_asset_id ? (
                            <DetectiveSprite
                              assetId={clue.reference_asset_id}
                            />
                          ) : (
                            '🔎'
                          )}
                        </span>
                      )}

                      <span className="lm3-clue-card-text">
                        <strong>
                          <Check size={16} />
                          {clue.title}
                        </strong>

                        <small>{clue.description}</small>
                      </span>
                    </button>
                  ))
                )}
              </>
            )}

            {/* ========== THỬ NGHIỆM ========== */}
            {tab === 'experiments' && (
              <>
                <h2>🧪 Thử nghiệm khoa học</h2>

                <p>
                  Thử một cách an toàn để
                  kiểm chứng điều con nghĩ.
                </p>

                {caseData.experiments.map((item) => {
                  const done =
                    caseData.completed_experiment_ids.includes(
                      item.id
                    );

                  return (
                    <button
                      key={item.id}
                      type="button"
                      className="lm3-experiment"
                      disabled={locked}
                      onClick={() =>
                        void experiment(item.id)
                      }
                    >
                      <FlaskConical size={20} />

                      <span>
                        <strong>{item.label}</strong>

                        <small>
                          {done
                            ? 'Đã làm – bấm xem lại'
                            : 'Bấm để thực hiện'}
                        </small>
                      </span>

                      {done && <Check size={18} />}
                    </button>
                  );
                })}
              </>
            )}

            {/* ========== KẾT LUẬN ========== */}
            {tab === 'conclusion' && (
              <>
                <h2>💡 Kết luận vụ án</h2>

                <p>
                  Chọn giả thuyết con tin là đúng.
                  Manh mối là tùy chọn.
                </p>

                <p
                  className="lm3-attempt-counter"
                  role="status"
                >
                  {caseData.attempts_used === 0
                    ? '🔎 Lượt kết luận 1/2'
                    : '💡 Cơ hội cuối 2/2'}
                </p>

                <h3>1. Giả thuyết của con</h3>

                {caseData.hypotheses.map((item) => (
                  <label
                    key={item.id}
                    className="lm3-choice"
                  >
                    <input
                      type="radio"
                      name={
                        `detective-hypothesis-${caseData.case_id}`
                      }
                      checked={hypothesisId === item.id}
                      onChange={() =>
                        setHypothesisId(item.id)
                      }
                      disabled={locked}
                    />

                    <span>{item.label}</span>
                  </label>
                ))}

                <h3>2. Manh mối (không bắt buộc)</h3>

                {caseData.discovered_clues.length === 0 && (
                  <p>
                    Con có thể nộp kết luận ngay cả khi
                    chưa có manh mối.
                  </p>
                )}

                {caseData.discovered_clues.map((clue) => (
                  <label
                    key={clue.id}
                    className="lm3-choice"
                  >
                    <input
                      type="checkbox"
                      checked={evidenceIds.includes(clue.id)}
                      onChange={() =>
                        toggleEvidence(clue.id)
                      }
                      disabled={locked}
                    />

                    <span>{clue.title}</span>
                  </label>
                ))}

                <button
                  type="button"
                  className="lm3-submit"
                  disabled={locked}
                  onClick={() => void solve()}
                >
                  {action === 'solve' ? (
                    <LoaderCircle
                      size={18}
                      className="lm3-rotate"
                    />
                  ) : (
                    <Lightbulb size={19} />
                  )}

                  Nộp kết luận
                </button>
              </>
            )}
          </div>
        </aside>
      </div>

      {/* ========== THÔNG BÁO LỖI ========== */}
      {error && (
        <div
          className="lm3-message lm3-message-error"
          role="alert"
        >
          <CircleAlert size={20} />

          <span>{error}</span>

          <button
            type="button"
            onClick={() => setError('')}
            aria-label="Đóng thông báo lỗi"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* GIỌNG CÔ GIÁO ĐỌC GỢI Ý SAU LƯỢT SAI */}
      {caseData.attempts_used === 1 &&
        !caseData.completed && (
          <DetectiveAudioPlayer
            caseId={caseData.case_id}
            childId={childId}
            segmentType="retry_feedback"
            text={
              caseData.retry_feedback ||
              notice ||
              'Con hãy xem lại dấu vết nhé!'
            }
          />
        )}

      {notice && (
        <div
          className="lm3-message lm3-message-note"
          role="status"
        >
          <Lightbulb size={20} />

          <span>{notice}</span>

          <button
            type="button"
            onClick={() => setNotice('')}
            aria-label="Đóng thông báo"
          >
            <X size={16} />
          </button>
        </div>
      )}
    </section>
  );
}
