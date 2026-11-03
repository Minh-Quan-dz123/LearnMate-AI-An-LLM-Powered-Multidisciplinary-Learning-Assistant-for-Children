
import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';

import {
  Pause,
  Play,
  RotateCcw,
  Volume2,
} from 'lucide-react';

import { detectiveService } from '../../services/detectiveService';

import type {
  DetectiveNarrationSegment,
} from '../../types/detective';

import './DetectiveAudioPlayer.css';

interface Props {
  caseId: string;
  childId: number;

  segmentType: DetectiveNarrationSegment;
  segmentId?: string | null;

  label?: string;
  text: string;

  // Tự phát khi component xuất hiện.
  autoPlayOnStart?: boolean;

  // Tăng giá trị này để dừng giọng Gemini.
  stopSignal?: number;

  // Có hiển thị văn bản dưới nút nghe không?
  showCaption?: boolean;
}

export function DetectiveAudioPlayer({
  caseId,
  childId,
  segmentType,
  segmentId = null,
  label = 'Nghe cô giáo',
  text,
  autoPlayOnStart = false,
  stopSignal = 0,
  showCaption = true,
}: Props) {
  // ==========================================================
  // 1. REFS
  // ==========================================================

  const audioRef =
    useRef<HTMLAudioElement | null>(null);

  const srcRef = useRef('');

  const speedRef = useRef(1);

  const requestVersion = useRef(0);

  const busy = useRef(false);

  // ==========================================================
  // 2. STATES
  // ==========================================================

  const [url, setUrl] = useState('');

  const [playing, setPlaying] =
    useState(false);

  const [loading, setLoading] =
    useState(false);

  const [speed, setSpeed] =
    useState(1);

  const [error, setError] =
    useState('');

  // ==========================================================
  // 3. RESET KHI CHUYỂN VỤ ÁN / PHÂN ĐOẠN
  // ==========================================================

  useEffect(() => {
    requestVersion.current += 1;
    busy.current = false;
    srcRef.current = '';

    setUrl('');
    setPlaying(false);
    setLoading(false);
    setError('');

    const audio = audioRef.current;

    audio?.pause();
    audio?.removeAttribute('src');

    return () => {
      requestVersion.current += 1;

      audio?.pause();
      audio?.removeAttribute('src');
    };
  }, [
    caseId,
    segmentType,
    segmentId,
  ]);

  // ==========================================================
  // 4. PHÁT GEMINI TTS
  // ==========================================================

  const play = useCallback(async () => {
    const audio = audioRef.current;

    if (!audio || busy.current) {
      return;
    }

    const version = requestVersion.current;

    busy.current = true;

    setLoading(true);
    setError('');

    try {
      // ----------------------------------------------
      // Nếu chưa có URL âm thanh:
      // gọi BE lấy từ cache hoặc sinh Gemini TTS.
      // ----------------------------------------------

      if (!srcRef.current) {
        const response =
          await detectiveService.getNarration(
            caseId,
            childId,
            segmentType,
            segmentId
          );

        // Nếu đã đổi vụ án hoặc dừng yêu cầu:
        // bỏ kết quả cũ.
        if (
          version !== requestVersion.current
        ) {
          return;
        }

        if (
          !response.success ||
          !response.data?.audio_url
        ) {
          throw new Error(
            response.message ||
            'Không tải được giọng kể.'
          );
        }

        srcRef.current =
          response.data.audio_url;

        audio.src = srcRef.current;

        setUrl(srcRef.current);
      }

      audio.playbackRate = speedRef.current;

      // ----------------------------------------------
      // Phát WAV của Gemini.
      //
      // Trình duyệt có thể chặn autoplay.
      // Khi đó vẫn giữ nút phát thủ công.
      // ----------------------------------------------

      await audio.play();

      if (
        version === requestVersion.current
      ) {
        setPlaying(true);
      }

    } catch (exc) {
      if (
        version !== requestVersion.current
      ) {
        return;
      }

      if (
        exc instanceof DOMException &&
        exc.name === 'NotAllowedError'
      ) {
        setError(
          'Trình duyệt chặn phát tự động. ' +
          'Con hãy bấm nút nghe cô giáo nhé!'
        );
      } else {
        setError(
          'Chưa phát được giọng cô giáo. ' +
          'Con có thể thử lại nhé!'
        );
      }

    } finally {
      if (
        version === requestVersion.current
      ) {
        busy.current = false;
        setLoading(false);
      }
    }

  }, [
    caseId,
    childId,
    segmentType,
    segmentId,
  ]);

  // ==========================================================
  // 5. DỪNG GEMINI KHI CẦN
  // ==========================================================

  useEffect(() => {
    // Bỏ hiệu lực request TTS đang chờ.
    requestVersion.current += 1;

    busy.current = false;

    audioRef.current?.pause();

    setPlaying(false);
    setLoading(false);

  }, [stopSignal]);

  // ==========================================================
  // 6. TỰ ĐỘNG PHÁT
  //
  // Hoạt động cho:
  // - introduction
  // - retry_feedback
  // - final_explanation
  // ==========================================================

  useEffect(() => {
    if (autoPlayOnStart) {
      void play();
    }
  }, [
    autoPlayOnStart,
    play,
  ]);

  // ==========================================================
  // 7. TẠM DỪNG
  // ==========================================================

  function pause() {
    audioRef.current?.pause();
    setPlaying(false);
  }

  // ==========================================================
  // 8. NGHE LẠI
  // ==========================================================

  function replay() {
    const audio = audioRef.current;

    if (!audio) return;

    audio.currentTime = 0;

    void play();
  }

  // ==========================================================
  // 9. ĐỔI TỐC ĐỘ ĐỌC
  // ==========================================================

  function changeSpeed(value: number) {
    speedRef.current = value;

    setSpeed(value);

    if (audioRef.current) {
      audioRef.current.playbackRate = value;
    }
  }

  // ==========================================================
  // 10. RENDER
  // ==========================================================

  return (
    <section
      className="lm3-audio"
      aria-label="Cô giáo kể chuyện"
    >
      <audio
        ref={audioRef}
        preload="none"

        onEnded={() =>
          setPlaying(false)
        }

        onPause={() =>
          setPlaying(false)
        }

        onError={() =>
          setError(
            'Không tải được âm thanh. ' +
            'Con có thể bấm nghe lại.'
          )
        }
      />

      <div className="lm3-audio-toolbar">

        <span className="lm3-audio-title">
          <Volume2 size={17} />
          Cô giáo kể chuyện
        </span>

        {/* NÚT PHÁT / TẠM DỪNG */}

        <button
          type="button"
          disabled={loading}
          onClick={() =>
            playing
              ? pause()
              : void play()
          }
        >
          {playing ? (
            <Pause size={17} />
          ) : (
            <Play size={17} />
          )}

          {loading
            ? 'Đang chuẩn bị...'
            : playing
              ? 'Tạm dừng'
              : label}
        </button>

        {/* NÚT NGHE LẠI */}

        <button
          type="button"
          disabled={!url || loading}
          onClick={replay}
          aria-label="Nghe lại từ đầu"
        >
          <RotateCcw size={17} />
          Nghe lại
        </button>

        {/* TỐC ĐỘ ĐỌC */}

        <label>
          Tốc độ

          <select
            value={speed}
            onChange={(event) =>
              changeSpeed(
                Number(event.target.value)
              )
            }
          >
            <option value={0.85}>
              0.85×
            </option>

            <option value={1}>
              1×
            </option>

            <option value={1.25}>
              1.25×
            </option>
          </select>
        </label>

      </div>

      {/* Văn bản minh họa, có thể ẩn ở V3. */}

      {showCaption && (
        <p className="lm3-audio-caption">
          {text}
        </p>
      )}

      {/* Lỗi âm thanh hoặc autoplay. */}

      {error && (
        <p
          className="lm3-audio-error"
          role="status"
        >
          {error}
        </p>
      )}

    </section>
  );
}
