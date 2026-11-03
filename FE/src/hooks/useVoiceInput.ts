
import { useCallback, useEffect, useRef, useState } from 'react';

// Khai báo kiểu cho Web Speech API.
// Không cần cài thêm thư viện Speech-to-Text.
interface SpeechResult {
  isFinal: boolean;
  [index: number]: { transcript: string };
}

interface SpeechEvent {
  results: {
    length: number;
    [index: number]: SpeechResult;
  };
}

interface SpeechError {
  error: string;
}

interface Recognition {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: SpeechEvent) => void) | null;
  onerror: ((event: SpeechError) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

type RecognitionConstructor = new () => Recognition;

function getSpeechRecognition(): RecognitionConstructor | undefined {
  if (typeof window === 'undefined') return undefined;

  const browser = window as Window & {
    SpeechRecognition?: RecognitionConstructor;
    webkitSpeechRecognition?: RecognitionConstructor;
  };

  return browser.SpeechRecognition ?? browser.webkitSpeechRecognition;
}

export function useVoiceInput(
  onText: (questionId: string, value: string) => void
) {
  const recognitionRef = useRef<Recognition | null>(null);
  const onTextRef = useRef(onText);

  const [listening, setListening] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [interim, setInterim] = useState('');
  const [error, setError] = useState('');

  const supported = Boolean(getSpeechRecognition());

  useEffect(() => {
    onTextRef.current = onText;
  }, [onText]);

  // Hủy hẳn phiên ghi âm đang chạy.
  const abort = useCallback(() => {
    const current = recognitionRef.current;
    recognitionRef.current = null;

    if (current) {
      current.onresult = null;
      current.onerror = null;
      current.onend = null;
      current.abort();
    }

    setListening(false);
    setStopping(false);
    setInterim('');
  }, []);

  /**
   * start():
   * - questionId: câu đang làm.
   * - existingText: nội dung đã nhập trước đó.
   * - reset = true: xóa nội dung và nói lại từ đầu.
   * - reset = false: nối lời nói mới vào nội dung cũ.
   */
  const start = useCallback((
    questionId: string,
    existingText: string,
    reset = false
  ) => {
    const SpeechRecognition = getSpeechRecognition();

    if (!SpeechRecognition) {
      setError('Trình duyệt không hỗ trợ nhận diện giọng nói.');
      return;
    }

    abort();
    setError('');

    const previousText = reset ? '' : existingText.trim();

    if (reset) {
      onTextRef.current(questionId, '');
    }

    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;

    // Nhận diện tiếng Việt.
    recognition.lang = 'vi-VN';

    // Cho phép nói nhiều câu liên tiếp.
    recognition.continuous = true;

    // Nhận cả kết quả tạm thời.
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      if (recognitionRef.current !== recognition) return;

      const finalParts: string[] = [];
      const interimParts: string[] = [];

      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        const transcript = result[0]?.transcript?.trim();

        if (!transcript) continue;

        if (result.isFinal) {
          finalParts.push(transcript);
        } else {
          interimParts.push(transcript);
        }
      }

      // Tính lại kết quả của cả phiên để tránh lặp chữ.
      if (finalParts.length > 0) {
        const text = [
          previousText,
          finalParts.join(' ')
        ]
          .filter(Boolean)
          .join(' ')
          .slice(0, 1000);

        onTextRef.current(questionId, text);
      }

      setInterim(interimParts.join(' '));
    };

    recognition.onerror = (event) => {
      if (recognitionRef.current !== recognition) return;

      const messages: Record<string, string> = {
        'not-allowed': 'Chưa được cấp quyền sử dụng micro.',
        'service-not-allowed': 'Dịch vụ nhận diện giọng nói bị chặn.',
        'no-speech': 'Chưa nghe rõ. Con hãy thử nói lại nhé!',
        'audio-capture': 'Không tìm thấy micro.',
        'network': 'Có lỗi kết nối dịch vụ nhận diện giọng nói.',
      };

      setError(
        messages[event.error] ?? 'Không nhận diện được lời nói.'
      );

      setListening(false);
      setStopping(false);
      setInterim('');
    };

    recognition.onend = () => {
      if (recognitionRef.current !== recognition) return;

      recognitionRef.current = null;
      setListening(false);
      setStopping(false);
      setInterim('');
    };

    try {
      recognition.start();
      setListening(true);
    } catch {
      recognitionRef.current = null;
      setListening(false);
      setError('Không khởi động được micro.');
    }
  }, [abort]);

  /**
   * Người dùng nhấn "Nói xong".
   * stop() vẫn cho phép trình duyệt trả về đoạn nói cuối.
   * Không dùng abort() ở đây vì có thể mất lời vừa nói.
   */
  const finish = useCallback(() => {
    if (!recognitionRef.current || stopping) return;

    setStopping(true);
    recognitionRef.current.stop();
  }, [stopping]);

  // Khi rời trang, hủy micro để không ghi vào câu khác.
  useEffect(() => {
    return () => {
      const current = recognitionRef.current;

      if (current) {
        current.onresult = null;
        current.onerror = null;
        current.onend = null;
        current.abort();
        recognitionRef.current = null;
      }
    };
  }, []);

  return {
    supported,
    listening,
    stopping,
    interim,
    error,
    start,
    finish,
    abort,
  };
}
