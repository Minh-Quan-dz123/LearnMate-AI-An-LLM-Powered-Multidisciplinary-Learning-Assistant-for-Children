
import { useEffect, useRef, useState } from 'react';
import type { CSSProperties } from 'react';

import {
  BookOpen,
  Check,
  Expand,
  LoaderCircle,
  Minimize2,
  Search,
} from 'lucide-react';

import type {
  DetectiveObject,
  DetectiveSceneId,
} from '../../types/detective';

import { DetectiveSprite } from './DetectiveSprite';

type Point = { x: number; y: number };
type Size = { width: number; height: number };
type Stage = 'original' | 'fallback' | 'missing';
type Action = 'inspect' | 'experiment' | 'solve' | null;

const SCENE_SLOTS: Record<
  DetectiveSceneId,
  Record<string, Point>
> = {
  classroom: {
    desk_left: { x: 26, y: 73 },
    desk_right: { x: 73, y: 73 },
    window: { x: 75, y: 29 },
    shelf: { x: 19, y: 31 },
  },

  garden: {
    center: { x: 52, y: 61 },
    soil: { x: 35, y: 79 },
    fence: { x: 77, y: 44 },
    corner: { x: 16, y: 55 },
  },

  lab: {
    table_left: { x: 28, y: 73 },
    table_right: { x: 72, y: 73 },
    cabinet: { x: 17, y: 34 },
    window: { x: 81, y: 28 },
  },
};

const LABELS: Record<DetectiveSceneId, string> = {
  classroom: 'Lớp học',
  garden: 'Khu vườn',
  lab: 'Phòng thí nghiệm',
};

const FALLBACK_SIZE: Size = {
  width: 1280,
  height: 720,
};

interface Props {
  sceneId: DetectiveSceneId;
  imageUrl: string;
  objects: DetectiveObject[];
  discoveredCount: number;
  inspectedIds: string[];
  locked: boolean;
  action: Action;
  onInspect: (objectId: string) => void;
}

