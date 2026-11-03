
import { apiRequest } from './apiClient';
import type { DetectiveCaseV3 } from '../types/detectiveV3';

import type {
  DetectiveTopicId,
} from '../constants/detectiveTopics';

import type {
  DetectiveCaseData,
  DetectiveHistoryData,
  DetectiveInspectData,
  DetectiveExperimentData,
  DetectiveSolveData,
  DetectiveNarrationData,
  DetectiveNarrationSegment,
} from '../types/detective';

function postJson<T>(
  endpoint: string,
  body: object
) {
  return apiRequest<T>(endpoint, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

function casePath(caseId: string) {
  return `/detective/${encodeURIComponent(caseId)}`;
}

export const detectiveService = {
  // Sinh vụ án mới.
  generateCase(
    childId: number,
    topicId: DetectiveTopicId
  ) {
    return postJson<DetectiveCaseData | DetectiveCaseV3>(
      '/detective/generate',
      {
        child_id: childId,
        topic_id: topicId,
      }
    );
  },

  // Lịch sử 5 vụ án gần nhất.
  getHistory(childId: number) {
    return apiRequest<DetectiveHistoryData>(
      `/detective/history?child_id=${childId}`
    );
  },

  // Khôi phục trạng thái vụ án.
  getCase(caseId: string, childId: number) {
    return apiRequest<DetectiveCaseData | DetectiveCaseV3>(
      `${casePath(caseId)}?child_id=${childId}`
    );
  },

  // Replay không sinh lại AI.
  replayCase(caseId: string, childId: number) {
    return postJson<DetectiveCaseData | DetectiveCaseV3>(
      `${casePath(caseId)}/replay`,
      { child_id: childId }
    );
  },

  // Khám phá vật thể.
  inspectObject(
    caseId: string,
    childId: number,
    objectId: string
  ) {
    return postJson<DetectiveInspectData>(
      `${casePath(caseId)}/inspect`,
      {
        child_id: childId,
        object_id: objectId,
      }
    );
  },

  // Thực hiện thử nghiệm khoa học.
  runExperiment(
    caseId: string,
    childId: number,
    experimentId: string
  ) {
    return postJson<DetectiveExperimentData>(
      `${casePath(caseId)}/experiment`,
      {
        child_id: childId,
        experiment_id: experimentId,
      }
    );
  },

  // Lấy audio Gemini TTS từ Backend.
  getNarration(
    caseId: string,
    childId: number,
    segmentType: DetectiveNarrationSegment,
    segmentId: string | null = null
  ) {
    return postJson<DetectiveNarrationData>(
      `${casePath(caseId)}/narration`,
      {
        child_id: childId,
        segment_type: segmentType,
        segment_id: segmentId,
      }
    );
  },

  // Nộp kết luận, tối đa 2 lượt.
  solveCase(
    caseId: string,
    childId: number,
    hypothesisId: string,
    evidenceIds: string[],
    submissionId: string
  ) {
    return postJson<DetectiveSolveData>(
      `${casePath(caseId)}/solve`,
      {
        child_id: childId,
        hypothesis_id: hypothesisId,
        evidence_ids: evidenceIds,
        submission_id: submissionId,
      }
    );
  },
};
