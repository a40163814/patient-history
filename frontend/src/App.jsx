import React, { useState } from 'react';
import { 
  Heart, Users, ShieldAlert, Sparkles, Smartphone, Tablet, 
  Stethoscope, CheckCircle2, RotateCcw, Globe 
} from 'lucide-react';
import { updatePatientLanguage } from './services/api';
import LoginOtp from './components/patient/LoginOtp';
import ConsentScreen from './components/patient/ConsentScreen';
import VitalsUpload from './components/patient/VitalsUpload';
import VoiceInterview from './components/patient/VoiceInterview';
import ConversationEndScreen from './components/patient/ConversationEndScreen';
import PatientReview from './components/patient/PatientReview';
import RedFlagAlert from './components/patient/RedFlagAlert';
import DoctorQueue from './components/doctor/DoctorQueue';
import CaseReview from './components/doctor/CaseReview';

export default function App() {
  const [role, setRole] = useState('patient'); // 'patient' | 'kiosk' | 'doctor'
  
  // Resumable Session State with localStorage persistence
  const [patientStep, setPatientStep] = useState(() => {
    try { return localStorage.getItem('ayush_step') || 'login'; } catch { return 'login'; }
  });
  const [patientData, setPatientData] = useState(() => {
    try {
      const s = localStorage.getItem('ayush_patient');
      return s ? JSON.parse(s) : null;
    } catch { return null; }
  });
  const [sessionData, setSessionData] = useState(() => {
    try {
      const s = localStorage.getItem('ayush_session');
      return s ? JSON.parse(s) : null;
    } catch { return null; }
  });
  const [redFlagData, setRedFlagData] = useState(() => {
    try {
      const s = localStorage.getItem('ayush_redflag');
      return s ? JSON.parse(s) : null;
    } catch { return null; }
  });
  const [selectedCaseSessionId, setSelectedCaseSessionId] = useState(null);

  const updateStep = (newStep) => {
    setPatientStep(newStep);
    try { localStorage.setItem('ayush_step', newStep); } catch {}
  };

  const updatePatient = (newData) => {
    setPatientData(newData);
    try {
      if (newData) localStorage.setItem('ayush_patient', JSON.stringify(newData));
      else localStorage.removeItem('ayush_patient');
    } catch {}
  };

  const updateSession = (newSess) => {
    setSessionData(newSess);
    try {
      if (newSess) localStorage.setItem('ayush_session', JSON.stringify(newSess));
      else localStorage.removeItem('ayush_session');
    } catch {}
  };

  const handleGlobalLanguageChange = async (newLang) => {
    if (patientData) {
      const updated = { ...patientData, preferred_language: newLang };
      updatePatient(updated);
      if (patientData.patient_token) {
        try {
          await updatePatientLanguage(patientData.patient_token, newLang);
        } catch (e) {
          console.warn('Language update backend sync:', e);
        }
      }
    }
  };

  // Patient Flow Handlers
  const handleLoginSuccess = (data) => {
    updatePatient(data);
    updateSession({ session_id: data.session_id });
    updateStep('consent');
  };

  const handleConsentApproved = () => {
    updateStep('vitals');
  };

  const handleVitalsCompleted = (vitals) => {
    updateStep('interview');
  };

  const handleInterviewFinished = () => {
    updateStep('conversation_end');
  };

  const handleRedFlagTriggered = (alert) => {
    setRedFlagData(alert);
    try { localStorage.setItem('ayush_redflag', JSON.stringify(alert)); } catch {}
    updateStep('red_flag');
  };

  const handleSubmittedToQueue = () => {
    updateStep('completed');
  };

  const handleResetToLogin = () => {
    try {
      localStorage.removeItem('ayush_step');
      localStorage.removeItem('ayush_patient');
      localStorage.removeItem('ayush_session');
      localStorage.removeItem('ayush_redflag');
    } catch {}
    setPatientStep('login');
    setPatientData(null);
    setSessionData(null);
    setRedFlagData(null);
  };

  return (
    <div className={`min-h-screen flex flex-col ${role === 'kiosk' ? 'bg-slate-100' : 'bg-slate-50'}`}>
      {/* Top Application Header */}
      <header className="bg-emerald-800 text-white px-4 py-3 shadow-md flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-full bg-white text-emerald-800 font-bold flex items-center justify-center text-lg shadow">
            आ
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight leading-none">AyushIntake</h1>
            <p className="text-[11px] text-emerald-200 mt-0.5">Ministry of Ayush • Pre-OPD Triage</p>
          </div>
        </div>

        {/* Top Controls: Language + Role Switcher */}
        <div className="flex items-center space-x-2">
          {/* Global Language Switcher */}
          {patientData && (
            <div className="flex items-center space-x-0.5 bg-emerald-950/60 p-1 rounded-xl text-[11px]">
              <Globe className="w-3.5 h-3.5 text-emerald-300 ml-1 mr-0.5 hidden sm:inline" />
              {['en', 'hi', 'mr'].map((lng) => (
                <button
                  key={lng}
                  onClick={() => handleGlobalLanguageChange(lng)}
                  className={`px-2 py-1 rounded font-bold uppercase transition ${
                    patientData.preferred_language === lng
                      ? 'bg-white text-emerald-900 shadow'
                      : 'text-emerald-200 hover:text-white'
                  }`}
                >
                  {lng}
                </button>
              ))}
            </div>
          )}

          {/* View Switcher for Live Demo & Testing */}
          <div className="flex items-center space-x-1 bg-emerald-950/60 p-1 rounded-xl text-xs">
          <button
            onClick={() => { setRole('patient'); setSelectedCaseSessionId(null); }}
            className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center space-x-1 min-h-[36px] ${
              role === 'patient' ? 'bg-white text-emerald-900 shadow font-bold' : 'text-emerald-100 hover:text-white'
            }`}
          >
            <Smartphone className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Patient (PWA)</span>
          </button>

          <button
            onClick={() => { setRole('kiosk'); setSelectedCaseSessionId(null); }}
            className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center space-x-1 min-h-[36px] ${
              role === 'kiosk' ? 'bg-white text-emerald-900 shadow font-bold' : 'text-emerald-100 hover:text-white'
            }`}
          >
            <Tablet className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Tablet Kiosk</span>
          </button>

          <button
            onClick={() => setRole('doctor')}
            className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center space-x-1 min-h-[36px] ${
              role === 'doctor' ? 'bg-white text-emerald-900 shadow font-bold' : 'text-emerald-100 hover:text-white'
            }`}
          >
            <Stethoscope className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Doctor OPD</span>
          </button>
        </div>

        {/* Reset / Start Fresh Session */}
        {patientData && (
          <button
            onClick={handleResetToLogin}
            title="Start fresh intake session"
            className="px-2.5 py-1.5 rounded-xl bg-emerald-950/60 hover:bg-emerald-900 text-emerald-200 hover:text-white transition flex items-center space-x-1 text-xs min-h-[36px]"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span className="hidden md:inline">New Session</span>
          </button>
        )}
      </div>
    </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-4 md:p-6">
        {/* DOCTOR VIEW */}
        {role === 'doctor' && (
          selectedCaseSessionId ? (
            <CaseReview
              sessionId={selectedCaseSessionId}
              onBackToQueue={() => setSelectedCaseSessionId(null)}
            />
          ) : (
            <DoctorQueue
              onSelectCase={(sessId) => setSelectedCaseSessionId(sessId)}
            />
          )
        )}

        {/* PATIENT / KIOSK FLOW */}
        {(role === 'patient' || role === 'kiosk') && (
          <>
            {/* Step Progress Bar (when logged in and not halted) */}
            {patientStep !== 'login' && patientStep !== 'red_flag' && patientStep !== 'completed' && (
              <div className="mb-6 max-w-xl mx-auto">
                <div className="flex items-center justify-between text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">
                  <span className={patientStep === 'consent' ? 'text-emerald-700' : ''}>1. Consent</span>
                  <span className={patientStep === 'vitals' ? 'text-emerald-700' : ''}>2. Vitals</span>
                  <span className={patientStep === 'interview' ? 'text-emerald-700' : ''}>3. Voice History</span>
                  <span className={(patientStep === 'conversation_end' || patientStep === 'review') ? 'text-emerald-700' : ''}>4. Summary & Review</span>
                </div>
                <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-emerald-700 h-full transition-all duration-300"
                    style={{
                      width:
                        patientStep === 'consent' ? '25%' :
                        patientStep === 'vitals' ? '50%' :
                        patientStep === 'interview' ? '75%' : '100%'
                    }}
                  />
                </div>
              </div>
            )}

            {patientStep === 'login' && (
              <LoginOtp onLoginSuccess={handleLoginSuccess} />
            )}

            {patientStep === 'consent' && (
              <ConsentScreen
                patient={patientData}
                onConsentApproved={handleConsentApproved}
              />
            )}

            {patientStep === 'vitals' && (
              <VitalsUpload
                patient={patientData}
                session={sessionData}
                onVitalsCompleted={handleVitalsCompleted}
              />
            )}

            {patientStep === 'interview' && (
              <VoiceInterview
                patient={patientData}
                session={sessionData}
                onInterviewFinished={handleInterviewFinished}
                onRedFlagTriggered={handleRedFlagTriggered}
                onSessionExpired={handleResetToLogin}
              />
            )}

            {patientStep === 'conversation_end' && (
              <ConversationEndScreen
                patient={patientData}
                session={sessionData}
                onReviewRequested={() => updateStep('review')}
                onSubmittedToQueue={handleSubmittedToQueue}
                onSwitchToDoctor={() => {
                  setRole('doctor');
                  setSelectedCaseSessionId(sessionData?.session_id);
                }}
              />
            )}

            {patientStep === 'review' && (
              <PatientReview
                patient={patientData}
                session={sessionData}
                onSubmittedToQueue={handleSubmittedToQueue}
                onBackToSummary={() => updateStep('conversation_end')}
              />
            )}

            {patientStep === 'red_flag' && (
              <RedFlagAlert
                alertData={redFlagData}
                onReset={handleResetToLogin}
              />
            )}

            {patientStep === 'completed' && (
              <div className="max-w-md mx-auto text-center p-8 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-6">
                <div className="w-20 h-20 bg-emerald-100 text-emerald-800 rounded-full flex items-center justify-center mx-auto shadow-inner">
                  <CheckCircle2 className="w-10 h-10" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-slate-800">History Submitted!</h2>
                  <p className="text-sm text-slate-500 mt-2">
                    Your token is <b>{patientData?.patient_token}</b>. Please proceed to the waiting area. The Ayush doctor will call your token shortly.
                  </p>
                </div>
                <div className="pt-2">
                  <button
                    onClick={() => {
                      setRole('doctor');
                      setSelectedCaseSessionId(sessionData?.session_id);
                    }}
                    className="w-full bg-emerald-700 hover:bg-emerald-800 text-white font-bold py-3.5 rounded-xl shadow transition min-h-touch text-sm"
                  >
                    Switch to Doctor View to Review & Stamp PDF
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* Safety Notice Footer */}
      <footer className="bg-white border-t border-slate-200 px-4 py-2.5 text-center text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-1">
        <span>Draft prepared from patient answers. Not a diagnosis.</span>
        <span className="text-emerald-800 font-semibold">AyushIntake v1.0.0 (DPDP Act 2023 Compliant)</span>
      </footer>
    </div>
  );
}
