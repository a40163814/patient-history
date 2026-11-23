import React, { useState } from 'react';
import { Phone, QrCode, Globe, CheckCircle, ArrowRight, UserCheck } from 'lucide-react';
import { loginPatient } from '../../services/api';

export default function LoginOtp({ onLoginSuccess }) {
  const [phone, setPhone] = useState('9876543210');
  const [language, setLanguage] = useState('en'); // Defaults to English
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    if (!phone || phone.length < 10) {
      setError('Please enter a valid 10-digit mobile number');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await loginPatient(phone, language);
      // Ensure returned language reflects user's explicit choice
      data.preferred_language = language;
      onLoginSuccess(data);
    } catch (err) {
      setError('Failed to login. Please ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemoSelect = (pPhone, defaultLang) => {
    setPhone(pPhone);
    // Keep user's chosen language if they already clicked English
    if (language !== 'en') {
      setLanguage(defaultLang);
    }
  };

  return (
    <div className="max-w-md mx-auto space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold text-slate-800">Welcome to OPD Pre-Intake</h2>
        <p className="text-sm text-slate-600">
          Sign in to take your medical history before consulting the physician.
        </p>
      </div>

      {/* Language Selector */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <label className="text-xs font-semibold uppercase tracking-wider text-slate-700 flex items-center space-x-1.5">
          <Globe className="w-4 h-4 text-emerald-700" />
          <span>Select Your Language / भाषा निवडा</span>
        </label>
        <div className="grid grid-cols-3 gap-2">
          {[
            { id: 'en', label: 'English', sub: 'English' },
            { id: 'hi', label: 'हिंदी', sub: 'Hindi' },
            { id: 'mr', label: 'मराठी', sub: 'Marathi' }
          ].map((l) => (
            <button
              key={l.id}
              type="button"
              onClick={() => setLanguage(l.id)}
              className={`p-3 rounded-lg border-2 text-center transition min-h-touch flex flex-col items-center justify-center ${
                language === l.id
                  ? 'border-emerald-700 bg-emerald-50 text-emerald-950 font-bold ring-2 ring-emerald-600/30'
                  : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
              }`}
            >
              <span className="text-base">{l.label}</span>
              <span className="text-[10px] text-slate-500">{l.sub}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Phone OTP Form */}
      <form onSubmit={handleLogin} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Mobile Number / मोबाइल नंबर
          </label>
          <div className="relative">
            <Phone className="w-5 h-5 absolute left-3 top-3.5 text-slate-400" />
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="e.g. 9876543210"
              className="w-full pl-11 pr-4 py-3 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-600 focus:outline-none text-base"
              required
            />
          </div>
        </div>

        <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600 flex items-center justify-between">
          <span>Demo OTP (Auto-verified): <b>123456</b></span>
          <span className="text-emerald-700 font-medium flex items-center space-x-1">
            <CheckCircle className="w-3.5 h-3.5" />
            <span>Ready</span>
          </span>
        </div>

        {error && (
          <p className="text-xs text-red-600 font-medium bg-red-50 p-2 rounded">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-emerald-700 hover:bg-emerald-800 text-white font-semibold py-3.5 rounded-lg shadow transition flex items-center justify-center space-x-2 min-h-touch text-base"
        >
          {loading ? (
            <span>Connecting...</span>
          ) : (
            <>
              <span>Begin Intake / तपासणी सुरू करा</span>
              <ArrowRight className="w-5 h-5" />
            </>
          )}
        </button>
      </form>

      {/* Quick Synthetic Demo Patient Profiles */}
      <div className="bg-slate-100 p-4 rounded-xl border border-slate-200 text-xs space-y-2">
        <p className="font-semibold text-slate-700 flex items-center space-x-1">
          <UserCheck className="w-4 h-4 text-emerald-700" />
          <span>Quick Demo Profiles (Click to Auto-fill):</span>
        </p>
        <div className="grid grid-cols-3 gap-2">
          <button
            type="button"
            onClick={() => handleQuickDemoSelect('9876543210', 'hi')}
            className="p-2 bg-white rounded border border-slate-200 hover:border-emerald-600 text-left"
          >
            <p className="font-bold text-slate-800">Ramesh</p>
            <p className="text-[10px] text-slate-500">Joint Stiffness</p>
          </button>
          <button
            type="button"
            onClick={() => handleQuickDemoSelect('9823456789', 'mr')}
            className="p-2 bg-white rounded border border-slate-200 hover:border-amber-600 text-left"
          >
            <p className="font-bold text-slate-800">Sunita</p>
            <p className="text-[10px] text-amber-700 font-medium">Lab Mismatch</p>
          </button>
          <button
            type="button"
            onClick={() => handleQuickDemoSelect('9123456780', 'en')}
            className="p-2 bg-white rounded border border-slate-200 hover:border-red-600 text-left"
          >
            <p className="font-bold text-slate-800">Vijay</p>
            <p className="text-[10px] text-red-700 font-medium">Red-Flag Alert</p>
          </button>
        </div>
      </div>
    </div>
  );
}
