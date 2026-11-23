import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, CheckCircle, Edit3, Save, X, FileText, 
  Download, AlertTriangle, ShieldAlert, Sparkles, Image as ImageIcon 
} from 'lucide-react';
import { fetchCaseSheet, editCaseField, approveCaseSheet } from '../../services/api';

export default function CaseReview({ sessionId, onBackToQueue }) {
  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editingFieldId, setEditingFieldId] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [doctorNotes, setDoctorNotes] = useState('');
  const [aiSummary, setAiSummary] = useState('');
  const [approving, setApproving] = useState(false);
  const [pdfUrl, setPdfUrl] = useState(null);

  const loadCase = async () => {
    setLoading(true);
    try {
      const data = await fetchCaseSheet(sessionId);
      setCaseData(data);
      setDoctorNotes(data.doctor_notes || '');
      setAiSummary(data.ai_summary || '');
      if (data.is_doctor_approved && data.session_id) {
        setPdfUrl(`/api/v1/doctor/case/${data.session_id}/pdf`);
      }
    } catch (err) {
      console.error('Failed to load case sheet:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCase();
  }, [sessionId]);

  const handleStartEdit = (field) => {
    setEditingFieldId(field.id);
    setEditValue(field.value);
  };

  const handleSaveFieldEdit = async (fieldId) => {
    try {
      await editCaseField(sessionId, fieldId, editValue, 'Doctor inline edit');
      setEditingFieldId(null);
      await loadCase(); // refresh with audit logs
    } catch (err) {
      console.error('Edit error:', err);
    }
  };

  const handleApproveCase = async () => {
    setApproving(true);
    try {
      const res = await approveCaseSheet(sessionId, doctorNotes, aiSummary);
      setPdfUrl(res.pdf_download_url);
      await loadCase();
    } catch (err) {
      console.error('Approval failed:', err);
    } finally {
      setApproving(false);
    }
  };

  if (loading) {
    return <div className="text-center p-12 text-slate-400 animate-pulse">Loading case sheet...</div>;
  }

  if (!caseData) {
    return <div className="text-center p-12 text-red-500">Case not found.</div>;
  }

  const sections = caseData.sections || {};
  const reports = caseData.reports || [];

  return (
    <div className="space-y-6">
      {/* Top Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <button
          onClick={onBackToQueue}
          className="flex items-center space-x-1.5 text-xs font-semibold text-slate-700 hover:text-emerald-800 transition min-h-touch"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to OPD Queue</span>
        </button>

        <div className="flex items-center space-x-3">
          {pdfUrl && (
            <a
              href={pdfUrl}
              target="_blank"
              rel="noreferrer"
              className="px-4 py-2 bg-emerald-50 text-emerald-800 hover:bg-emerald-100 font-bold rounded-lg border border-emerald-300 flex items-center space-x-1.5 text-xs transition min-h-touch"
            >
              <Download className="w-4 h-4" />
              <span>Download Stamped PDF</span>
            </a>
          )}

          <button
            onClick={handleApproveCase}
            disabled={approving || caseData.is_doctor_approved}
            className={`px-5 py-2 font-bold rounded-lg flex items-center space-x-1.5 text-xs transition min-h-touch ${
              caseData.is_doctor_approved
                ? 'bg-emerald-100 text-emerald-900 border border-emerald-400 cursor-default'
                : 'bg-emerald-700 hover:bg-emerald-800 text-white shadow'
            }`}
          >
            <CheckCircle className="w-4 h-4" />
            <span>{caseData.is_doctor_approved ? 'Doctor Approved' : approving ? 'Generating PDF...' : 'Approve & Stamp PDF'}</span>
          </button>
        </div>
      </div>

      {/* Mandatory Disclaimer */}
      <div className="p-3 bg-red-50 border border-red-300 rounded-lg text-center text-xs font-semibold text-red-900">
        MANDATORY NOTICE: Draft prepared from patient answers. Not a diagnosis. Evaluated by examining physician.
      </div>

      {/* Header Info Card */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Patient Token</span>
          <p className="text-base font-bold text-slate-900">{caseData.patient_token}</p>
          <p className="text-xs text-slate-500">Phone: {caseData.phone_number}</p>
          <p className="text-xs text-slate-500">Language: {caseData.preferred_language.toUpperCase()}</p>
        </div>

        <div>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Discipline & Status</span>
          <p className="text-base font-bold text-emerald-800 capitalize">{caseData.ayush_system} OPD</p>
          <p className="text-xs text-slate-600">Status: <span className="font-semibold">{caseData.status}</span></p>
          <p className="text-xs text-slate-500">Guardian: {caseData.is_guardian_mode ? `${caseData.guardian_name} (${caseData.guardian_relation})` : 'Self'}</p>
        </div>

        <div>
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Vitals</span>
            <span className="text-[10px] bg-amber-100 text-amber-900 px-2 py-0.5 rounded font-bold uppercase">
              {caseData.vitals_label}
            </span>
          </div>
          <p className="text-sm font-semibold text-slate-800 mt-1">
            {caseData.height_cm || '—'} cm | {caseData.weight_kg || '—'} kg
          </p>
          <p className="text-xs text-slate-700">
            BMI: <b>{caseData.bmi || '—'} kg/m²</b> ({caseData.bmi_category || '—'})
          </p>
        </div>
      </div>

      {/* Red-Flag and Mismatch Banners */}
      {caseData.has_red_flag && (
        <div className="p-4 bg-red-100 border-2 border-red-500 rounded-xl flex items-start space-x-3 text-red-950">
          <ShieldAlert className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-black text-sm uppercase tracking-wider">CRITICAL TRIAGE ALERT: {caseData.red_flag_category}</p>
            <p className="text-xs leading-relaxed">{caseData.red_flag_details}</p>
          </div>
        </div>
      )}

      {/* Main Two-Column Layout: Clinical Fields + Uploaded Reports Side-by-Side */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Clinical Fields (2/3 width) */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
            Patient Disclosures with Provenance & Transcript Quotes
          </h3>

          {Object.entries(sections).map(([secKey, fields]) => (
            <div key={secKey} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
              <h4 className="text-xs font-bold text-emerald-800 uppercase tracking-wider border-b border-slate-100 pb-2">
                {secKey.replace(/_/g, ' ').toUpperCase()}
              </h4>

              <div className="space-y-3">
                {fields.map((f) => {
                  const isEditing = editingFieldId === f.id;

                  return (
                    <div key={f.id} className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-700">{f.field_label || f.field_key}</span>
                        <div className="flex items-center space-x-2">
                          {/* Provenance Chip */}
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                            f.source === 'patient_said' ? 'bg-blue-100 text-blue-800' :
                            f.source === 'from_report' ? 'bg-purple-100 text-purple-800' :
                            f.source === 'unclear' ? 'bg-amber-100 text-amber-800' :
                            'bg-slate-200 text-slate-700'
                          }`}>
                            {f.source}
                          </span>

                          {!isEditing && (
                            <button
                              onClick={() => handleStartEdit(f)}
                              className="text-slate-400 hover:text-emerald-700 p-1"
                              title="Edit field"
                            >
                              <Edit3 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Value or Inline Edit Box */}
                      {isEditing ? (
                        <div className="space-y-2 pt-1">
                          <textarea
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            className="w-full p-2 border border-emerald-600 rounded bg-white text-xs text-slate-900 focus:outline-none"
                            rows="2"
                          />
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => handleSaveFieldEdit(f.id)}
                              className="px-3 py-1 bg-emerald-700 text-white rounded text-xs font-semibold flex items-center space-x-1"
                            >
                              <Save className="w-3 h-3" />
                              <span>Save & Log Audit</span>
                            </button>
                            <button
                              onClick={() => setEditingFieldId(null)}
                              className="px-2 py-1 text-slate-500 hover:text-slate-700"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <p className="text-sm font-semibold text-slate-900 leading-snug">
                          {f.value}
                        </p>
                      )}

                      {/* Doctor Edit Notice */}
                      {f.is_edited_by_doctor && (
                        <p className="text-[10px] text-red-600 font-medium">
                          [Doctor Modified: Originally was "{f.original_value}"]
                        </p>
                      )}

                      {/* Linked Transcript Quote */}
                      {f.transcript_quote && (
                        <p className="text-[11px] text-slate-500 italic border-l-2 border-slate-300 pl-2">
                          "{f.transcript_quote}"
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}

          {/* AI-Generated Summary (Max 5 lines, Doctor Editable) */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-2">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-emerald-700" />
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                AI-Generated Summary (Doctor Reviewable & Editable)
              </h4>
            </div>
            <textarea
              value={aiSummary}
              onChange={(e) => setAiSummary(e.target.value)}
              rows="4"
              className="w-full p-3 text-xs border border-slate-300 rounded-lg text-slate-800 font-sans leading-relaxed focus:ring-1 focus:ring-emerald-600"
              placeholder="Summary generated from transcript reconciliation..."
            />
          </div>

          {/* Doctor Assessment & Clinical Notes */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-2">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Doctor Clinical Assessment & Prescription Plan
            </h4>
            <textarea
              value={doctorNotes}
              onChange={(e) => setDoctorNotes(e.target.value)}
              rows="3"
              className="w-full p-3 text-xs border border-slate-300 rounded-lg text-slate-900 focus:ring-1 focus:ring-emerald-600"
              placeholder="Enter official clinical notes, Chikitsa sutra, advice, or follow-up instructions..."
            />
          </div>
        </div>

        {/* Right Column: Original Uploaded Reports Side-by-Side (1/3 width) */}
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
            Diagnostic Reports & OCR Evidence
          </h3>

          {reports.length === 0 ? (
            <div className="bg-white p-6 rounded-xl border border-slate-200 text-center text-xs text-slate-400">
              No reports uploaded for this session.
            </div>
          ) : (
            reports.map((rep, idx) => (
              <div key={idx} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3 text-xs">
                <div className="flex items-center space-x-2 font-bold text-slate-800 border-b border-slate-100 pb-2">
                  <FileText className="w-4 h-4 text-emerald-700" />
                  <span className="truncate">{rep.file_name}</span>
                </div>

                {/* Mismatch Alert Box */}
                {rep.mismatch_flags?.length > 0 && (
                  <div className="p-2.5 bg-amber-50 rounded-lg border border-amber-300 text-amber-900 font-medium space-y-1">
                    <p className="font-bold flex items-center space-x-1 text-[11px]">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
                      <span>Report Discrepancy Identified:</span>
                    </p>
                    {rep.mismatch_flags.map((m, mIdx) => (
                      <p key={mIdx} className="text-[11px] leading-tight">• {m.message}</p>
                    ))}
                  </div>
                )}

                {/* Extracted Lab Values Table */}
                <div className="space-y-1">
                  <p className="font-bold text-slate-600 text-[10px] uppercase">Extracted Readings:</p>
                  {rep.lab_values?.map((lv, lIdx) => (
                    <div key={lIdx} className="p-2 bg-slate-50 rounded border border-slate-100 flex items-center justify-between">
                      <span className="font-semibold text-slate-800">{lv.test_name}</span>
                      <span className="font-bold text-slate-900">{lv.raw_value}</span>
                    </div>
                  ))}
                </div>

                <div className="text-[10px] text-slate-400 italic">
                  Non-diagnostic transcription. Values extracted for physician verification.
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
