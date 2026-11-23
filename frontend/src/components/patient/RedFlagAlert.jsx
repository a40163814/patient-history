import React from 'react';
import { AlertTriangle, PhoneCall, ShieldAlert, HeartPulse } from 'lucide-react';

export default function RedFlagAlert({ alertData, onReset }) {
  const patientMsg = alertData?.patient_message || 
    "Please sit down and rest comfortably. Our clinic staff and medical team are being alerted immediately to attend to you right now.";
  const helpline = alertData?.crisis_helpline || "14416";
  const ambulance = alertData?.ambulance_service || "108";

  return (
    <div className="max-w-md mx-auto text-center space-y-6 p-6 bg-red-50 rounded-2xl border-2 border-red-500 shadow-lg">
      <div className="w-20 h-20 bg-red-600 text-white rounded-full flex items-center justify-center mx-auto shadow-md animate-pulse">
        <HeartPulse className="w-10 h-10" />
      </div>

      <div className="space-y-2">
        <span className="inline-block px-3 py-1 bg-red-200 text-red-950 font-bold text-xs uppercase tracking-widest rounded-full">
          Immediate Medical Alert • Triage Stop
        </span>
        <h2 className="text-2xl font-black text-red-900 leading-tight">
          Please Sit Down and Rest
        </h2>
        <p className="text-base text-red-900 font-medium leading-relaxed px-2">
          {patientMsg}
        </p>
      </div>

      {/* Emergency Alert Card for Clinic Staff */}
      <div className="p-4 bg-white rounded-xl border border-red-200 text-left space-y-2 text-xs">
        <p className="font-bold text-red-950 flex items-center space-x-1.5">
          <ShieldAlert className="w-4 h-4 text-red-600" />
          <span>Staff Emergency Response Triggered</span>
        </p>
        <p className="text-slate-700">
          <b>Trigger Category:</b> {alertData?.category || 'Acute Emergency'}
        </p>
        <p className="text-slate-600 italic">
          {alertData?.reason || 'Critical symptom flagged in patient history.'}
        </p>
      </div>

      {/* Configurable Crisis Hotlines */}
      <div className="space-y-2 pt-2">
        <p className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
          National Crisis Helplines
        </p>
        <div className="grid grid-cols-2 gap-3">
          <a
            href={`tel:${helpline}`}
            className="p-3 bg-white rounded-xl border border-slate-300 shadow-sm flex flex-col items-center justify-center hover:bg-slate-50 min-h-touch"
          >
            <PhoneCall className="w-5 h-5 text-red-700 mb-1" />
            <span className="text-sm font-bold text-slate-900">Dial {helpline}</span>
            <span className="text-[10px] text-slate-500">Tele-MANAS (Mental Health)</span>
          </a>
          <a
            href={`tel:${ambulance}`}
            className="p-3 bg-white rounded-xl border border-slate-300 shadow-sm flex flex-col items-center justify-center hover:bg-slate-50 min-h-touch"
          >
            <PhoneCall className="w-5 h-5 text-red-700 mb-1" />
            <span className="text-sm font-bold text-slate-900">Dial {ambulance} / 112</span>
            <span className="text-[10px] text-slate-500">Emergency Ambulance</span>
          </a>
        </div>
      </div>

      <div className="pt-4 border-t border-red-200">
        <button
          onClick={onReset}
          className="text-xs text-red-700 hover:text-red-900 underline font-medium"
        >
          Return to Portal Home (Staff / Admin Reset)
        </button>
      </div>
    </div>
  );
}
