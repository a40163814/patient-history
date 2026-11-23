import React, { useState, useEffect } from 'react';
import { 
  CheckCircle2, Sparkles, Volume2, ArrowRight, Edit3, 
  Send, FileText, Activity, AlertCircle, Heart, Stethoscope, Clock, ShieldCheck
} from 'lucide-react';
import { fetchPatientReview, submitFinalIntake } from '../../services/api';
import { audioManager } from '../../audio/audio_manager';
import { liveAudioClient } from '../../audio/live_audio_client';

export default function ConversationEndScreen({ 
  patient, 
  session, 
  onReviewRequested, 
  onSubmittedToQueue, 
  onSwitchToDoctor 
}) {
  const [reviewData, setReviewData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [isSpeakingClosing, setIsSpeakingClosing] = useState(false);

  const lang = patient?.preferred_language || 'en';

  const closingPhrases = {
    en: "Thank you for completing your intake! Your health details have been recorded and organized for the doctor. Please review your answers below or proceed directly to the OPD queue.",
    hi: "साक्षात्कार पूरा करने के लिए धन्यवाद! आपकी सभी स्वास्थ्य जानकारी डॉक्टर के लिए सुरक्षित कर ली गई है। कृपया नीचे दिए गए विवरण की समीक्षा करें या ओपीडी कतार में आगे बढ़ें।",
    mr: "आरोग्य माहिती पूर्ण केल्याबद्दल धन्यवाद! तुमची सर्व माहिती डॉक्टरांसाठी तयार केली आहे. कृपया खाली दिलेल्या माहितीची खात्री करा किंवा ओपीडी रांगेत पुढे जा."
  };

  const spokenClosing = closingPhrases[lang] || closingPhrases.en;

  const playClosingAudio = () => {
    setIsSpeakingClosing(true);
    audioManager.stopSpeaking();
    liveAudioClient.stopAudioPlayback();

    if (liveAudioClient.isConnected) {
      liveAudioClient.askQuestion(spokenClosing, lang);
      setTimeout(() => setIsSpeakingClosing(false), 5000);
    } else {
      audioManager.speak(spokenClosing, lang, () => {
        setIsSpeakingClosing(false);
      });
    }
  };

  useEffect(() => {
    async function loadData() {
      try {
        const data = await fetchPatientReview(patient.patient_token, session.session_id);
        setReviewData(data);
      } catch (err) {
        console.error('Failed to load review data for end screen:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();

    // Automatically speak the friendly closing statement once on mount
    const timer = setTimeout(() => {
      playClosingAudio();
    }, 600);

    return () => {
      clearTimeout(timer);
      audioManager.stopSpeaking();
      liveAudioClient.stopAudioPlayback();
    };
  }, [patient?.patient_token, session?.session_id]);

  const handleQuickSubmit = async () => {
    setSubmitting(true);
    try {
      await submitFinalIntake(patient.patient_token, session.session_id);
      onSubmittedToQueue();
    } catch (err) {
      console.error('Submit error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-xl mx-auto p-12 text-center text-slate-500 space-y-3">
        <div className="w-10 h-10 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="font-semibold animate-pulse">Compiling your clinical intake case sheet...</p>
      </div>
    );
  }

  const sections = reviewData?.sections || {};
  const vitals = reviewData?.vitals || {};
  const reports = reviewData?.reports || [];

  // Helper to extract field value
  const getFieldValue = (secKey, fieldKey) => {
    const secFields = sections[secKey] || [];
    const item = secFields.find(f => f.field_key === fieldKey);
    return item ? item.value : null;
  };

  const chiefComplaint = getFieldValue('symptoms', 'chief_complaint') || 'Health Consultation';
  const duration = getFieldValue('symptoms', 'symptom_duration');
  const severity = getFieldValue('symptoms', 'symptom_severity');
  const modulating = getFieldValue('symptoms', 'modulating_factors');
  const associated = getFieldValue('symptoms', 'associated_symptoms');

  const chronic = getFieldValue('pre_existing_conditions', 'known_chronic_conditions');
  const meds = getFieldValue('current_medicines', 'active_medications');
  const allergies = getFieldValue('allergies', 'allergies_list');

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fadeIn pb-12">
      {/* 1. Congratulatory Header & Spoken Voice Banner */}
      <div className="bg-gradient-to-br from-emerald-800 via-emerald-700 to-teal-800 text-white rounded-3xl p-6 md:p-8 shadow-xl text-center relative overflow-hidden">
        <div className="absolute -top-12 -right-12 w-40 h-40 bg-white/10 rounded-full blur-2xl pointer-events-none" />
        <div className="absolute -bottom-10 -left-10 w-36 h-36 bg-emerald-400/20 rounded-full blur-xl pointer-events-none" />

        <div className="inline-flex p-3 bg-white/20 backdrop-blur-md text-white rounded-2xl shadow-inner mb-3">
          <CheckCircle2 className="w-10 h-10 text-emerald-200" />
        </div>

        <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight">
          {lang === 'hi' ? 'स्वास्थ्य साक्षात्कार पूरा हुआ!' : lang === 'mr' ? 'आरोग्य माहिती पूर्ण झाली!' : 'Intake Conversation Complete!'}
        </h2>
        <p className="text-emerald-100 text-xs md:text-sm mt-1 max-w-md mx-auto">
          {lang === 'hi'
            ? 'आपकी आवाज से डॉक्टर के लिए विस्तृत क्लिनिकल केस शीट तैयार कर ली गई है।'
            : lang === 'mr'
            ? 'तुमच्या आवाजावरून डॉक्टरांसाठी सविस्तर केस शीट तयार करण्यात आली आहे.'
            : 'Your detailed pre-OPD case summary has been compiled for the consulting doctor.'}
        </p>

        {/* Audio Replay Pill */}
        <div className="mt-4 inline-flex items-center space-x-2 bg-emerald-950/40 hover:bg-emerald-950/60 border border-emerald-400/30 px-3.5 py-1.5 rounded-full text-xs transition cursor-pointer" onClick={playClosingAudio}>
          <Volume2 className={`w-4 h-4 text-emerald-300 ${isSpeakingClosing ? 'animate-pulse text-white' : ''}`} />
          <span className="font-semibold text-emerald-100">
            {isSpeakingClosing
              ? (lang === 'hi' ? 'एआई बोल रहा है...' : lang === 'mr' ? 'एआय बोलत आहे...' : 'AI Speaking...')
              : (lang === 'hi' ? 'एआई संदेश फिर से सुनें' : lang === 'mr' ? 'एआय संदेश पुन्हा ऐका' : 'Replay AI Closing Message')}
          </span>
        </div>

        {/* Token Badge */}
        <div className="mt-5 inline-block bg-white text-emerald-900 rounded-2xl px-5 py-2.5 shadow-md">
          <span className="text-[10px] font-bold uppercase tracking-widest text-emerald-700 block">
            Official OPD Intake Token
          </span>
          <span className="text-xl md:text-2xl font-black font-mono tracking-wider">
            {patient?.patient_token || 'AYUSH-TOKEN'}
          </span>
        </div>
      </div>

      {/* 2. Structured Patient History Overview */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 md:p-6 shadow-sm space-y-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-emerald-700" />
            <h3 className="font-bold text-slate-800 text-sm md:text-base">
              Recorded Clinical History Highlights
            </h3>
          </div>
          <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
            {vitals.ayush_system ? vitals.ayush_system.toUpperCase() : 'ALLOPATHY'} OPD
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Card A: Chief Problem & Symptoms */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-700 uppercase tracking-wide">
              <Heart className="w-3.5 h-3.5 text-red-500" />
              <span>Chief Complaint & Symptoms</span>
            </div>
            <p className="text-sm font-bold text-slate-900">
              {chiefComplaint}
            </p>
            <div className="text-xs text-slate-600 space-y-1 pt-1 border-t border-slate-200">
              {duration && <p><b>Duration:</b> {duration}</p>}
              {severity && <p><b>Severity:</b> {severity}</p>}
              {modulating && <p><b>Modulating:</b> {modulating}</p>}
              {associated && <p><b>Associated:</b> {associated}</p>}
            </div>
          </div>

          {/* Card B: Medical History & Medicines */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-700 uppercase tracking-wide">
              <Stethoscope className="w-3.5 h-3.5 text-emerald-700" />
              <span>Medical History & Medicines</span>
            </div>
            <div className="text-xs text-slate-700 space-y-1.5">
              <p><b>Chronic Illness:</b> {chronic || 'None reported'}</p>
              <p><b>Active Medicines:</b> {meds || 'None reported'}</p>
              <p><b>Known Allergies:</b> {allergies || 'No allergies'}</p>
            </div>
          </div>

          {/* Card C: Vitals Summary */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-700 uppercase tracking-wide">
              <Activity className="w-3.5 h-3.5 text-teal-600" />
              <span>Physical Vitals</span>
            </div>
            <div className="flex items-center space-x-4 text-xs text-slate-800">
              <div>
                <span className="text-slate-500 block text-[10px]">Height</span>
                <span className="font-bold">{vitals.height_cm ? `${vitals.height_cm} cm` : 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">Weight</span>
                <span className="font-bold">{vitals.weight_kg ? `${vitals.weight_kg} kg` : 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">BMI</span>
                <span className="font-bold">{vitals.bmi ? `${vitals.bmi} (${vitals.bmi_category || 'Normal'})` : 'N/A'}</span>
              </div>
            </div>
          </div>

          {/* Card D: Reports & Documents */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-700 uppercase tracking-wide">
              <FileText className="w-3.5 h-3.5 text-indigo-600" />
              <span>Diagnostic Reports</span>
            </div>
            <p className="text-xs text-slate-800 font-semibold">
              {reports.length > 0 
                ? `${reports.length} report(s) parsed and attached to case sheet`
                : 'No prior diagnostic documents uploaded'}
            </p>
            {reports.length > 0 && (
              <p className="text-[11px] text-slate-500 truncate">
                Files: {reports.map(r => r.file_name).join(', ')}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* 3. Action Buttons & Next Steps */}
      <div className="space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {/* Action A: Review & Edit Answers */}
          <button
            onClick={onReviewRequested}
            className="w-full py-4 px-5 rounded-2xl bg-white hover:bg-slate-50 text-slate-800 border-2 border-slate-300 font-bold text-sm shadow-sm flex items-center justify-center space-x-2 transition min-h-touch"
          >
            <Edit3 className="w-4 h-4 text-emerald-700" />
            <span>
              {lang === 'hi' ? 'विवरण की जांच / संपादन करें' : lang === 'mr' ? 'माहिती तपासा / दुरुस्त करा' : 'Review & Verify Answers'}
            </span>
          </button>

          {/* Action B: Direct Submit to Doctor Queue */}
          <button
            onClick={handleQuickSubmit}
            disabled={submitting}
            className="w-full py-4 px-5 rounded-2xl bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-sm shadow-md flex items-center justify-center space-x-2 transition min-h-touch disabled:opacity-50"
          >
            <Send className="w-4 h-4 text-emerald-200" />
            <span>
              {submitting 
                ? 'Submitting to Queue...'
                : (lang === 'hi' ? 'डॉक्टर कतार में भेजें' : lang === 'mr' ? 'थेट डॉक्टरांकडे पाठवा' : 'Confirm & Submit to Doctor Queue')}
            </span>
          </button>
        </div>

        {/* Demo Switcher shortcut for testing */}
        {onSwitchToDoctor && (
          <div className="pt-2 text-center">
            <button
              onClick={onSwitchToDoctor}
              className="text-xs text-emerald-800 hover:text-emerald-950 font-semibold underline underline-offset-4 inline-flex items-center space-x-1"
            >
              <Stethoscope className="w-3.5 h-3.5" />
              <span>Switch directly to Doctor OPD View to examine Case Sheet & generate PDF</span>
            </button>
          </div>
        )}
      </div>

      {/* Disclaimer */}
      <p className="text-[11px] text-slate-400 text-center">
        Draft prepared from patient voice consultation. Not a medical diagnosis.
      </p>
    </div>
  );
}
