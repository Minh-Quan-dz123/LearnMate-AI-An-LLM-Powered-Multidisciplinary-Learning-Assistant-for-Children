
import {
  useEffect,
  useId,
  useRef,
} from 'react';

import {
  Check,
  FlaskConical,
  Search,
  X,
} from 'lucide-react';

import type {
  DetectiveClue,
} from '../../types/detective';

import { DetectiveClueVisual } from './DetectiveClueVisual';
import { DetectiveAudioPlayer } from './DetectiveAudioPlayer';

import './DetectiveClueModal.css';

interface Props {
  clue: DetectiveClue;
  title: string;
  detail?: string;
  onClose: () => void;

  caseId: string;
  childId: number;
  experimentId?: string | null;
}

export function DetectiveClueModal({
  clue,
  title,
  detail,
  onClose,
  caseId,
  childId,
  experimentId = null,
}: Props) {
  const titleId = useId();
  const descriptionId = useId();

  const closeButtonRef =
    useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const previouslyFocused =
      document.activeElement as HTMLElement | null;

    const previousOverflow =
      document.body.style.overflow;

    document.body.style.overflow = 'hidden';

    closeButtonRef.current?.focus();

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
      }
    };

    window.addEventListener('keydown', onKeyDown);

    return () => {
      window.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = previousOverflow;
      previouslyFocused?.focus();
    };
  }, [onClose]);

  return (
    <div
      className="lm5-clue-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <section
        className="lm5-clue-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
      >
        <button
          className="lm5-clue-x"
          type="button"
          aria-label="Đóng cửa sổ manh mối"
          onClick={onClose}
        >
          <X size={20} />
        </button>

        <div
          className="lm5-clue-illustration"
          aria-hidden="true"
        >
          {detail ? (
            <FlaskConical size={37} />
          ) : (
            <Search size={37} />
          )}
          <span>✨</span>
        </div>

        <p className="lm5-clue-kicker">
          {title}
        </p>

        <h2 id={titleId}>
          {clue.title}
        </h2>

        {/* Minh họa manh mối Cloudflare */}
        <DetectiveClueVisual
          visual={clue.visual}
          title={clue.title}
          assetId={clue.reference_asset_id}
        />

        <p
          className="lm5-clue-description"
          id={descriptionId}
        >
          {clue.description}
        </p>

        {/* Kết quả thử nghiệm */}
        {detail && (
          <div className="lm5-clue-experiment-result">
            <strong>
              <FlaskConical size={17} />
              Kết quả thử nghiệm
            </strong>

            <p>{detail}</p>
          </div>
        )}

        {/* Giọng cô giáo */}
        <DetectiveAudioPlayer
          key={`${clue.id}:${experimentId ?? 'clue'}`}
          caseId={caseId}
          childId={childId}
          segmentType={
            experimentId ? 'experiment' : 'clue'
          }
          segmentId={experimentId ?? clue.id}
          label="Nghe cô giải thích"
          text={
            experimentId && detail
              ? detail
              : `${clue.title}. ${clue.description}`
          }
        />

        <p className="lm5-clue-reminder">
          Manh mối này đã có trong sổ tay của con.
        </p>

        <button
          type="button"
          className="lm5-clue-confirm"
          ref={closeButtonRef}
          onClick={onClose}
        >
          <Check size={19} />
          Đã hiểu, tiếp tục điều tra!
        </button>
      </section>
    </div>
  );
}



