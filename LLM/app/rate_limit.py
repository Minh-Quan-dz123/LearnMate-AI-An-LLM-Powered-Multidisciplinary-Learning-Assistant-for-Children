# ============================================================
# FILE: app/rate_limit.py
# PHỤ TRÁCH: Hoàng Tùng (Người 4)
#
# MỤC ĐÍCH:
# Giới hạn số request mỗi phút (sliding window, in-memory).
# Đủ đơn giản cho prototype; không cần Redis.
# ============================================================

import threading
import time
from collections import deque


class SlidingWindowRateLimiter:
    """Giới hạn số lượt gọi trong cửa sổ 60 giây.

    - Thread-safe (FastAPI chạy event loop + có thể có worker thread).
    - Không lưu thông tin định danh caller (prototype nội bộ).
    """

    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self.max_requests = max(0, max_requests)
        self.window_seconds = window_seconds
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    def check(self) -> bool:
        """Trả về True nếu request được phép, False nếu đã vượt giới hạn."""
        if self.max_requests <= 0:
            # 0 = không giới hạn.
            return True

        now = time.monotonic()
        with self._lock:
            while self._timestamps and now - self._timestamps[0] >= self.window_seconds:
                self._timestamps.popleft()

            if len(self._timestamps) >= self.max_requests:
                return False

            self._timestamps.append(now)
            return True
