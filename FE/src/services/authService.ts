import { CONFIG } from '../constants/config';
import { apiRequest } from './apiClient';
import type { ApiResponse } from '../types/api';
import type { User, LoginPayload, RegisterPayload } from '../types/auth';

// Key lưu trữ localStorage
const STORAGE_KEY_USER = 'learnmate_user';

export const authService = {
  // Lấy user đã lưu
  getCurrentUser(): User | null {
    const raw = localStorage.getItem(STORAGE_KEY_USER);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  },

  // Đăng xuất (xóa user khỏi localStorage)
  logout(): void {
    localStorage.removeItem(STORAGE_KEY_USER);
    localStorage.removeItem('learnmate_active_child_id');
  },

  // Đăng ký
  async register(payload: RegisterPayload): Promise<ApiResponse<User>> {
    if (CONFIG.USE_MOCK) {
      // Giả lập network delay 300ms
      await new Promise((r) => setTimeout(r, 300));
      if (!payload.username.trim() || !payload.password.trim()) {
        return {
          success: false,
          message: 'Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.',
          data: null as any,
          error: { code: 'INVALID_INPUT' },
        };
      }
      if (payload.username === 'be_an_da_co') {
        return {
          success: false,
          message: 'Tên đăng nhập này đã có người sử dụng. Con hãy thử tên khác nhé!',
          data: null as any,
          error: { code: 'USERNAME_ALREADY_EXISTS' },
        };
      }
      const mockUser: User = { user_id: Date.now(), username: payload.username.trim() };
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(mockUser));
      return {
        success: true,
        message: 'Tạo tài khoản thành công! Chào mừng con đến với LearnMate AI.',
        data: mockUser,
      };
    }

    const res = await apiRequest<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    if (res.success && res.data) {
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(res.data));
    }
    return res;
  },

  // Đăng nhập
  async login(payload: LoginPayload): Promise<ApiResponse<User>> {
    if (CONFIG.USE_MOCK) {
      await new Promise((r) => setTimeout(r, 300));
      if (!payload.username.trim() || !payload.password.trim()) {
        return {
          success: false,
          message: 'Tên đăng nhập và mật khẩu không được để trống.',
          data: null as any,
          error: { code: 'INVALID_INPUT' },
        };
      }
      const mockUser: User = { user_id: 1, username: payload.username.trim() };
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(mockUser));
      return {
        success: true,
        message: 'Đăng nhập thành công! Hãy chọn bé để bắt đầu học nhé.',
        data: mockUser,
      };
    }

    const res = await apiRequest<User>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    if (res.success && res.data) {
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(res.data));
    }
    return res;
  },
};
