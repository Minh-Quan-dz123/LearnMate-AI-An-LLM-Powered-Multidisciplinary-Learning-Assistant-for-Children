import { CONFIG } from '../constants/config';
import type { ApiResponse } from '../types/api';

/**
 * HTTP Client dùng chung cho Frontend.
 *
 * Chức năng:
 * 1. Tự động gắn API_BASE_URL vào endpoint.
 * 2. Gửi HTTP Request đến Backend.
 * 3. Tự động đọc dữ liệu JSON.
 * 4. Xử lý các lỗi HTTP (400, 401, 422, 500...).
 * 5. Xử lý lỗi kết nối hoặc JSON không hợp lệ.
 * 6. Trả về dữ liệu theo cấu trúc ApiResponse<T>.
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {

  // 1. Xây dựng URL API
  const url =
    `${CONFIG.API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  // 2. Chuẩn bị HTTP Headers
  const headers = new Headers(options.headers);

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  try {
    // 3. Gửi HTTP Request
    const response = await fetch(url, {
      ...options,
      headers,
    });

    // 4. Đọc dữ liệu JSON từ Backend
    const body: unknown = await response.json();

    // 5. Kiểm tra dữ liệu trả về có phải object không
    const value =
      body && typeof body === 'object' && !Array.isArray(body)
        ? body as Partial<ApiResponse<T>> & { detail?: unknown }
        : {};

    // 6. Xử lý các HTTP Error
    if (!response.ok) {
      return {
        success: false,

        message:
          typeof value.message === 'string'
            ? value.message
            : typeof value.detail === 'string'
              ? value.detail
              : `Dữ liệu không hợp lệ hoặc máy chủ lỗi (HTTP ${response.status}).`,

        data: null as T,

        error: value.error ?? {
          code: `HTTP_${response.status}`,
          details: value.detail,
        },
      };
    }

    // 7. Kiểm tra cấu trúc JSON thống nhất của Backend
    if (typeof value.success !== 'boolean') {
      throw new Error(
        'Response của Backend không đúng cấu trúc JSON thống nhất'
      );
    }

    // 8. Trả kết quả về cho service gọi API
    return value as ApiResponse<T>;

  } catch (err) {

    // 9. Xử lý lỗi kết nối hoặc lỗi đọc JSON
    return {
      success: false,

      message: 'Không thể kết nối hoặc đọc phản hồi từ Backend.',

      data: null as T,

      error: {
        code: 'NETWORK_OR_PARSE_ERROR',
        details: err instanceof Error ? err.message : undefined,
      },
    };
  }
}