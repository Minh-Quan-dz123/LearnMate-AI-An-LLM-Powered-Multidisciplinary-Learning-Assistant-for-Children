
import { apiRequest } from './apiClient';

import type {
  QuizGenerateRequest,
  QuizGenerateData,
  OpenGenerateRequest,
  OpenGenerateData,
  OpenEvaluateRequest,
  OpenEvaluateData,
} from '../types/exercise';

/**
 * Service kết nối Frontend với Backend.
 *
 * Module 1: sinh trắc nghiệm.
 * Module 2: sinh câu hỏi mở và chấm câu trả lời.
 *
 * FE không trực tiếp gọi LLM Server.
 */
export const exerciseService = {
  // Module 1: Sinh trắc nghiệm
  generateQuiz(payload: QuizGenerateRequest) {
    return apiRequest<QuizGenerateData>(
      '/exercises/quiz/generate',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  },

  // Module 2: Sinh câu hỏi mở
  generateOpen(payload: OpenGenerateRequest) {
    return apiRequest<OpenGenerateData>(
      '/exercises/open/generate',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  },

  // Module 2: Chấm một câu trả lời mở
  evaluateOpen(payload: OpenEvaluateRequest) {
    return apiRequest<OpenEvaluateData>(
      '/exercises/open/evaluate',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  },
};
