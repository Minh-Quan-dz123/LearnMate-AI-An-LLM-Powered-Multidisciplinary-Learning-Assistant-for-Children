
/**
 * Giọng kể Module 3:
 * - Mặc định ưu tiên Gemini TTS qua Backend, dùng URL đã cache khi có.
 * - Có thể chuyển ngay sang Web Speech API, kể cả khi request Gemini đang chờ.
 * - Khi Gemini lỗi/quota hết, tự chuyển sang giọng trình duyệt.
 * - Nếu có voiceMode/onSwitchToBrowser từ DetectivePage, lựa chọn dùng chung
 *   cho cả ván; V2 không truyền props vẫn hoạt động độc lập.
 *
 * Chú ý: AbortController chỉ hủy việc chờ response phía FE.
 * BE/nhà cung cấp có thể vẫn tiếp tục xử lý request đã nhận.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { Pause, Play, RotateCcw, Volume2, RefreshCw } from 'lucide-react';
import { detectiveService } from '../../services/detectiveService';
import type { DetectiveNarrationSegment } from '../../types/detective';
import './DetectiveAudioPlayer.css';

export type DetectiveNarrationVoice = 'gemini' | 'browser';

interface Props {
  caseId: string;
  childId: number;
  segmentType: DetectiveNarrationSegment;
  segmentId?: string | null;
  label?: string;
  text: string;
  autoPlayOnStart?: boolean;
  stopSignal?: number;
  showCaption?: boolean;
  /** Truyền từ DetectivePage để các phần kể chuyện/nhận xét dùng chung một giọng. */
  voiceMode?: DetectiveNarrationVoice;
  onSwitchToBrowser?: () => void;
}

