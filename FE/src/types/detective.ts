
import type {
  DetectiveTopicId,
} from '../constants/detectiveTopics';

export type DetectiveSceneId =
  | 'classroom'
  | 'garden'
  | 'lab';

export type CaseTopicId =
  Exclude<DetectiveTopicId, 'random'>;

export type DetectiveOutcome =
  | 'solved'
  | 'unsolved';

export interface DetectiveObject {
  object_id: string;
  label: string;
  asset_id: string;
  slot_id: string;
}

export interface DetectiveClueVisual {
  kind:
    | 'ai_closeup'
    | 'compare'
    | 'experiment_effect';

  image_url?: string | null;
  before_image_url?: string | null;
  reference_asset_id?: string | null;
  highlight?: string | null;
  alt: string;
}

export interface DetectiveClue {
  id: string;
  title: string;
  description: string;

  reference_asset_id?: string | null;
  visual?: DetectiveClueVisual | null;
}

export interface DetectiveHypothesis {
  id: string;
  label: string;
}

export interface DetectiveExperiment {
  id: string;
  label: string;
}

export interface DetectiveCaseData {
  schema_version?: 2;

  case_id: string;
  topic_id: CaseTopicId;

  title: string;
  introduction: string;

  image_url: string;
  scene_id: DetectiveSceneId;

  objects: DetectiveObject[];
  hypotheses: DetectiveHypothesis[];
  experiments: DetectiveExperiment[];

  discovered_clues: DetectiveClue[];
  discovered_clue_ids: string[];
  completed_experiment_ids: string[];

  selected_hypothesis_id: string | null;

  completed: boolean;
  attempts_used: number;
  outcome: DetectiveOutcome | null;

  retry_feedback?: string | null;
}

export interface DetectiveInspectData {
  clue: DetectiveClue;
  discovered_clue_ids: string[];
  already_discovered: boolean;
}

export interface DetectiveExperimentData {
  result: string;
  unlocked_clue: DetectiveClue;
  already_completed: boolean;
  discovered_clue_ids: string[];
  completed_experiment_ids: string[];
}

export interface DetectiveSolveData {
  completed: boolean;
  outcome: DetectiveOutcome | null;

  attempts_used: number;
  remaining_attempts: number;

  feedback: string;

  title?: string;
  explanation?: string;
  history_count?: number;

  can_retry?: boolean;
}

export interface DetectiveHistoryItem {
  case_id: string;
  title: string;
  topic_id: CaseTopicId;
  last_completed_at: string;
  outcome: DetectiveOutcome;
}

export interface DetectiveHistoryData {
  cases: DetectiveHistoryItem[];
}

export type DetectiveNarrationSegment =
  | 'introduction'
  | 'clue'
  | 'experiment'
  | 'retry_feedback'
  | 'final_explanation';

export interface DetectiveNarrationData {
  audio_url: string;
  mime_type: 'audio/wav';
  cached: boolean;
}
