
import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';

/**
 * Hook đọc gợi ý bằng Web Speech API.
 *
 * Không gọi Gemini TTS.
 *
 * Chức năng:
 * - Đọc tiếng Việt.
 * - Hủy giọng cũ khi đọc gợi ý mới.
 * - Nghe lại.
 * - Dừng đọc.
 * - Dọn audio khi component unmount.
 */
export function useDetectiveHintSpeech() {

  const utterance =
    useRef<SpeechSynthesisUtterance | null>(null);

  const [speaking, setSpeaking] =
    useState(false);

  /**
   * Kiểm tra trình duyệt có hỗ trợ đọc không.
   */
  const supported =
    typeof window !== 'undefined' &&
    'speechSynthesis' in window &&
    'SpeechSynthesisUtterance' in window;

  /**
   * Dừng giọng đang phát.
   */
  const stop = useCallback(() => {
    if (supported) {
      window.speechSynthesis.cancel();
    }

    utterance.current = null;
    setSpeaking(false);
  }, [supported]);

  /**
   * Đọc nội dung.
   *
   * Tìm giọng tiếng Việt nếu có.
   */
  const speak = useCallback(
    (text: string) => {

      if (!supported || !text.trim()) {
        return;
      }

      // Không cho hai giọng chồng lên nhau.
      window.speechSynthesis.cancel();

      const speech =
        new SpeechSynthesisUtterance(text);

      speech.lang = 'vi-VN';
      speech.rate = 0.94;
      speech.pitch = 1.04;

      const voices =
        window.speechSynthesis.getVoices();

      const vietnameseVoice =
        voices.find((voice) =>
          voice.lang.toLowerCase().startsWith('vi')
        );

      if (vietnameseVoice) {
        speech.voice = vietnameseVoice;
      }

      speech.onstart = () => {
        setSpeaking(true);
      };

      speech.onend = () => {
        setSpeaking(false);
      };

      speech.onerror = () => {
        setSpeaking(false);
      };

      utterance.current = speech;

      window.speechSynthesis.speak(speech);

    },
    [supported]
  );

  /**
   * Hủy giọng đọc khi rời màn hình.
   */
  useEffect(() => {
    return () => {
      if (supported) {
        window.speechSynthesis.cancel();
      }
    };
  }, [supported]);

  return {
    supported,
    speaking,
    speak,
    stop,
  };
}
