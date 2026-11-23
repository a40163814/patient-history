import React, { useState, useEffect } from 'react';
import { Check, X, Edit2, Send, CheckCircle2, ShieldCheck, ArrowRight, ArrowLeft } from 'lucide-react';
import { fetchPatientReview, submitFinalIntake } from '../../services/api';

export default function PatientReview({ patient, session, onSubmittedToQueue, onBackToSummary }) {
  const [reviewData, setReviewData] = useState(null);
  const [confirmations, setConfirmations] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchPatientReview(patient.patient_token, session.session_id);
        setReviewData(data);
      } catch (err) {
        console.error('Failed to load review:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleToggleConfirm = (fieldId, isOk) => {
    setConfirmations((prev) => ({
      ...prev,
      [fieldId]: isOk
    }));
  };

  const handleSubmit = async () => {
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
      <div className="text-center p-12 text-slate-500">
        <p className="animate-pulse">Loading review summary...</p>
      </div>
    );
  }

  const sections = reviewData?.sections || {};

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <div className="text-center space-y-1">
        <div className="inline-flex p-2.5 bg-emerald-100 text-emerald-800 rounded-full mb-1">
          <CheckCircle2 className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-slate-800">Review Your Answers</h2>
        <p className="text-xs text-slate-500">
          Step 6 of 7: Please confirm what our assistant understood before sending it to the doctor.
        </p>
      </div>

      <div className="space-y-4">
        {Object.keys(sections).length === 0 ? (
          <div className="p-6 bg-white rounded-xl border border-slate-200 text-center text-sm text-slate-500">
            No fields recorded. You can still submit your queue ticket to the doctor.
          </div>
        ) : (
          Object.entries(sections).map(([secKey, fields]) => (
            <div key={secKey} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-800 border-b border-slate-100 pb-1.5">
                {secKey.replace(/_/g, ' ').toUpperCase()}
              </h3>

              <div className="space-y-3">
                {fields.map((f) => {
                  const isConfirmed = confirmations[f.id] !== false; // defaults to true
                  return (
                    <div key={f.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-start justify-between space-x-3">
                      <div className="flex-1 space-y-1">
                        <p className="text-xs font-semibold text-slate-600">
                          {f.field_key.replace(/_/g, ' ').title || f.field_key}
                        </p>
                        <p className="text-sm font-bold text-slate-900 leading-snug">
                          {f.value}
                        </p>
                        {f.quote && (
                          <p className="text-[11px] text-slate-500 italic">
                            "{f.quote}"
                          </p>
                        )}
                        <span className="inline-block text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded font-medium">
                          Source: {f.source}
                        </span>
                      </div>

                      {/* Large Yes / No Icon Buttons */}
                      <div className="flex items-center space-x-1.5 pt-1">
                        <button
                          type="button"
                          onClick={() => handleToggleConfirm(f.id, true)}
                          title="Correct"
                          className={`w-11 h-11 rounded-lg border flex items-center justify-center transition ${
                            isConfirmed
                              ? 'bg-emerald-700 text-white border-emerald-800 shadow'
                              : 'bg-white text-slate-400 border-slate-200 hover:border-slate-300'
                          }`}
                        >
                          <Check className="w-6 h-6 stroke-[3]" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleToggleConfirm(f.id, false)}
                          title="Incorrect or Edit"
                          className={`w-11 h-11 rounded-lg border flex items-center justify-center transition ${
                            !isConfirmed
                              ? 'bg-red-600 text-white border-red-700 shadow'
                              : 'bg-white text-slate-400 border-slate-200 hover:border-slate-300'
                          }`}
                        >
                          <X className="w-6 h-6 stroke-[3]" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))
        )}
      </div>

      <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-xs text-emerald-950 flex items-center space-x-2">
        <ShieldCheck className="w-5 h-5 text-emerald-700 flex-shrink-0" />
        <span>Your answers will be securely transferred to the doctor's queue.</span>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        {onBackToSummary && (
          <button
            type="button"
            onClick={onBackToSummary}
            className="sm:w-1/3 py-3.5 px-4 rounded-xl bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-bold text-sm shadow-sm flex items-center justify-center space-x-1.5 transition"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Summary</span>
          </button>
        )}
        <button
          onClick={handleSubmit}
          disabled={submitting}
          className="flex-1 bg-emerald-700 hover:bg-emerald-800 text-white font-bold py-3.5 px-4 rounded-xl shadow-lg transition flex items-center justify-center space-x-2 min-h-touch text-base"
        >
          {submitting ? (
            <span>Submitting to Doctor...</span>
          ) : (
            <>
              <span>Submit to Doctor Queue / डॉक्टरांकडे पाठवा</span>
              <Send className="w-5 h-5" />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
