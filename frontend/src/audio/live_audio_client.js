/**
 * Real-time WebSocket Client for Gemini Live API & Fallback Voice Adapters
 * Connects browser <-> FastAPI WebSocket (/ws/voice/{session_id})
 * Handles 16kHz upstream microphone PCM streaming and 24kHz queued downstream playback.
 */
function resampleTo16k(inputBuffer, inputSampleRate) {
  if (inputSampleRate === 16000) {
    const pcm16 = new Int16Array(inputBuffer.length);
    for (let i = 0; i < inputBuffer.length; i++) {
      const s = Math.max(-1, Math.min(1, inputBuffer[i]));
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return pcm16.buffer;
  }

  const ratio = inputSampleRate / 16000;
  const newLength = Math.round(inputBuffer.length / ratio);
  const pcm16 = new Int16Array(newLength);
  
  for (let i = 0; i < newLength; i++) {
    const origIndex = i * ratio;
    const index1 = Math.floor(origIndex);
    const index2 = Math.min(index1 + 1, inputBuffer.length - 1);
    const weight = origIndex - index1;
    const interpolated = inputBuffer[index1] * (1 - weight) + inputBuffer[index2] * weight;
    const s = Math.max(-1, Math.min(1, interpolated));
    pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }
  return pcm16.buffer;
}

export class LiveAudioClient {
  constructor() {
    this.ws = null;
    this.audioContext = null;
    this.captureContext = null;
    this.mediaStream = null;
    this.processor = null;
    this.isConnected = false;
    this.adapterType = null;
    this.nextPlayTime = 0;
    this.activeSources = [];
    this.isPlaying = false;

    this.onTranscript = null;
    this.onRedFlag = null;
    this.onLatency = null;
    this.onNotice = null;
    this.onError = null;
    this.onSpeechStart = null;
    this.onSpeechEnd = null;
    this.onLiveFallback = null;
  }

  ensureAudioContext() {
    try {
      if (!this.audioContext) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        this.audioContext = new AudioCtx({ sampleRate: 24000 });
      }
      if (this.audioContext.state === 'suspended') {
        this.audioContext.resume();
      }
    } catch (e) {
      console.warn('Could not resume AudioContext:', e);
    }
  }

  connect({
    sessionId,
    patientToken,
    language = 'en',
    onTranscript,
    onRedFlag,
    onLatency,
    onNotice,
    onError,
    onSpeechStart,
    onSpeechEnd,
    onLiveFallback
  }) {
    this.onTranscript = onTranscript;
    this.onRedFlag = onRedFlag;
    this.onLatency = onLatency;
    this.onNotice = onNotice;
    this.onError = onError;
    this.onSpeechStart = onSpeechStart;
    this.onSpeechEnd = onSpeechEnd;
    this.onLiveFallback = onLiveFallback;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/voice/${encodeURIComponent(sessionId)}`;

    try {
      this.ws = new WebSocket(wsUrl);
      this.ws.binaryType = 'arraybuffer';

      this.ws.onopen = () => {
        this.isConnected = true;
        // Send initial handshake
        this.ws.send(JSON.stringify({
          patient_token: patientToken,
          language: language
        }));
        if (this.pendingQuestion) {
          const q = this.pendingQuestion;
          this.pendingQuestion = null;
          this.askQuestion(q.prompt, q.language);
        }
      };

      this.ws.onmessage = async (event) => {
        if (typeof event.data === 'string') {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'ready') {
              this.adapterType = data.adapter;
              if (this.onNotice) {
                this.onNotice(`AI Voice Ready: ${data.adapter} (${data.language})`);
              }
            } else if (data.type === 'notice') {
              if (this.onNotice) this.onNotice(data.message);
            } else if (data.type === 'transcript') {
              if (this.onTranscript) this.onTranscript(data.speaker, data.text);
            } else if (data.type === 'red_flag_alert') {
              this.stopAudioPlayback();
              if (this.onRedFlag) this.onRedFlag(data.alert);
            } else if (data.type === 'latency') {
              if (this.onLatency) this.onLatency(data.turn_latency_ms);
            } else if (data.type === 'interrupted') {
              this.stopAudioPlayback();
            } else if (data.type === 'live_fallback') {
              if (this.onLiveFallback) this.onLiveFallback(data.prompt, data.language);
            }
          } catch (e) {
            console.warn('WebSocket message parse error:', e);
          }
        } else if (event.data instanceof ArrayBuffer) {
          // Play downstream 24kHz PCM audio chunk from Gemini Live
          this.playAudioChunk(event.data);
        }
      };

      this.ws.onerror = (err) => {
        console.warn('Live WebSocket error:', err);
        if (this.onError) this.onError(err);
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        this.stopAudioCapture();
        this.stopAudioPlayback();
      };
    } catch (err) {
      console.warn('Could not establish Live WebSocket:', err);
      if (this.onError) this.onError(err);
    }
  }

  askQuestion(prompt, language = 'en') {
    this.stopAudioPlayback();
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'ask_question',
        prompt: prompt,
        language: language
      }));
    } else if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
      this.pendingQuestion = { prompt, language };
    } else {
      if (this.onLiveFallback) this.onLiveFallback(prompt, language);
    }
  }

  playAudioChunk(arrayBuffer) {
    if (!arrayBuffer || arrayBuffer.byteLength === 0) return;

    try {
      this.ensureAudioContext();

      const int16Array = new Int16Array(arrayBuffer);
      const float32Array = new Float32Array(int16Array.length);
      for (let i = 0; i < int16Array.length; i++) {
        float32Array[i] = int16Array[i] / 32768.0;
      }

      const audioBuffer = this.audioContext.createBuffer(1, float32Array.length, 24000);
      audioBuffer.getChannelData(0).set(float32Array);

      const source = this.audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(this.audioContext.destination);

      const currentTime = this.audioContext.currentTime;
      const startTime = Math.max(currentTime, this.nextPlayTime || 0);
      source.start(startTime);
      this.nextPlayTime = startTime + audioBuffer.duration;
      this.activeSources.push(source);

      if (!this.isPlaying) {
        this.isPlaying = true;
        if (this.onSpeechStart) this.onSpeechStart();
      }

      source.onended = () => {
        const idx = this.activeSources.indexOf(source);
        if (idx > -1) this.activeSources.splice(idx, 1);
        if (this.activeSources.length === 0) {
          this.isPlaying = false;
          if (this.onSpeechEnd) this.onSpeechEnd();
        }
      };
    } catch (err) {
      console.warn('Error playing audio chunk:', err);
    }
  }

  stopAudioPlayback() {
    this.nextPlayTime = 0;
    this.isPlaying = false;
    this.activeSources.forEach((src) => {
      try { src.stop(); } catch (e) {}
    });
    this.activeSources = [];
  }

  async startAudioCapture() {
    if (!navigator.mediaDevices?.getUserMedia) {
      return false;
    }

    try {
      this.stopAudioCapture();

      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        }
      });

      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.captureContext = new AudioCtx();
      const source = this.captureContext.createMediaStreamSource(this.mediaStream);

      // 2048 buffer size gives ~42ms audio frames for near-instant latency
      this.processor = this.captureContext.createScriptProcessor(2048, 1, 1);
      this.processor.onaudioprocess = (e) => {
        if (!this.isConnected || !this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        
        const floatSamples = e.inputBuffer.getChannelData(0);
        const actualRate = this.captureContext.sampleRate || 48000;
        const pcmBuffer = resampleTo16k(floatSamples, actualRate);
        this.ws.send(pcmBuffer);
      };

      // Connect to a 0-gain node before destination to prevent hearing oneself through speakers
      const silenceGain = this.captureContext.createGain();
      silenceGain.gain.value = 0.0;

      source.connect(this.processor);
      this.processor.connect(silenceGain);
      silenceGain.connect(this.captureContext.destination);
      return true;
    } catch (err) {
      console.warn('Audio capture setup failed:', err);
      return false;
    }
  }

  stopAudioCapture() {
    if (this.processor) {
      try { this.processor.disconnect(); } catch (e) {}
      this.processor = null;
    }
    if (this.captureContext) {
      try { this.captureContext.close(); } catch (e) {}
      this.captureContext = null;
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((t) => t.stop());
      this.mediaStream = null;
    }
  }

  bargeIn() {
    this.stopAudioPlayback();
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'barge_in' }));
    }
  }

  sendTextInput(text) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'text_input', text }));
    }
  }

  disconnect() {
    this.stopAudioCapture();
    this.stopAudioPlayback();
    if (this.audioContext) {
      try { this.audioContext.close(); } catch (e) {}
      this.audioContext = null;
    }
    if (this.ws) {
      try { this.ws.close(); } catch (e) {}
      this.ws = null;
    }
    this.isConnected = false;
  }
}

export const liveAudioClient = new LiveAudioClient();
