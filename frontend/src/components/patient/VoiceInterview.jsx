import React, { useState, useEffect, useRef } from 'react';
import { 
  Mic, MicOff, Volume2, VolumeX, FastForward, Check, X, 
  HelpCircle, AlertOctagon, Type, Sliders, ArrowRight, Sparkles, Send, Edit3
} from 'lucide-react';
import { audioManager } from '../../audio/audio_manager';
import { liveAudioClient } from '../../audio/live_audio_client';
import { fetchNextQuestion, recordAnswer } from '../../services/api';

const QUESTION_CHIPS = {
  known_chronic_conditions: [
    { label: 'None / No Illness (कोई नहीं)', value: 'None, no known chronic illness' },
    { label: 'Diabetes / शुगर (मधुमेह)', value: 'Type 2 Diabetes Mellitus' },
    { label: 'High BP / रक्तचाप (बीपी)', value: 'High Blood Pressure (Hypertension)' },
    { label: 'Asthma / दमा', value: 'Bronchial Asthma' },
    { label: 'Acidity / गैस / पित्त', value: 'Hyperacidity and digestive gas' },
    { label: 'Thyroid / थायराइड', value: 'Hypothyroidism' }
  ],
  allergies_list: [
    { label: 'No Allergies (कोई एलर्जी नहीं)', value: 'No known allergies to food, drugs or herbs' },
    { label: 'Dust & Smoke', value: 'Allergy to dust and vehicular smoke' },
    { label: 'Skin Rash / Hives', value: 'Skin allergy with itching and red rash' },
    { label: 'Drug / Antibiotic Allergy', value: 'Allergic reaction to specific antibiotics' }
  ],
  active_medications: [
    { label: 'No Medicines (कोई दवा नहीं)', value: 'No regular or active medicines' },
    { label: 'Daily BP Tablet', value: 'Amlodipine 5mg once daily for BP' },
    { label: 'Diabetes Tablet', value: 'Metformin 500mg daily after meals' },
    { label: 'Ayurvedic Kadha / Churna', value: 'Ayurvedic herbal kadha and triphala churna' },
    { label: 'Vitamins / Calcium', value: 'Multivitamin and calcium supplements' }
  ],
  family_health_history: [
    { label: 'No Major Family Illness', value: 'No significant family history of chronic illness' },
    { label: 'Diabetes in Family', value: 'Father has diabetes' },
    { label: 'High BP in Family', value: 'Mother has hypertension' },
    { label: 'Heart Disease in Family', value: 'Family history of heart problems' }
  ],
  chief_complaint: [
    { label: 'Fever & Bodyache (बुखार)', value: 'Fever with generalized body ache and weakness' },
    { label: 'Cough & Cold (खांसी जुकाम)', value: 'Dry cough and throat irritation with runny nose' },
    { label: 'Knee / Joint Pain (घुटनों में दर्द)', value: 'Knee stiffness and joint pain, especially in morning' },
    { label: 'Acidity / Stomach Pain (पेट दर्द)', value: 'Burning sensation in chest and stomach acidity' },
    { label: 'Headache & Migraine (सिरदर्द)', value: 'Throbbing headache and dizziness' },
    { label: 'Fatigue & Tiredness (थकान)', value: 'Severe fatigue, lack of energy and disturbed sleep' }
  ],
  symptom_duration: [
    { label: '1 - 2 Days', value: '2 days' },
    { label: '3 - 5 Days', value: '4 days' },
    { label: '1 - 2 Weeks', value: '10 days' },
    { label: 'More than 1 Month', value: '6 weeks' }
  ],
  symptom_severity: [
    { label: 'Mild (हल्का / कमी)', value: 'Mild discomfort, able to perform daily tasks' },
    { label: 'Moderate (मध्यम)', value: 'Moderate pain, disrupts work and daily routine' },
    { label: 'Severe (तेज़ / जास्त)', value: 'Severe pain, unable to rest or work' }
  ],
  associated_symptoms: [
    { label: 'No Other Symptoms (कोई अन्य नहीं)', value: 'No other associated symptoms, just the main complaint' },
    { label: 'Fever & Chills (बुखार / ताप)', value: 'Mild fever with feeling of chills' },
    { label: 'Nausea & Vomiting (उल्टी / मळमळ)', value: 'Nausea, loss of appetite and feeling like vomiting' },
    { label: 'Headache & Dizziness (सिरदर्द / चक्कर)', value: 'Persistent headache and dizziness' },
    { label: 'Generalized Weakness (कमजोरी / थकवा)', value: 'General body ache and extreme fatigue' }
  ],
  diabetes_history: [
    { label: 'Under 1 Year (1 साल से कम)', value: 'Diagnosed less than 1 year ago, sugar mostly normal' },
    { label: '1 - 5 Years (1-5 साल)', value: 'Diagnosed 1 to 5 years ago, checking sugar regularly' },
    { label: 'Over 5 Years (5 साल से ज्यादा)', value: 'Longstanding diabetes over 5 years' }
  ],
  bp_medication_status: [
    { label: 'Daily BP Tablet (रोजाना दवा)', value: 'Taking prescribed BP tablet daily without missing' },
    { label: 'Sometimes / Irregular (अनियमित)', value: 'Taking BP tablet irregularly when feeling dizzy' },
    { label: 'Not on Medicines (दवा नहीं लेता)', value: 'Diagnosed high BP but currently not taking medicine' }
  ],
  asthma_inhaler_status: [
    { label: 'Daily Inhaler (रोजाना)', value: 'Using regular daily inhaler or nebulizer' },
    { label: 'As Needed (जरूरत पड़ने पर)', value: 'Only using SOS inhaler during acute breathlessness' },
    { label: 'Stable / No Recent Attack', value: 'Stable asthma, no major attack in past 6 months' }
  ],
  medicine_source_type: [
    { label: 'Doctor Prescribed (डॉक्टर की सलाह)', value: 'Formally prescribed by a licensed allopathic/Ayush doctor' },
    { label: 'Self-Started (खुद से शुरू की)', value: 'Over-the-counter self-medication based on advice of relatives' },
    { label: 'Home Remedy / Kadha (घरेलू काढ़ा)', value: 'Traditional home remedy and herbal decoction' }
  ],
  allergy_reaction_type: [
    { label: 'Skin Rash & Itching (दाने व खाज)', value: 'Allergic reaction presents with red skin rash and intense itching' },
    { label: 'Swelling of Face/Lips (सूजन)', value: 'Facial and lip swelling' },
    { label: 'Breathing Tightness (सांस में तकलीफ)', value: 'Throat tightness and difficulty breathing' }
  ],
  agni_digestion_quality: [
    { label: 'Normal / Good Digestion', value: 'Normal digestion and regular bowel movements (Samagni)' },
    { label: 'Slow / Heaviness after food', value: 'Sluggish digestion with abdominal heaviness (Mandagni)' },
    { label: 'Hyperacidity / Burning', value: 'Sharp appetite with hyperacidity and burning (Tikshnagni)' }
  ]
};

