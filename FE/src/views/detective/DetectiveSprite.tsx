
/**
 * FILE: src/views/detective/DetectiveSprite.tsx
 *
 * 9 sprite SVG tương ứng với ALLOWED_ASSETS trong BE.
 * Vẽ trực tiếp bằng JSX, không tải ảnh hoặc thêm thư viện.
 */
import type { ReactNode } from 'react';

interface Props {
  assetId: string;
}

export function DetectiveSprite({ assetId }: Props) {
  let picture: ReactNode;

  switch (assetId) {
    case 'wilted_plant':
      picture = <>
        <path d="M48 61V29M48 43Q30 42 25 25M48 52Q64 46 72 32" fill="none" stroke="#43864B" strokeWidth="5" strokeLinecap="round" />
        <path d="M25 25Q7 19 13 37Q25 50 35 38Q27 35 25 25Z" fill="#86C874" stroke="#43864B" strokeWidth="2.5" />
        <path d="M72 32Q88 23 85 42Q77 57 62 49Q72 41 72 32Z" fill="#A1D98B" stroke="#43864B" strokeWidth="2.5" />
        <path d="M48 30Q35 18 48 9Q62 18 48 30Z" fill="#66AF60" stroke="#43864B" strokeWidth="2.5" />
        <path d="M29 60H67L62 85Q48 91 34 85Z" fill="#E98C62" stroke="#A9513B" strokeWidth="3" />
        <path d="M26 58H70V66H26Z" fill="#F3A378" stroke="#A9513B" strokeWidth="3" strokeLinejoin="round" />
      </>;
      break;

    case 'dry_soil':
      picture = <>
        <path d="M8 60Q22 38 45 47Q67 36 88 60L82 81H13Z" fill="#AE7950" stroke="#785034" strokeWidth="3" strokeLinejoin="round" />
        <path d="M14 65Q25 56 37 63L44 55M52 62L63 68L73 60M43 77L49 70L57 75" fill="none" stroke="#69452E" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="25" cy="56" r="3" fill="#E8C6A0" />
        <circle cx="72" cy="72" r="3" fill="#E8C6A0" />
        <path d="M32 45L29 35M60 42L67 32" fill="none" stroke="#74A96B" strokeWidth="3" strokeLinecap="round" />
      </>;
      break;

    case 'watering_can':
      picture = <>
        <path d="M22 42H69L66 80Q46 90 25 79Z" fill="#72C7E8" stroke="#287FA9" strokeWidth="3" strokeLinejoin="round" />
        <path d="M30 43Q22 18 43 18Q62 18 61 43" fill="none" stroke="#287FA9" strokeWidth="6" strokeLinecap="round" />
        <path d="M67 50L86 38L91 47L69 66" fill="#8DD5EF" stroke="#287FA9" strokeWidth="3" strokeLinejoin="round" />
        <path d="M14 38L8 32M18 26L17 17" fill="none" stroke="#63BCE0" strokeWidth="4" strokeLinecap="round" />
        <path d="M31 59H56" stroke="#D8F6FF" strokeWidth="5" strokeLinecap="round" />
      </>;
      break;

    case 'notebook':
      picture = <>
        <rect x="23" y="12" width="56" height="72" rx="7" fill="#FFD56B" stroke="#C58B32" strokeWidth="3" />
        <rect x="18" y="12" width="15" height="72" rx="5" fill="#8E78CD" stroke="#6049A3" strokeWidth="3" />
        {[25, 40, 55, 70].map((y) => (
          <circle key={y} cx="25" cy={y} r="3" fill="#ECE5FF" />
        ))}
        <path d="M43 35H68M43 47H68M43 59H64" stroke="#B6803E" strokeWidth="4" strokeLinecap="round" />
        <path d="M63 18L68 23L57 29Z" fill="#FFF1AE" />
      </>;
      break;

    case 'water_tank':
      picture = <>
        <ellipse cx="48" cy="24" rx="28" ry="11" fill="#7AD0EF" stroke="#247CA7" strokeWidth="3" />
        <path d="M20 24V75Q48 91 76 75V24" fill="#57B7DE" stroke="#247CA7" strokeWidth="3" />
        <ellipse cx="48" cy="75" rx="28" ry="11" fill="#399BC9" stroke="#247CA7" strokeWidth="3" />
        <path d="M20 40Q48 54 76 40M20 58Q48 71 76 58" fill="none" stroke="#B6E7F5" strokeWidth="3" />
        <path d="M48 40Q39 52 41 58Q48 66 55 58Q57 52 48 40Z" fill="#E2FBFF" />
      </>;
      break;

    case 'lamp':
      picture = <>
        <path d="M30 43Q25 17 48 13Q72 17 66 43Q61 53 59 61H38Q37 53 30 43Z" fill="#FFDF77" stroke="#B77D35" strokeWidth="3" />
        <path d="M38 61H59V69H38ZM39 71H58V78Q48 85 39 78Z" fill="#8CB3D5" stroke="#526F98" strokeWidth="3" strokeLinejoin="round" />
        <path d="M42 59L38 44L47 50L56 44L53 59" fill="none" stroke="#DF9840" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M48 3V9M16 26L23 31M80 26L73 31M13 52H22M74 52H83" stroke="#FFBB39" strokeWidth="4" strokeLinecap="round" />
      </>;
      break;

    case 'thermometer':
      picture = <>
        <rect x="37" y="10" width="22" height="61" rx="11" fill="#F8FEFF" stroke="#6C8FB0" strokeWidth="3" />
        <circle cx="48" cy="74" r="16" fill="#FF776A" stroke="#C94F51" strokeWidth="3" />
        <path d="M48 29V74" stroke="#FF6A67" strokeWidth="8" strokeLinecap="round" />
        <path d="M63 28H71M63 40H68M63 52H71" stroke="#6C8FB0" strokeWidth="3" strokeLinecap="round" />
        <circle cx="44" cy="69" r="4" fill="#FFB0A0" />
      </>;
      break;

    case 'toy_robot':
      picture = <>
        <path d="M48 9V19" stroke="#5269A0" strokeWidth="4" strokeLinecap="round" />
        <circle cx="48" cy="8" r="5" fill="#FFC75F" />
        <rect x="19" y="20" width="58" height="47" rx="12" fill="#9BD6EB" stroke="#517FA8" strokeWidth="3" />
        <circle cx="36" cy="42" r="7" fill="#344E7C" />
        <circle cx="60" cy="42" r="7" fill="#344E7C" />
        <circle cx="38" cy="39" r="2.5" fill="white" />
        <circle cx="62" cy="39" r="2.5" fill="white" />
        <path d="M39 56Q48 63 57 56" fill="none" stroke="#344E7C" strokeWidth="3" strokeLinecap="round" />
        <path d="M19 44H10M77 44H86" stroke="#517FA8" strokeWidth="7" strokeLinecap="round" />
        <path d="M35 67V83M61 67V83" stroke="#517FA8" strokeWidth="8" strokeLinecap="round" />
      </>;
      break;

    case 'magnifier':
    default:
      picture = <>
        <circle cx="40" cy="38" r="25" fill="#DAF7FF" fillOpacity=".7" stroke="#457DB3" strokeWidth="8" />
        <path d="M59 57L82 81" stroke="#D19458" strokeWidth="13" strokeLinecap="round" />
        <path d="M23 29Q31 17 45 20" fill="none" stroke="white" strokeWidth="5" strokeLinecap="round" />
        <circle cx="40" cy="38" r="20" fill="none" stroke="#85D4E9" strokeWidth="2" />
      </>;
  }

  return (
    <svg
      viewBox="0 0 96 96"
      width="100%"
      height="100%"
      aria-hidden="true"
      focusable="false"
    >
      {picture}
    </svg>
  );
}
