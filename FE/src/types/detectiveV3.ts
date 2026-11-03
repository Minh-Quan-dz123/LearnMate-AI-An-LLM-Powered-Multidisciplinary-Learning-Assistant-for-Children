
import type {
  CaseTopicId,
  DetectiveSceneId,
  DetectiveHypothesis,
  DetectiveOutcome,
  DetectiveSolveData,
} from './detective';

/**
 * Vùng khoanh do Gemini Vision xác định
 * trên ảnh Cloudflare thực tế.
 *
 * Tọa độ tính theo phần trăm 0–100.
 */
export interface HintRegion {
  x: number;
  y: number;
  width: number;
  height: number;
  shape: 'circle' | 'rect';
}

/**
 * Một gợi ý đã được mở.
 *
 * Backend không gửi gợi ý chưa mở.
 */
export interface DetectiveHintV3 {
  id: string;
  order: number;
  title: string;
  content: string;
  region: HintRegion;
}

export interface DetectiveCaseV3 {
  schema_version: 3;

  case_id: string;
  topic_id: CaseTopicId;
  scene_id: DetectiveSceneId;

  title: string;
  introduction: string;
  image_url: string;

  hint_count: number;
  revealed_hints: DetectiveHintV3[];
  hints_used: number;

  hypotheses: DetectiveHypothesis[];

  attempts_used: number;
  completed: boolean;
  outcome: DetectiveOutcome | null;

  explanation?: string;
  last_submission_result?: DetectiveSolveV3 | null;
}

/**
 * Response khi bấm Dùng gợi ý.
 */
export interface DetectiveHintResponseV3 {
  hint: DetectiveHintV3;

  revealed_hint_ids: string[];

  hints_used: number;
  hint_count: number;
  remaining_hints: number;

  already_revealed_for_request: boolean;
}

/**
 * Kết quả kết luận V3.
 *
 * is_correct: kết luận có đúng không.
 * reasoning_support: mức độ có cơ sở.
 */
export interface DetectiveSolveV3
  extends DetectiveSolveData {
  is_correct: boolean;

  reasoning_support:
    | 'strong'
    | 'partial'
    | 'insufficient';
}
