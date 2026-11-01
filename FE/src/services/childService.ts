import { CONFIG } from '../constants/config';
import { apiRequest } from './apiClient';
import type { ApiResponse } from '../types/api';
import type { ChildProfile, CreateChildPayload, UpdateChildPayload } from '../types/child';

const STORAGE_KEY_ACTIVE_CHILD = 'learnmate_active_child_id';
const STORAGE_KEY_MOCK_CHILDREN = 'learnmate_mock_children';

export const childService = {
  // Lấy ID bé đang học hiện tại
  getActiveChildId(): number | null {
    const raw = localStorage.getItem(STORAGE_KEY_ACTIVE_CHILD);
    return raw ? Number(raw) : null;
  },

  // Chọn bé để bắt đầu học
  setActiveChildId(childId: number): void {
    localStorage.setItem(STORAGE_KEY_ACTIVE_CHILD, String(childId));
  },

  // Lấy danh sách hồ sơ bé của user
  async getChildren(userId: number): Promise<ApiResponse<ChildProfile[]>> {
    if (CONFIG.USE_MOCK) {
      await new Promise((r) => setTimeout(r, 200));
      const raw = localStorage.getItem(STORAGE_KEY_MOCK_CHILDREN);
      let list: ChildProfile[] = raw ? JSON.parse(raw) : [];

      if (list.length === 0) {
        // Tạo sẵn dữ liệu mẫu cho lần đầu chạy
        list = [
          {
            child_id: 101,
            user_id: userId,
            name: 'Bé An',
            age: 7,
            gender: 'Nữ',
            interests: ['Động vật', 'Vẽ tranh', 'Âm nhạc'],
          },
          {
            child_id: 102,
            user_id: userId,
            name: 'Bé Bo',
            age: 9,
            gender: 'Nam',
            interests: ['Khoa học', 'Lego & Lắp ráp'],
          },
        ];
        localStorage.setItem(STORAGE_KEY_MOCK_CHILDREN, JSON.stringify(list));
      }

      return {
        success: true,
        message: 'Lấy danh sách hồ sơ trẻ thành công',
        data: list,
      };
    }

    return apiRequest<ChildProfile[]>(`/children?user_id=${userId}`, {
      method: 'GET',
    });
  },

  // Tạo hồ sơ mới
  async createChild(payload: CreateChildPayload): Promise<ApiResponse<ChildProfile>> {
    if (CONFIG.USE_MOCK) {
      await new Promise((r) => setTimeout(r, 300));
      const raw = localStorage.getItem(STORAGE_KEY_MOCK_CHILDREN);
      const list: ChildProfile[] = raw ? JSON.parse(raw) : [];

      const newChild: ChildProfile = {
        child_id: Date.now(),
        user_id: payload.user_id,
        name: payload.name.trim(),
        age: payload.age,
        gender: payload.gender || 'Không muốn cung cấp',
        interests: payload.interests || [],
        created_at: new Date().toISOString(),
      };

      list.push(newChild);
      localStorage.setItem(STORAGE_KEY_MOCK_CHILDREN, JSON.stringify(list));

      return {
        success: true,
        message: 'Tạo hồ sơ trẻ thành công',
        data: newChild,
      };
    }

    return apiRequest<ChildProfile>('/children', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Cập nhật hồ sơ
  async updateChild(payload: UpdateChildPayload): Promise<ApiResponse<ChildProfile>> {
    if (CONFIG.USE_MOCK) {
      await new Promise((r) => setTimeout(r, 300));
      const raw = localStorage.getItem(STORAGE_KEY_MOCK_CHILDREN);
      let list: ChildProfile[] = raw ? JSON.parse(raw) : [];

      list = list.map((c) =>
        c.child_id === payload.child_id
          ? {
              ...c,
              name: payload.name.trim(),
              age: payload.age,
              gender: payload.gender,
              interests: payload.interests || [],
              updated_at: new Date().toISOString(),
            }
          : c
      );
      localStorage.setItem(STORAGE_KEY_MOCK_CHILDREN, JSON.stringify(list));

      const updated = list.find((c) => c.child_id === payload.child_id)!;
      return {
        success: true,
        message: 'Cập nhật hồ sơ trẻ thành công',
        data: updated,
      };
    }

    return apiRequest<ChildProfile>(`/children/${payload.child_id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  // Xóa hồ sơ
  async deleteChild(childId: number, userId: number): Promise<ApiResponse<null>> {
    if (CONFIG.USE_MOCK) {
      await new Promise((r) => setTimeout(r, 300));
      const raw = localStorage.getItem(STORAGE_KEY_MOCK_CHILDREN);
      let list: ChildProfile[] = raw ? JSON.parse(raw) : [];

      list = list.filter((c) => c.child_id !== childId);
      localStorage.setItem(STORAGE_KEY_MOCK_CHILDREN, JSON.stringify(list));

      // Nếu đang chọn bé này thì reset
      if (this.getActiveChildId() === childId) {
        localStorage.removeItem(STORAGE_KEY_ACTIVE_CHILD);
      }

      return {
        success: true,
        message: 'Đã xóa hồ sơ trẻ',
        data: null,
      };
    }

    return apiRequest<null>(`/children/${childId}?user_id=${userId}`, {
      method: 'DELETE',
    });
  },
};
