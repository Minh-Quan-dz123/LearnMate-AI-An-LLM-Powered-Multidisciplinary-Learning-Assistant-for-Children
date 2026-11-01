/**
 * Định nghĩa envelope chuẩn cho mọi phản hồi từ Backend
 */
export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data: T;
  error?: {
    code: string;
    details?: any;
  };
}