export default function VoiceInterview({ patient, session, onInterviewFinished, onRedFlagTriggered, onSessionExpired }) {
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [state, setState] = useState('tap_to_start'); // 'tap_to_start' | 'speaking' | 'listening' | 'reviewing' | 'processing'
  const [liveCaptions, setLiveCaptions] = useState('');
  const [draftAnswer, setDraftAnswer] = useState('');
  const [isMicActive, setIsMicActive] = useState(false);
  const [failures, setFailures] = useState(0);
  const [largeText, setLargeText] = useState(false);
  const [speed, setSpeed] = useState(1.0);
  const [turnLatency, setTurnLatency] = useState(null);
  const [loading, setLoading] = useState(false);
  const [micNotice, setMicNotice] = useState(null);
  const [liveNotice, setLiveNotice] = useState(null);

  const lang = patient.preferred_language || 'en';

  useEffect(() => {
    audioManager.requestWakeLock();

    // Connect WebSocket for Gemini Live API & Backend Triage Stream
    if (session?.session_id && patient?.patient_token) {
      liveAudioClient.connect({
        sessionId: session.session_id,
        patientToken: patient.patient_token,
        language: lang,
        onNotice: (msg) => {
          setLiveNotice(msg);
        },
        onTranscript: (speaker, text) => {
          if (speaker === 'patient') {
            const cleanText = (text || '').trim();
            if (cleanText) {
              setDraftAnswer(cleanText);
              setState('listening');
            }
          } else if (speaker === 'assistant') {
            setLiveCaptions((prev) => {
              if (!prev || prev === currentQuestion?.prompt) return text;
              return prev.includes(text) ? prev : `${prev} ${text}`.trim();
            });
          }
        },
        onSpeechStart: () => {
          setState('speaking');
        },
        onSpeechEnd: () => {
          setState('listening');
          setIsMicActive(true);
          // Start upstream 16kHz PCM streaming to Gemini Live
          liveAudioClient.startAudioCapture();
          // Start client-side speech recognition for instant real-time transcription
          audioManager.startListening(
            lang,
            (interim, final) => {
              const text = final || interim;
              if (text && text.trim()) {
                setDraftAnswer(text.trim());
              }
            },
            () => {},
            (finalText) => {
              if (finalText && finalText.trim()) {
                setDraftAnswer(finalText.trim());
              }
            }
          );
        },
        onLiveFallback: (prompt, fallbackLang) => {
          console.log('Live fallback invoked, speaking via browser TTS:', prompt);
          setState('speaking');
          audioManager.speak(prompt, fallbackLang || lang, () => {
            startListeningTurn();
          });
        },
        onRedFlag: (alert) => {
          onRedFlagTriggered(alert);
        },
        onLatency: (ms) => {
          setTurnLatency(ms);
        }
      });
    }

    return () => {
      audioManager.stopSpeaking();
      audioManager.stopListening();
      audioManager.releaseWakeLock();
      liveAudioClient.disconnect();
    };
  }, [session?.session_id, patient?.patient_token, lang]);

  const loadQuestion = async (failCount = failures) => {
    setLoading(true);
    setDraftAnswer('');
    setIsMicActive(false);
    try {
      const q = await fetchNextQuestion(patient.patient_token, session.session_id, failCount);
      if (!q) {
        // Interview complete!
        onInterviewFinished();
        return;
      }
      setCurrentQuestion(q);
      setLiveCaptions(q.prompt);

      // Check if Gemini Live API is connected
      const isLive = liveAudioClient.isConnected && (liveAudioClient.adapterType === 'LiveAdapter' || !liveAudioClient.adapterType);
      if (isLive) {
        setState('speaking');
        // Stop audio capture while assistant speaks to prevent speaker echo leaking into mic
        liveAudioClient.stopAudioCapture();
        setIsMicActive(false);
        liveAudioClient.askQuestion(q.prompt, lang);
      } else {
        // Fallback to local Web Speech
        setState('speaking');
        audioManager.speak(q.prompt, lang, () => {
          // Finished speaking question -> Start listening
          startListeningTurn(q);
        });
      }
    } catch (err) {
      console.error('Failed to get question:', err);
      if (err.message === 'SESSION_EXPIRED' && onSessionExpired) {
        onSessionExpired();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRepeatQuestion = () => {
    if (!currentQuestion) return;
    setState('speaking');
    audioManager.stopSpeaking();
    liveAudioClient.stopAudioPlayback();
    if (liveAudioClient.isConnected) {
      liveAudioClient.askQuestion(currentQuestion.prompt, lang);
    } else {
      audioManager.speak(currentQuestion.prompt, lang, () => {
        startListeningTurn();
      });
    }
  };

  const handleInitialStart = () => {
    liveAudioClient.ensureAudioContext();
    loadQuestion(0);
  };

  const startListeningTurn = (q = currentQuestion) => {
    setState('listening');
    setIsMicActive(true);
    setMicNotice(null);
    audioManager.startListening(
      lang,
      (interim, final) => {
        const text = final || interim;
        if (text) {
          setDraftAnswer(text);
          setMicNotice(null);
        }
      },
      (friendlyErr) => {
        setIsMicActive(false);
        setMicNotice(typeof friendlyErr === 'string' ? friendlyErr : 'Microphone unavailable. Use quick chips or type below.');
        setFailures((prev) => prev + 1);
      },
      (finalText) => {
        if (finalText && finalText.trim()) {
          setDraftAnswer(finalText);
          setIsMicActive(false);
        }
      },
      (status) => {
        if (status === 'listening') {
          setIsMicActive(true);
        } else if (status === 'stopped' || status === 'error' || status === 'unsupported') {
          setIsMicActive(false);
        }
      }
    );
  };

  const toggleMic = async () => {
    const isLive = liveAudioClient.isConnected && liveAudioClient.adapterType === 'LiveAdapter';
    if (isMicActive) {
      if (isLive) {
        liveAudioClient.stopAudioCapture();
      } else {
        audioManager.stopListening();
      }
      setIsMicActive(false);
    } else {
      audioManager.stopSpeaking();
      liveAudioClient.stopAudioPlayback();
      if (isLive) {
        const ok = await liveAudioClient.startAudioCapture();
        if (ok) {
          setIsMicActive(true);
          setState('listening');
          setMicNotice(null);
        } else {
          setMicNotice('Microphone access blocked. Please allow mic in browser address bar.');
        }
      } else {
        startListeningTurn();
      }
    }
  };

  const handleSelectChip = (chipValue) => {
    audioManager.stopSpeaking();
    liveAudioClient.stopAudioPlayback();
    audioManager.stopListening();
    liveAudioClient.stopAudioCapture();
    setIsMicActive(false);

    // For multi-select fields (like chronic conditions, allergies), allow toggling/combining multiple items
    if (currentQuestion?.question_type === 'multi_select_or_text' || currentQuestion?.field_key === 'known_chronic_conditions') {
      if (chipValue.includes('None') || chipValue.includes('कोई नहीं')) {
        setDraftAnswer(chipValue);
      } else {
        setDraftAnswer((prev) => {
          if (!prev || prev.includes('None') || prev.includes('कोई नहीं')) return chipValue;
          const items = prev.split(', ').map(s => s.trim()).filter(Boolean);
          if (items.includes(chipValue)) {
            const filtered = items.filter(i => i !== chipValue);
            return filtered.join(', ');
          } else {
            return [...items, chipValue].join(', ');
          }
        });
      }
    } else {
      setDraftAnswer(chipValue);
    }
  };

  const handleConfirmAndNext = async (textToSubmit = draftAnswer) => {
    const text = (textToSubmit || draftAnswer || '').trim();
    if (!text || !currentQuestion) return;

    audioManager.stopListening();
    audioManager.stopSpeaking();
    liveAudioClient.stopAudioPlayback();
    liveAudioClient.stopAudioCapture();
    setIsMicActive(false);
    setState('processing');

    const t0 = performance.now();
    try {
      const res = await recordAnswer({
        patient_token: patient.patient_token,
        session_id: session.session_id,
        section_id: currentQuestion.section_id,
        field_key: currentQuestion.field_key,
        value: text,
        source: 'patient_said',
        confidence: 0.95,
        transcript_quote: text
      });

      const elapsed = Math.round(performance.now() - t0);
      setTurnLatency(elapsed);

      // Check if emergency red-flag triggered
      if (res.status === 'emergency_halt') {
        onRedFlagTriggered(res.red_flag);
        return;
      }

      // Success -> Reset failure count and load next question
      setFailures(0);
      loadQuestion(0);
    } catch (err) {
      console.error('Answer submission error:', err);
      setState('listening');
    }
  };

  // Barge-In interrupt
  const handleBargeIn = () => {
    audioManager.stopSpeaking();
    liveAudioClient.bargeIn();
    setState('listening');
    const isLive = liveAudioClient.isConnected && liveAudioClient.adapterType === 'LiveAdapter';
    if (isLive) {
      liveAudioClient.startAudioCapture().then(() => setIsMicActive(true));
    } else {
      startListeningTurn();
    }
  };

  const handleSkipQuestion = async () => {
    audioManager.stopSpeaking();
    audioManager.stopListening();
    setIsMicActive(false);
    if (!currentQuestion) return;

    await recordAnswer({
      patient_token: patient.patient_token,
      session_id: session.session_id,
      section_id: currentQuestion.section_id,
      field_key: currentQuestion.field_key,
      value: 'Skipped by patient',
      source: 'skipped',
      confidence: 1.0,
      transcript_quote: 'Skipped by patient'
    });

    setFailures(0);
    loadQuestion(0);
  };

  const handleSpeedChange = (newSpeed) => {
    setSpeed(newSpeed);
    audioManager.speechRate = newSpeed;
  };

  if (state === 'tap_to_start') {
    return (
      <div className="max-w-md mx-auto text-center p-8 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-6">
        <div className="w-20 h-20 bg-emerald-100 text-emerald-800 rounded-full flex items-center justify-center mx-auto shadow-inner">
          <Mic className="w-10 h-10" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Ready for Voice Intake</h2>
          <p className="text-sm text-slate-500 mt-1">
            Tap the button below to start. The assistant will ask questions one at a time.
          </p>
        </div>
        <button
          onClick={handleInitialStart}
          className="w-full bg-emerald-700 hover:bg-emerald-800 text-white font-bold py-4 rounded-xl shadow-lg transition text-lg flex items-center justify-center space-x-2 min-h-touch"
        >
          <span>Tap to Start Voice Interview</span>
          <ArrowRight className="w-6 h-6" />
        </button>
      </div>
    );
  }

  const chips = currentQuestion ? (QUESTION_CHIPS[currentQuestion.field_key] || []) : [];

  return (
    <div className="max-w-xl mx-auto space-y-4">
      {/* Top Controls: Large Text Toggle & Speed Selector */}
      <div className="flex items-center justify-between bg-white px-4 py-2 rounded-xl border border-slate-200 text-xs">
        <button
          onClick={() => setLargeText(!largeText)}
          className={`flex items-center space-x-1 px-3 py-1.5 rounded font-medium border transition ${
            largeText ? 'bg-emerald-700 text-white border-emerald-700' : 'bg-slate-50 text-slate-700 border-slate-200'
          }`}
        >
          <Type className="w-3.5 h-3.5" />
          <span>Large Text</span>
        </button>

        <div className="flex items-center space-x-2">
          <span className="text-slate-500">Speed:</span>
          {[0.8, 1.0, 1.2].map((s) => (
            <button
              key={s}
              onClick={() => handleSpeedChange(s)}
              className={`px-2 py-1 rounded font-medium ${
                speed === s ? 'bg-emerald-100 text-emerald-800 font-bold' : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              {s}x
            </button>
          ))}
        </div>

        {turnLatency && (
          <span className="text-slate-400 text-[10px]">Turn: {turnLatency}ms</span>
        )}
      </div>

      {/* Main Conversation Visualizer & Live Captions */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-5 text-center">
        {/* Status Badge */}
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-slate-100">
          <span className={`w-2.5 h-2.5 rounded-full ${
            state === 'speaking' ? 'bg-emerald-600 animate-pulse' :
            isMicActive ? 'bg-red-600 animate-ping' : 'bg-slate-400'
          }`} />
          <span className="text-slate-700">
            {state === 'speaking' && 'Assistant Speaking...'}
            {state === 'listening' && (isMicActive ? 'Listening to You...' : 'Ready for Answer')}
            {state === 'processing' && 'AI Extracting Details...'}
          </span>
        </div>

        {/* Section Title */}
        <p className="text-xs font-bold text-emerald-800 uppercase tracking-widest">
          {currentQuestion?.section_title || 'OPD Intake'}
        </p>

        {/* Spoken Question */}
        <div className="min-h-[70px] flex flex-col items-center justify-center px-2 space-y-2">
          <p className={`font-semibold text-slate-800 leading-snug transition-all ${
            largeText ? 'text-2xl' : 'text-lg'
          }`}>
            "{liveCaptions}"
          </p>
          <button
            type="button"
            onClick={handleRepeatQuestion}
            className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 transition"
          >
            <Volume2 className="w-3.5 h-3.5 text-emerald-700" />
            <span>Hear Question Again</span>
          </button>
        </div>

        {/* Gemini Live Adapter Status Notice */}
        {liveNotice && (
          <div className="p-2.5 bg-blue-50 border border-blue-200 rounded-xl text-blue-900 text-xs flex items-center justify-between text-left">
            <div className="flex items-center space-x-1.5">
              <Sparkles className="w-4 h-4 text-blue-600 flex-shrink-0" />
              <span className="text-[11px] font-medium">{liveNotice}</span>
            </div>
            <button onClick={() => setLiveNotice(null)} className="text-blue-400 hover:text-blue-700 ml-2">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Microphone Notice / Insecure Origin Alert */}
        {micNotice && (
          <div className="p-3 bg-amber-50 border border-amber-300 rounded-xl text-amber-900 text-xs flex items-start space-x-2 text-left">
            <AlertOctagon className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold">{micNotice}</p>
              <p className="text-[11px] text-amber-700 mt-0.5">Tip: On mobile, use HTTPS or tap any quick-response option below.</p>
            </div>
            <button onClick={() => setMicNotice(null)} className="text-amber-500 hover:text-amber-800">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Quick-Response Chips (One-Tap Options for Fast & Accurate Entry) */}
        {chips.length > 0 && (
          <div className="pt-1 text-left space-y-1.5">
            <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              Quick One-Tap Options:
            </p>
            <div className="flex flex-wrap gap-2">
              {chips.map((chip, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelectChip(chip.value)}
                  className={`px-3 py-2 rounded-xl text-xs font-semibold transition border ${
                    (draftAnswer === chip.value || (draftAnswer && draftAnswer.includes(chip.value)))
                      ? 'bg-emerald-700 text-white border-emerald-700 shadow-sm'
                      : 'bg-emerald-50/70 hover:bg-emerald-100 text-emerald-900 border-emerald-200'
                  }`}
                >
                  {chip.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Always-Accessible Input & Speech Area */}
        <div className="space-y-3 pt-2 text-left">
          <div className="relative flex items-center">
            <input
              type="text"
              value={draftAnswer}
              onChange={(e) => setDraftAnswer(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && draftAnswer.trim()) {
                  handleConfirmAndNext();
                }
              }}
              placeholder="Speak using mic or type your answer..."
              className="w-full px-4 py-3.5 pr-20 rounded-xl border border-slate-300 bg-slate-50 text-sm font-medium text-slate-900 focus:bg-white focus:border-emerald-600 focus:outline-none shadow-inner"
            />
            <div className="absolute right-2 flex items-center space-x-1">
              <button
                type="button"
                onClick={toggleMic}
                title={isMicActive ? "Mute Microphone" : "Turn on Microphone"}
                className={`p-2 rounded-lg transition ${
                  isMicActive ? 'bg-red-600 text-white animate-pulse' : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
                }`}
              >
                {isMicActive ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Understood Echo & Confirmation (Large Touch Buttons as requested in brief) */}
          {draftAnswer && (
            <div className="p-3.5 bg-emerald-50 rounded-xl border border-emerald-300 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800 flex items-center space-x-1">
                  <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Assistant Understood:</span>
                </span>
                <span className="text-[10px] text-emerald-700 font-medium">Verify & Confirm</span>
              </div>
              <p className="text-sm font-bold text-emerald-950">
                "{draftAnswer}"
              </p>
              <div className="pt-1 flex items-center space-x-3">
                <button
                  onClick={() => handleConfirmAndNext(draftAnswer)}
                  disabled={loading}
                  className="flex-1 bg-emerald-700 hover:bg-emerald-800 text-white font-bold py-3 px-4 rounded-xl shadow flex items-center justify-center space-x-2 min-h-touch text-sm"
                >
                  <Check className="w-5 h-5" />
                  <span>Yes, Confirm & Next</span>
                </button>
                <button
                  onClick={() => setDraftAnswer('')}
                  className="px-4 py-3 bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 font-semibold rounded-xl text-xs min-h-touch"
                >
                  <X className="w-4 h-4 inline mr-1" />
                  <span>Clear</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Audio / Interrupt Button */}
        {state === 'speaking' && (
          <div className="pt-1">
            <button
              onClick={handleBargeIn}
              className="px-5 py-2.5 bg-amber-600 hover:bg-amber-700 text-white font-bold rounded-full shadow transition inline-flex items-center space-x-2 text-xs"
            >
              <VolumeX className="w-4 h-4" />
              <span>Interrupt & Speak</span>
            </button>
          </div>
        )}
      </div>

      {/* Bottom Auxiliary Controls: Always Visible Skip & Finish Options */}
      <div className="flex items-center justify-between pt-1">
        <button
          type="button"
          onClick={() => {
            audioManager.stopSpeaking();
            liveAudioClient.stopAudioPlayback();
            audioManager.stopListening();
            liveAudioClient.stopAudioCapture();
            onInterviewFinished();
          }}
          className="px-3.5 py-2 bg-emerald-50 hover:bg-emerald-100 rounded-xl border border-emerald-200 text-emerald-800 font-semibold text-xs flex items-center space-x-1.5 min-h-touch shadow-sm transition"
        >
          <Check className="w-3.5 h-3.5 text-emerald-600" />
          <span>Finish & View Summary</span>
        </button>

        <button
          type="button"
          onClick={handleSkipQuestion}
          className="px-4 py-2 bg-white rounded-xl border border-slate-200 hover:border-slate-300 text-slate-600 font-medium text-xs flex items-center space-x-1.5 min-h-touch shadow-sm transition"
        >
          <FastForward className="w-4 h-4 text-slate-400" />
          <span>Skip Question</span>
        </button>
      </div>
    </div>
  );
}
