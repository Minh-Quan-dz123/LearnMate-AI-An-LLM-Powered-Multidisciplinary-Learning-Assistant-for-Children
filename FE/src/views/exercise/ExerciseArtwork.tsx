
/**
 * FILE: ExerciseArtwork.tsx
 *
 * MỤC ĐÍCH:
 * - Quản lý hình minh họa môn học và chủ đề.
 * - Mặc định dùng SVG từ lucide-react.
 * - Có thể thay bằng ảnh local thông qua imageUrl.
 * - Nếu ảnh lỗi, tự hiển thị SVG dự phòng.
 */

import { useState, type CSSProperties } from 'react';

import {
  Atom,
  BadgeCheck,
  Compass,
  Earth,
  Footprints,
  GraduationCap,
  HandHeart,
  Handshake,
  Heart,
  House,
  Leaf,
  Lightbulb,
  MessageCircle,
  Microscope,
  PawPrint,
  Pencil,
  School,
  ShieldCheck,
  Shuffle,
  Smile,
  Sun,
  Trees,
  Users,
  Zap,
  type LucideIcon,
} from 'lucide-react';

import type { Subject } from '../../types/exercise';

// =====================================================
// 1. KIỂU DỮ LIỆU HÌNH MINH HỌA
// =====================================================

export interface Artwork {
  icon: LucideIcon;
  background: string;
  color: string;
  imageUrl?: string;
}

// =====================================================
// 2. HÌNH MINH HỌA MÔN HỌC
// =====================================================

export const SUBJECT_ART: Record<
  Subject,
  Artwork & { caption: string }
> = {
  'Khoa học tự nhiên': {
    icon: Microscope,
    background: '#dff6fd',
    color: '#137f96',
    caption: 'Khám phá thế giới',
  },

  'Đạo đức': {
    icon: HandHeart,
    background: '#ffe6ec',
    color: '#ce5375',
    caption: 'Học những điều tốt',
  },

  'Kỹ năng sống': {
    icon: Compass,
    background: '#efe7ff',
    color: '#7757bc',
    caption: 'Tự tin mỗi ngày',
  },
};

// =====================================================
// 3. HÌNH MINH HỌA TỪNG CHỦ ĐỀ
// =====================================================

// Tên phải khớp với SUBJECT_TOPICS trong subjects.ts.

const TOPIC_ICONS: Record<string, LucideIcon> = {
  // Khoa học tự nhiên
  'Động vật và thực vật': PawPrint,
  'Cơ thể người': Heart,
  'Môi trường và tài nguyên thiên nhiên': Trees,
  'Vật chất và năng lượng': Atom,
  'Trái Đất và bầu trời': Earth,

  // Đạo đức
  'Yêu thương gia đình': House,
  'Kính trọng thầy cô, lễ phép với người lớn': GraduationCap,
  'Đoàn kết, giúp đỡ bạn bè': Users,
  'Trung thực': BadgeCheck,
  'Chăm chỉ, có trách nhiệm': Sun,
  'Tuân thủ quy định nơi công cộng': Footprints,
  'Bảo vệ của công': School,

  // Kỹ năng sống
  'Kỹ năng giao tiếp': MessageCircle,
  'Kỹ năng quản lý cảm xúc': Smile,
  'Kỹ năng tự phục vụ': HandHeart,
  'Kỹ năng làm việc nhóm': Handshake,
  'Kỹ năng giải quyết vấn đề': Lightbulb,
  'Kỹ năng tự bảo vệ bản thân': ShieldCheck,
  'Kỹ năng xử lý tình huống nguy hiểm': Zap,
};

// =====================================================
// 4. MÀU NỀN CHỦ ĐỀ
// =====================================================

const PALETTE = [
  { background: '#e3f7e8', color: '#25865c' },
  { background: '#fff1d9', color: '#af6b21' },
  { background: '#e4f1ff', color: '#377cca' },
  { background: '#f0e7ff', color: '#7a55bd' },
  { background: '#ffe8ed', color: '#c54e72' },
];

// =====================================================
// 5. ẢNH LOCAL (TÙY CHỌN)
// =====================================================

/*
Ví dụ muốn thay SVG bằng ảnh WebP:

import animals from '../../assets/learning/animals.webp';

const TOPIC_IMAGES: Record<string, string> = {
  'Động vật và thực vật': animals,
};

Những chủ đề chưa có ảnh vẫn sử dụng SVG.
*/

const TOPIC_IMAGES: Record<string, string> = {};

// =====================================================
// 6. LẤY MINH HỌA CỦA CHỦ ĐỀ
// =====================================================

export function getTopicArt(
  name: string,
  index: number
): Artwork {
  return {
    icon: TOPIC_ICONS[name] ?? Leaf,
    ...PALETTE[index % PALETTE.length],
    imageUrl: TOPIC_IMAGES[name],
  };
}

// =====================================================
// 7. MINH HỌA CHỦ ĐỀ ĐẶC BIỆT
// =====================================================

export const RANDOM_ART: Artwork = {
  icon: Shuffle,
  background: '#fff4ce',
  color: '#ad7b1e',
};

export const CUSTOM_ART: Artwork = {
  icon: Pencil,
  background: '#ebe7ff',
  color: '#7757bc',
};

// =====================================================
// 8. COMPONENT HIỂN THỊ HÌNH
// =====================================================

export function ExerciseArtwork({
  art,
}: {
  art: Artwork;
}) {
  const [brokenUrl, setBrokenUrl] = useState<string | null>(null);

  const Icon = art.icon;

  const style = {
    '--setup-art-bg': art.background,
    '--setup-art-color': art.color,
  } as CSSProperties;

  return (
    <span
      className="setup-art"
      style={style}
      aria-hidden="true"
    >
      {art.imageUrl && brokenUrl !== art.imageUrl ? (
        <img
          src={art.imageUrl}
          alt=""
          loading="lazy"
          onError={() =>
            setBrokenUrl(art.imageUrl ?? null)
          }
        />
      ) : (
        <>
          <span className="setup-art-halo" />

          <span className="setup-art-sparkle">
            ✦
          </span>

          <Icon
            className="setup-art-symbol"
            strokeWidth={1.8}
          />
        </>
      )}
    </span>
  );
}