const supportsBrowserSpeech = () =>
  typeof window !== 'undefined' &&
  'speechSynthesis' in window &&
  typeof SpeechSynthesisUtterance !== 'undefined';

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
  voiceMode,
  onSwitchToBrowser,
}: Props) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const srcRef = useRef('');
  const requestVersion = useRef(0);
  const abortRef = useRef<AbortController | null>(null);
  const speechRef = useRef<SpeechSynthesisUtterance | null>(null);
  const speedRef = useRef(1);
  const busy = useRef(false);
  const switchedHere = useRef(false);
  const previousMode = useRef<DetectiveNarrationVoice | null>(null);
  const autoStartedRef = useRef(false);

  // Chế độ local dành cho các component V2 không dùng state cấp trang.
  const [localBrowser, setLocalBrowser] = useState(false);
  const mode: DetectiveNarrationVoice =
    voiceMode ?? (localBrowser ? 'browser' : 'gemini');
  const modeRef = useRef<DetectiveNarrationVoice>(mode);
  modeRef.current = mode;

  const [url, setUrl] = useState('');
  const [playing, setPlaying] = useState(false);
  const [paused, setPaused] = useState(false);
  const [loading, setLoading] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const browserSupported = supportsBrowserSpeech();

  /** Hủy request FE và dừng cả 2 cơ chế phát, không làm mất URL cache. */
  const stopCurrent = useCallback((updateState = true, cancelBrowserSpeech = true) => {
    requestVersion.current += 1;
    busy.current = false;
    abortRef.current?.abort();
    abortRef.current = null;
    audioRef.current?.pause();

    if (speechRef.current) {
      speechRef.current = null;
      // Hint có thể đã bắt đầu đọc ngay trước khi stopSignal được commit.
      // Khi đó KHÔNG cancel toàn cục: sẽ vô tình tắt cả giọng của hint.
      if (cancelBrowserSpeech && supportsBrowserSpeech()) {
        window.speechSynthesis.cancel();
      }
    }

    if (updateState) {
      setPlaying(false);
      setPaused(false);
      setLoading(false);
    }
  }, []);

  /** Đọc ngay bằng trình duyệt, không gửi API. */
  const speakBrowser = useCallback(() => {
    if (!supportsBrowserSpeech()) {
      setError('Trình duyệt này không hỗ trợ giọng đọc. Con vẫn có thể đọc nội dung bên dưới.');
      return;
    }
    if (!text.trim()) return;

    // Web Speech là API toàn trình duyệt, hủy giọng cũ trước khi đọc đoạn mới.
    window.speechSynthesis.cancel();
    const speech = new SpeechSynthesisUtterance(text);
    speech.lang = 'vi-VN';
    speech.rate = speedRef.current;
    speech.pitch = 1.03;
    const vietnameseVoice = window.speechSynthesis.getVoices()
      .find((voice) => voice.lang.toLowerCase().startsWith('vi'));
    if (vietnameseVoice) speech.voice = vietnameseVoice;

    speechRef.current = speech;
    speech.onstart = () => {
      if (speechRef.current === speech) {
        setPlaying(true);
        setPaused(false);
      }
    };
    speech.onend = () => {
      if (speechRef.current === speech) {
        speechRef.current = null;
        setPlaying(false);
        setPaused(false);
      }
    };
    speech.onerror = (event) => {
      if (speechRef.current !== speech) return;
      speechRef.current = null;
      setPlaying(false);
      setPaused(false);
      if (event.error !== 'canceled' && event.error !== 'interrupted') {
        setError('Chưa đọc được bằng giọng trình duyệt. Con hãy bấm Nghe lại nhé!');
      }
    };

    setError('');
    setPlaying(true);
    setPaused(false);
    window.speechSynthesis.speak(speech);
  }, [text]);

  /** Bấm nút hoặc Gemini hết quota: chỉ đổi sang browser cho ván hiện tại. */
  const switchToBrowser = useCallback((message = '') => {
    stopCurrent(); // Hủy request đang chờ và ngăn audio Gemini phát muộn.
    modeRef.current = 'browser'; // Có hiệu lực ngay, không chờ React render.
    switchedHere.current = true;
    if (voiceMode === undefined) {
      setLocalBrowser(true);
    }
    onSwitchToBrowser?.();
    setNotice(message);
    if (supportsBrowserSpeech()) {
      speakBrowser();
    } else {
      setError('Trình duyệt chưa hỗ trợ đọc thành tiếng. Nội dung vẫn có trên màn hình.');
    }
  }, [onSwitchToBrowser, speakBrowser, stopCurrent, voiceMode]);

  const play = useCallback(async () => {
    if (modeRef.current === 'browser') {
      if (paused && supportsBrowserSpeech() && window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
        setPaused(false);
        setPlaying(true);
      } else {
        speakBrowser();
      }
      return;
    }
    const audio = audioRef.current;
    if (!audio || busy.current) return;

    // Nếu đã có URL và audio đang tạm dừng thì tiếp tục phát.
    if (srcRef.current && audio.src) {
      const version = requestVersion.current;
      try {
        audio.playbackRate = speedRef.current;
        await audio.play();
        if (version === requestVersion.current && modeRef.current === 'gemini') {
          setPlaying(true);
        }
      } catch (exc) {
        if (version !== requestVersion.current || modeRef.current !== 'gemini') return;
        if (exc instanceof DOMException && exc.name === 'NotAllowedError') {
          setError('Trình duyệt chặn phát tự động. Con hãy bấm nút nghe nhé!');
        } else {
          switchToBrowser('Giọng Gemini tạm thời không phát được. Đã chuyển sang giọng trình duyệt.');
        }
      }
      return;
    }

    const version = ++requestVersion.current;
    const controller = new AbortController();
    abortRef.current = controller;
    busy.current = true;
    setLoading(true);
    setError('');
    try {
      const response = await detectiveService.getNarration(
        caseId, childId, segmentType, segmentId, controller.signal
      );
      // Bỏ hoàn toàn kết quả request cũ sau khi đổi giọng hoặc chuyển màn.
      if (version !== requestVersion.current || modeRef.current !== 'gemini') return;
      if (!response.success || !response.data?.audio_url) {
        throw new Error(response.message || 'Gemini TTS không khả dụng');
      }
      srcRef.current = response.data.audio_url;
      audio.src = srcRef.current;
      setUrl(srcRef.current);
      audio.playbackRate = speedRef.current;
      await audio.play();
      if (version === requestVersion.current && modeRef.current === 'gemini') {
        setPlaying(true);
      }
    } catch (exc) {
      if (version !== requestVersion.current || modeRef.current !== 'gemini') return;
      if (exc instanceof DOMException && exc.name === 'NotAllowedError') {
        setError('Trình duyệt chặn phát tự động. Con hãy bấm nút nghe nhé!');
      } else {
        switchToBrowser('Gemini TTS đang bận hoặc hết hạn mức. Đã dùng giọng trình duyệt cho ván này.');
      }
    } finally {
      if (version === requestVersion.current) {
        busy.current = false;
        abortRef.current = null;
        setLoading(false);
      }
    }
  }, [caseId, childId, segmentType, segmentId, paused, speakBrowser, switchToBrowser]);

  // Reset khi chuyển vụ án/đoạn kể. Không reset trạng thái chung trong DetectivePage.
  useEffect(() => {
    autoStartedRef.current = false;
    stopCurrent();
    srcRef.current = '';
    audioRef.current?.removeAttribute('src');
    setUrl('');
    setError('');
    setNotice('');
    setLocalBrowser(false);
    return () => {
      autoStartedRef.current = false;
      stopCurrent(false);
    };
  }, [caseId, segmentType, segmentId, stopCurrent]);

  // Khi bấm hint, hook hint đã gọi speechSynthesis.cancel() rồi đọc hint.
  // Không được cancel Web Speech lần nữa trong effect này, kẻo tắt luôn hint mới.
  // Request Gemini vẫn bị abort và kết quả chậm vẫn bị bỏ qua.
  useEffect(() => {
    stopCurrent(true, false);
  }, [stopSignal, stopCurrent]);

  // Nếu đoạn khác trong ván đã chuyển giọng, dừng audio của đoạn này.
  useEffect(() => {
    if (mode === 'browser' && previousMode.current !== 'browser') {
      if (!switchedHere.current) stopCurrent();
      switchedHere.current = false;
    }
    previousMode.current = mode;
  }, [mode, stopCurrent]);

  // Khóa auto-start: thay đổi loading/paused/voiceMode không được phát lại đoạn cũ.
  // Vẫn hoạt động với React StrictMode vì effect reset ở trên dọn cờ khi remount.
  useEffect(() => {
    if (autoPlayOnStart && !autoStartedRef.current) {
      autoStartedRef.current = true;
      void play();
    }
    if (!autoPlayOnStart) autoStartedRef.current = false;
  }, [autoPlayOnStart, play]);

  function pause() {
    if (modeRef.current === 'browser') {
      if (supportsBrowserSpeech()) window.speechSynthesis.pause();
      setPaused(true);
    } else {
      audioRef.current?.pause();
    }
    setPlaying(false);
  }

  function replay() {
    if (modeRef.current === 'browser') {
      speakBrowser();
    } else {
      const audio = audioRef.current;
      if (audio) audio.currentTime = 0;
      void play();
    }
  }

  function changeSpeed(value: number) {
    speedRef.current = value;
    setSpeed(value);
    if (audioRef.current) audioRef.current.playbackRate = value;
    // Với Web Speech, tốc độ có hiệu lực từ lượt đọc tiếp theo.
  }

  return (
    <section className="lm3-audio" aria-label="Cô giáo kể chuyện">
      <audio
        ref={audioRef}
        preload="none"
        onEnded={() => setPlaying(false)}
        onPause={() => {
          if (modeRef.current === 'gemini') setPlaying(false);
        }}
        onError={() => {
          if (modeRef.current === 'gemini' && srcRef.current) {
            switchToBrowser('Không tải được âm thanh Gemini. Đã chuyển sang giọng trình duyệt.');
          }
        }}
      />

      <div className="lm3-audio-toolbar">
        <span className="lm3-audio-title">
          <Volume2 size={17} />
          Cô giáo kể chuyện
        </span>

        <button
          type="button"
          disabled={loading && mode === 'gemini'}
          onClick={() => playing ? pause() : void play()}
        >
          {playing ? <Pause size={17} /> : <Play size={17} />}
          {loading && mode === 'gemini'
            ? 'Đang tải giọng Gemini...'
            : playing ? 'Tạm dừng' : mode === 'browser' ? 'Nghe giọng trình duyệt' : label}
        </button>

        <button
          type="button"
          disabled={mode === 'gemini' ? !url || loading : !browserSupported}
          onClick={replay}
          aria-label="Nghe lại từ đầu"
        >
          <RotateCcw size={17} />
          Nghe lại
        </button>

        <label>
          Tốc độ
          <select value={speed} onChange={(e) => changeSpeed(Number(e.target.value))}>
            <option value={0.85}>0.85×</option>
            <option value={1}>1×</option>
            <option value={1.25}>1.25×</option>
          </select>
        </label>

        {mode === 'gemini' ? (
          <button
            type="button"
            className="lm3-audio-switch"
            onClick={() => switchToBrowser('Đã chuyển sang giọng trình duyệt cho ván này.')}
            disabled={!browserSupported}
            title="Chuyển ngay, không cần đợi Gemini TTS tải xong"
          >
            <RefreshCw size={16} />
            Dùng giọng trình duyệt
          </button>
        ) : (
          <span className="lm3-audio-mode" role="status">
            Giọng trình duyệt · ván này
          </span>
        )}
      </div>

      {(showCaption || (mode === 'browser' && !browserSupported)) && (
        <p className="lm3-audio-caption">{text}</p>
      )}
      {notice && <p className="lm3-audio-notice" role="status">{notice}</p>}
      {error && <p className="lm3-audio-error" role="status">{error}</p>}
    </section>
  );
}
