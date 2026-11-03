
-- Chạy MỘT LẦN trong Supabase SQL Editor, project đang có child_profiles.
-- Lưu vụ án kèm lời giải ở BE, không gửi case_data trực tiếp về FE.

CREATE TABLE IF NOT EXISTS public.detective_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_id BIGINT NOT NULL REFERENCES public.child_profiles(id) ON DELETE CASCADE,
    topic_id TEXT NOT NULL,
    title TEXT NOT NULL,
    case_data JSONB NOT NULL,
    image_path TEXT,
    play_state JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_completed_at TIMESTAMPTZ
);

-- Tối ưu lấy 5 vụ mới nhất (kể cả chưa chơi xong).
CREATE INDEX IF NOT EXISTS idx_detective_recent
ON public.detective_cases (child_id, created_at DESC);

-- Tối ưu danh sách 5 vụ ĐÃ HOÀN THÀNH.
CREATE INDEX IF NOT EXISTS idx_detective_completed
ON public.detective_cases (child_id, last_completed_at DESC)
WHERE last_completed_at IS NOT NULL;

-- Tạo bucket công khai để FE tải ảnh nền.
-- Dùng key có quyền ghi Storage ở BE; KHÔNG lộ key trên FE.
INSERT INTO storage.buckets (id, name, public)
VALUES ('detective-backgrounds', 'detective-backgrounds', true)
ON CONFLICT (id) DO UPDATE SET public = true;

-- Nếu RLS được bật, backend cần dùng server-side key có quyền đọc/ghi
-- bảng và Storage, chẳng hạn service_role key (chỉ lưu ở BE/.env).
