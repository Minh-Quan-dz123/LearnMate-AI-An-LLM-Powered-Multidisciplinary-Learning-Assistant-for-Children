
let audioContext: AudioContext | null = null;

/**
 * Khởi tạo và kích hoạt AudioContext.
 * Nên gọi khi người dùng tương tác với giao diện.
 */
export function unlockCelebrationAudio(): void {
  if (typeof window === 'undefined') return;

  try {
    audioContext ??= new AudioContext();

    if (audioContext.state === 'suspended') {
      void audioContext.resume();
    }
  } catch (error) {
    console.warn('Không thể kích hoạt âm thanh:', error);
  }
}

/**
 * Phát âm thanh chúc mừng ngắn.
 */
export function playCelebrationSound(): void {
  unlockCelebrationAudio();

  const ctx = audioContext;
  if (!ctx || ctx.state !== 'running') return;

  const frequencies = [523.25, 659.25, 783.99, 1046.5];

  frequencies.forEach((frequency, index) => {
    const oscillator = ctx.createOscillator();
    const gain = ctx.createGain();

    const start = ctx.currentTime + index * 0.13;
    const end = start + 0.22;

    oscillator.type = 'sine';
    oscillator.frequency.value = frequency;

    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(0.15, start + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, end);

    oscillator.connect(gain);
    gain.connect(ctx.destination);

    oscillator.start(start);
    oscillator.stop(end);
  });
}
