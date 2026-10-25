import { CONFIG } from '../constants/config';
import type { ApiResponse } from '../types/api';

/**
 * HTTP Client tiện ích cho Frontend:
 * - Tự động gắn baseURL (/api)
 * - Tự động parse JSON
 * - Xử lý thông báo lỗi chuẩn tiếng Việt
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = `${CONFIG.API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    const data: ApiResponse<T> = await response.json();

    if (!response.ok && !data.error) {
      // Trường hợp BE trả status HTTP lỗi mà không có envelope chuẩn
      return {
        success: false,
        message: data.message || `Lỗi máy chủ (${response.status})`,
        data: null as any,
        error: {
          code: `HTTP_${response.status}`,
        },
      };
    }

    return data;
  } catch (err: any) {
    return {
      success: false,
      message: 'Không thể kết nối đến máy chủ. Vui lòng kiểm tra lại mạng!',
      data: null as any,
      error: {
        code: 'NETWORK_ERROR',
        details: err.message,
      },
    };
  }
}