export function DetectiveScene({
  sceneId,
  imageUrl,
  objects,
  discoveredCount,
  inspectedIds,
  locked,
  action,
  onInspect,
}: Props) {
  const [stage, setStage] = useState<Stage>('original');

  const [size, setSize] = useState<Size>(FALLBACK_SIZE);

  const [expanded, setExpanded] = useState(false);

  const [fitted, setFitted] = useState<Size | null>(null);

  const viewportRef = useRef<HTMLDivElement>(null);

  // Đổi vụ án => tải lại ảnh nền.
  useEffect(() => {
    setStage('original');
    setSize(FALLBACK_SIZE);
  }, [imageUrl, sceneId]);

  // Khóa cuộn nền và hỗ trợ phím Escape.
  useEffect(() => {
    if (!expanded) return;

    const previous = document.body.style.overflow;

    document.body.style.overflow = 'hidden';

    const escape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setExpanded(false);
      }
    };

    document.addEventListener('keydown', escape);

    return () => {
      document.body.style.overflow = previous;
      document.removeEventListener('keydown', escape);
    };
  }, [expanded]);

  // Tính kích thước ảnh phù hợp khi xem toàn màn hình.
  useEffect(() => {
    if (!expanded || !viewportRef.current) {
      setFitted(null);
      return;
    }

    const viewport = viewportRef.current;

    const observer = new ResizeObserver(([entry]) => {
      const widthLimit = entry.contentRect.width;
      const heightLimit = entry.contentRect.height;

      if (widthLimit <= 0 || heightLimit <= 0) {
        return;
      }

      const width = Math.min(
        widthLimit,
        (heightLimit * size.width) / size.height
      );

      setFitted({
        width,
        height: (width * size.height) / size.width,
      });
    });

    observer.observe(viewport);

    return () => observer.disconnect();
  }, [expanded, size.width, size.height]);

  const fallbackUrl =
    `/api/detective/backgrounds/${sceneId}.svg`;

  const imageSrc =
    stage === 'original' ? imageUrl : fallbackUrl;

  // Ảnh và hotspot nằm trong cùng một khung.
  const style: CSSProperties = {
    aspectRatio: `${size.width} / ${size.height}`,

    ...(expanded && fitted
      ? {
          width: fitted.width,
          height: fitted.height,
        }
      : {}),
  };

  return (
    <div
      className={
        `lm3-scene-shell${expanded ? ' is-expanded' : ''}`
      }
    >
      <div className="lm3-scene-top">
        <span>
          <Search size={17} />
          Hiện trường: {LABELS[sceneId]}
        </span>

        <div className="lm3-scene-controls">
          <span className="lm3-found-count">
            <BookOpen size={16} />
            {discoveredCount} manh mối
          </span>

          <button
            type="button"
            className="lm3-scene-expand"
            onClick={() => setExpanded(!expanded)}
            aria-label={
              expanded
                ? 'Thu nhỏ hiện trường'
                : 'Xem hiện trường toàn màn hình'
            }
          >
            {expanded ? (
              <Minimize2 size={17} />
            ) : (
              <Expand size={17} />
            )}

            {expanded ? 'Thu lại' : 'Toàn màn hình'}
          </button>
        </div>
      </div>

      <div
        className="lm3-scene-viewport"
        ref={viewportRef}
      >
        <div
          className="lm3-scene"
          style={style}
          aria-label="Các vật thể có thể khám phá"
        >
          {stage !== 'missing' ? (
            <img
              key={`${stage}:${imageSrc}`}
              className="lm3-scene-image"
              src={imageSrc}
              draggable={false}
              alt={`Hiện trường ${LABELS[sceneId]}`}
              onLoad={(event) => {
                const {
                  naturalWidth,
                  naturalHeight,
                } = event.currentTarget;

                if (
                  naturalWidth > 0 &&
                  naturalHeight > 0
                ) {
                  setSize({
                    width: naturalWidth,
                    height: naturalHeight,
                  });
                }
              }}
              onError={() => {
                setStage((s) =>
                  s === 'original'
                    ? 'fallback'
                    : 'missing'
                );

                setSize(FALLBACK_SIZE);
              }}
            />
          ) : (
            <div
              className="lm3-no-image"
              role="status"
            >
              <span aria-hidden="true">🏞️</span>

              <strong>
                Hiện trường đang dùng nền đơn giản
              </strong>

              <small>
                Con vẫn có thể bấm các vật thể
                để điều tra.
              </small>
            </div>
          )}

          {objects.map((object) => {
            const pos =
              SCENE_SLOTS[sceneId]?.[object.slot_id];

            if (!pos) return null;

            const visited =
              inspectedIds.includes(object.object_id);

            return (
              <button
                key={object.object_id}
                type="button"
                className={
                  `lm3-hotspot${
                    visited ? ' is-visited' : ''
                  }`
                }
                style={{
                  '--lm3-x': `${pos.x}%`,
                  '--lm3-y': `${pos.y}%`,
                } as CSSProperties}
                disabled={locked}
                title={`Khám phá ${object.label}`}
                aria-label={
                  `Khám phá ${object.label}` +
                  (visited ? ', đã kiểm tra' : '')
                }
                onClick={() => {
                  if (expanded) {
                    setExpanded(false);
                  }

                  onInspect(object.object_id);
                }}
              >
                <span className="lm3-hotspot-icon">
                  <DetectiveSprite
                    assetId={object.asset_id}
                  />
                </span>

                <span className="lm3-hotspot-name">
                  {object.label}
                </span>

                {visited && (
                  <span
                    className="lm3-hotspot-tick"
                    aria-hidden="true"
                  >
                    <Check size={11} />
                  </span>
                )}
              </button>
            );
          })}

          {action && (
            <div
              className="lm3-scene-wait"
              role="status"
            >
              <LoaderCircle
                className="lm3-rotate"
                size={28}
              />

              {action === 'inspect'
                ? 'Đang tìm manh mối...'
                : action === 'experiment'
                  ? 'Đang thử nghiệm...'
                  : 'Đang kiểm tra kết luận...'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
