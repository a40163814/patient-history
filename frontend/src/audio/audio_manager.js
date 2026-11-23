export class AudioManager {
  constructor() {
    this.synth = typeof window !== 'undefined' && 'speechSynthesis' in window ? window.speechSynthesis : null;
    this.recognition = null;
    this.wakeLock = null;
    this.speechRate = 1.0;
    this.isListening = false;
    this.activeUtterance = null;
    this.setupRecognition();
  }

  isSpeechSupported() {
    if (typeof window === 'undefined') return false;
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  setupRecognition() {
    if (typeof window === 'undefined') return;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 1;
      } catch (e) {
        console.warn('SpeechRecognition initialization error:', e);
      }
    }
  }

  async requestWakeLock() {
    if (typeof navigator !== 'undefined' && 'wakeLock' in navigator) {
      try {
        this.wakeLock = await navigator.wakeLock.request('screen');
      } catch (err) {
        console.warn('Wake Lock request skipped:', err);
      }
    }
  }

  releaseWakeLock() {
    if (this.wakeLock) {
      this.wakeLock.release().catch(() => {});
      this.wakeLock = null;
    }
  }

  speak(text, language = 'en', onEnd = null) {
    if (!this.synth) {
      if (onEnd) onEnd();
      return;
    }

    // Barge-in: cancel any active speech first
    this.synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    this.activeUtterance = utterance; // Prevent Chrome garbage collection bug
    utterance.rate = this.speechRate;
    
    // Select matching language voice if present
    if (language === 'hi') utterance.lang = 'hi-IN';
    else if (language === 'mr') utterance.lang = 'mr-IN';
    else utterance.lang = 'en-IN';

    let ended = false;
    const safeEnd = () => {
      if (!ended) {
        ended = true;
        this.activeUtterance = null;
        if (onEnd) onEnd();
      }
    };

    utterance.onend = () => {
      safeEnd();
    };

    utterance.onerror = (e) => {
      console.warn('Speech synthesis error or interrupt:', e);
      safeEnd();
    };

    // Chrome fallback timeout in case onend never fires
    const timeoutMs = Math.max(3000, Math.min(10000, (text.length / 15) * 1000));
    setTimeout(() => {
      if (!ended && this.synth && !this.synth.speaking) {
        safeEnd();
      }
    }, timeoutMs);

    this.synth.speak(utterance);
  }

  stopSpeaking() {
    if (this.synth) {
      this.synth.cancel();
      this.activeUtterance = null;
    }
  }

  startListening(language = 'en', onResult, onError, onFinal, onStatusChange) {
    if (!this.recognition) {
      this.setupRecognition();
    }

    if (!this.recognition) {
      const msg = 'Speech recognition requires HTTPS or localhost. Quick-tap options and typing are ready below.';
      if (onError) onError(msg);
      if (onStatusChange) onStatusChange('unsupported');
      return;
    }

    if (this.isListening) {
      try { this.recognition.stop(); } catch (e) {}
    }

    if (language === 'hi') this.recognition.lang = 'hi-IN';
    else if (language === 'mr') this.recognition.lang = 'mr-IN';
    else this.recognition.lang = 'en-IN';

    this.recognition.onresult = (event) => {
      let interim = '';
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interim += event.results[i][0].transcript;
        }
      }
      if (onResult) onResult(interim, finalTranscript);
      if (finalTranscript && onFinal) {
        onFinal(finalTranscript);
      }
    };

    this.recognition.onerror = (err) => {
      this.isListening = false;
      const errCode = err?.error || '';
      console.warn('Speech recognition event error:', errCode, err);

      let friendlyMsg = 'Microphone not available.';
      if (errCode === 'not-allowed') {
        friendlyMsg = 'Microphone permission denied. Please allow microphone access or tap quick chips below.';
      } else if (errCode === 'network' || errCode === 'service-not-allowed') {
        friendlyMsg = 'Speech service unavailable on HTTP. Use HTTPS or tap quick-reply options.';
      } else if (errCode === 'no-speech') {
        // Just silence, don't show angry alert
        if (onStatusChange) onStatusChange('ready');
        return;
      }

      if (onError) onError(friendlyMsg);
      if (onStatusChange) onStatusChange('error');
    };

    this.recognition.onend = () => {
      this.isListening = false;
      if (onStatusChange) onStatusChange('stopped');
    };

    try {
      this.recognition.start();
      this.isListening = true;
      if (onStatusChange) onStatusChange('listening');
    } catch (err) {
      if (err.name === 'InvalidStateError') {
        // Already active
        this.isListening = true;
        if (onStatusChange) onStatusChange('listening');
      } else {
        console.warn('Recognition start exception:', err);
        if (onError) onError('Could not start microphone. You can tap quick options below.');
        if (onStatusChange) onStatusChange('error');
      }
    }
  }

  stopListening() {
    if (this.recognition && this.isListening) {
      try {
        this.recognition.stop();
      } catch (e) {}
      this.isListening = false;
    }
  }
}

export const audioManager = new AudioManager();
