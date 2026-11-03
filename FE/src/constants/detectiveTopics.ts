
/**
 * Danh sách chủ đề của Module 3.
 * `id` PHẢI trùng với TOPIC_NAMES của BE/app/schemas/detective.py.
 * Chỉ lưu thông tin hiển thị; độ tuổi, sở thích được BE đọc từ hồ sơ bé.
 */
export const DETECTIVE_TOPICS = [
  { id: 'random', name: 'Ngẫu nhiên', description: 'Để AI chọn một bí ẩn bất ngờ!', emoji: '🎲', color: '#845EF7' },
  { id: 'plants', name: 'Thực vật kỳ thú', description: 'Khám phá bí mật của cây cối.', emoji: '🌱', color: '#2F9E44' },
  { id: 'animals', name: 'Thế giới động vật', description: 'Đi tìm dấu vết của muôn loài.', emoji: '🦊', color: '#F08C00' },
  { id: 'environment', name: 'Môi trường xanh', description: 'Giải mã câu chuyện về Trái Đất.', emoji: '🌳', color: '#0CA678' },
  { id: 'weather', name: 'Bí ẩn thời tiết', description: 'Lần theo mây, mưa và gió.', emoji: '🌦️', color: '#228BE6' },
  { id: 'physics', name: 'Vật lý quanh ta', description: 'Ánh sáng, âm thanh và chuyển động.', emoji: '💡', color: '#E67700' },
  { id: 'water', name: 'Nước và vật chất', description: 'Điều gì nổi, chìm hay tan trong nước?', emoji: '💧', color: '#1098AD' },
  { id: 'space', name: 'Khám phá vũ trụ', description: 'Những điều kỳ lạ trên bầu trời.', emoji: '🪐', color: '#7048E8' },
] as const;

/** Bao gồm `random` vì BE chấp nhận topic_id="random". */
export type DetectiveTopicId = (typeof DETECTIVE_TOPICS)[number]['id'];
