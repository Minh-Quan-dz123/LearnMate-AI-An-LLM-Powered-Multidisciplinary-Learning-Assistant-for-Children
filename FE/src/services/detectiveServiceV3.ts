
import { apiRequest } from './apiClient';

import type {
  DetectiveHintResponseV3,
  DetectiveSolveV3,
} from '../types/detectiveV3';

/**
 * Đường dẫn API cho một vụ án.
 */
function casePath(caseId: string): string {
  return `/detective/${encodeURIComponent(caseId)}`;
}

/**
 * Helper POST JSON.
 *
 * apiRequest tự thêm API_BASE_URL.
 */
function postJson<T>(
  endpoint: string,
  body: object
) {
  return apiRequest<T>(endpoint, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

/**
 * Các API riêng cho Module 3 V3.
 *
 * Không ảnh hưởng detectiveService V2.
 */
export const detectiveServiceV3 = {

  /**
   * Mở gợi ý tiếp theo.
   *
   * requestId là UUID.
   * Retry phải dùng lại cùng UUID.
   */
  useHint(
    caseId: string,
    childId: number,
    requestId: string
  ) {
    return postJson<DetectiveHintResponseV3>(
      `${casePath(caseId)}/hint`,
      {
        child_id: childId,
        request_id: requestId,
      }
    );
  },

  /**
   * Nộp kết luận bằng cách chọn giả thuyết.
   *
   * Backend so sánh hypothesis_id.
   * Không cần gọi Gemini.
   */
  solveChoice(
    caseId: string,
    childId: number,
    hypothesisId: string,
    submissionId: string
  ) {
    return postJson<DetectiveSolveV3>(
      `${casePath(caseId)}/solve`,
      {
        child_id: childId,
        answer_mode: 'choice',
        hypothesis_id: hypothesisId,
        submission_id: submissionId,
      }
    );
  },

  /**
   * Nộp kết luận tự viết.
   *
   * Backend gọi Gemini để chấm theo ý nghĩa.
   */
  solveOpen(
    caseId: string,
    childId: number,
    answerText: string,
    submissionId: string
  ) {
    return postJson<DetectiveSolveV3>(
      `${casePath(caseId)}/solve`,
      {
        child_id: childId,
        answer_mode: 'open',
        answer_text: answerText,
        submission_id: submissionId,
      }
    );
  },
};
