
import { useState } from 'react';

import {
  Eye,
  ImageOff,
  Maximize2,
  Minimize2,
} from 'lucide-react';

import type {
  DetectiveClueVisual as Visual,
} from '../../types/detective';

import { DetectiveSprite } from './DetectiveSprite';

import './DetectiveClueVisual.css';

interface Props {
  visual?: Visual | null;
  title: string;
  assetId?: string | null;
}

export function DetectiveClueVisual({
  visual,
  title,
  assetId,
}: Props) {
  const [zoom, setZoom] = useState(false);

  const [imageError, setImageError] = useState(false);

  const [comparison, setComparison] = useState(50);

  const src = visual?.image_url;

  const hasImage = Boolean(src) && !imageError;

  const hasComparison =
    visual?.kind === 'compare' &&
    Boolean(
      visual.before_image_url ||
      visual.reference_asset_id
    );

  // Không có ảnh => fallback bằng sprite.
  if (!hasImage) {
    return (
      <div
        className="lm3-visual-fallback"
        role="status"
      >
        {assetId ? (
          <div className="lm3-visual-sprite">
            <DetectiveSprite assetId={assetId} />
          </div>
        ) : (
          <ImageOff
            size={36}
            aria-hidden="true"
          />
        )}

        <strong>Hình minh họa vật thể</strong>

        <small>
          Con vẫn có thể dựa vào mô tả
          manh mối để suy luận.
        </small>
      </div>
    );
  }

  return (
    <div className="lm3-visual">
      {hasComparison ? (
        <div className="lm3-visual-compare">
          {visual?.before_image_url ? (
            <img
              src={visual.before_image_url}
              alt={`Hình đối chiếu: ${title}`}
            />
          ) : (
            <div
              className="lm3-visual-compare-sprite"
              aria-label={
                `Vật thể hiện trường: ${title}`
              }
            >
              <DetectiveSprite
                assetId={visual!.reference_asset_id!}
              />
            </div>
          )}

          <div
            className="lm3-visual-compare-front"
            style={{
              clipPath:
                `inset(0 ${100 - comparison}% 0 0)`,
            }}
          >
            <img
              src={src!}
              alt={visual?.alt || title}
              onError={() => setImageError(true)}
            />
          </div>

          <span
            className="lm3-visual-compare-line"
            style={{ left: `${comparison}%` }}
          />

          <label>
            Kéo để đối chiếu vật thể và ảnh dấu vết

            <input
              type="range"
              min={0}
              max={100}
              value={comparison}
              onChange={(event) =>
                setComparison(Number(event.target.value))
              }
            />
          </label>
        </div>
      ) : (
        <img
          className="lm3-visual-image"
          src={src!}
          alt={visual?.alt || title}
          onError={() => setImageError(true)}
        />
      )}

      {visual?.highlight && (
        <div className="lm3-visual-hint">
          <Eye size={16} />
          Hãy quan sát kỹ dấu vết trong hình nhé!
        </div>
      )}

      {visual?.kind === 'experiment_effect' && (
        <span className="lm3-visual-experiment">
          ✨ Đã quan sát hiệu ứng thử nghiệm
        </span>
      )}

      <button
        type="button"
        className="lm3-visual-zoom"
        onClick={() =>
          setZoom((old) => !old)
        }
      >
        {zoom ? (
          <Minimize2 size={16} />
        ) : (
          <Maximize2 size={16} />
        )}

        {zoom ? 'Thu nhỏ' : 'Phóng to'}
      </button>

      {zoom && (
        <div
          className="lm3-visual-lightbox"
          role="presentation"
          onClick={() => setZoom(false)}
        >
          <button
            type="button"
            className="lm3-visual-close"
            aria-label="Đóng ảnh phóng to"
            onClick={() => setZoom(false)}
          >
            Đóng ×
          </button>

          <img
            src={src!}
            alt={visual?.alt || title}
            onClick={(event) =>
              event.stopPropagation()
            }
          />
        </div>
      )}
    </div>
  );
}
