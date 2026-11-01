export const CONFIG = {
  // Vite proxy /api sang FastAPI localhost:8000
  API_BASE_URL: '/api',

  // false: gọi Backend thật
  // true: dùng mock nội bộ của FE (chỉ cho auth/children)
  USE_MOCK: false,
};
