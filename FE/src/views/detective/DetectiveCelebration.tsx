
/**
 * Hiệu ứng ăn mừng khi phá án thành công V3.
 *
 * Không dùng thư viện bên ngoài.
 * Không ảnh hưởng màn chơi V2.
 */

import './DetectiveCelebration.css';

const EMOJIS = [
  '🎉',
  '🎊',
  '⭐',
  '✨',
  '🏆',
];

export function DetectiveCelebration() {
  return (
    <div
      className="lm3-v3-celebration"
      aria-hidden="true"
    >
      <div className="lm3-v3-celebration-icons">
        🏆 🎉 🌟 🎊
      </div>

      {Array.from(
        { length: 36 },
        (_, index) => (
          <span
            key={index}
            className="lm3-v3-confetti"
            style={{
              left:
                `${(index * 41 + 11) % 100}%`,

              animationDelay:
                `${(index % 12) * 0.09}s`,

              animationDuration:
                `${2.3 + (index % 5) * 0.24}s`,
            }}
          >
            {EMOJIS[index % EMOJIS.length]}
          </span>
        )
      )}
    </div>
  );
}
