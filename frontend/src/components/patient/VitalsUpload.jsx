import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle2, ArrowRight, AlertTriangle, Sparkles, X, Check, Trash2, Plus } from 'lucide-react';
import { submitVitals, uploadReportFile, uploadMultipleReportFiles } from '../../services/api';

export default function VitalsUpload({ patient, session, onVitalsCompleted }) {
  const [height, setHeight] = useState('170');
  const [weight, setWeight] = useState('68');
  const [ayushSystem] = useState('allopathy');
  const [uploading, setUploading] = useState(false);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const fileInputRef = useRef(null);

  // Live BMI calculation in code
  const hNum = parseFloat(height);
  const wNum = parseFloat(weight);
  const bmi = (hNum > 0 && wNum > 0) ? (wNum / Math.pow(hNum / 100, 2)).toFixed(1) : '—';
  
  let bmiCategory = '—';
  let bmiColor = 'text-slate-600';
  if (bmi !== '—') {
    const b = parseFloat(bmi);
    if (b < 18.5) { bmiCategory = 'Underweight'; bmiColor = 'text-blue-600'; }
    else if (b <= 22.9) { bmiCategory = 'Normal'; bmiColor = 'text-emerald-700'; }
    else if (b <= 24.9) { bmiCategory = 'Overweight'; bmiColor = 'text-amber-700'; }
    else { bmiCategory = 'Obese'; bmiColor = 'text-red-700'; }
  }

  const [uploadStatus, setUploadStatus] = useState('');

  const handleFileUpload = async (e) => {
    const fileList = e.target.files;
    if (!fileList || fileList.length === 0) return;

    const filesToUpload = Array.from(fileList);
    setUploading(true);
    setError(null);
    setUploadStatus(`Uploading ${filesToUpload.length} document${filesToUpload.length > 1 ? 's' : ''}...`);

    try {
      if (filesToUpload.length === 1) {
        const data = await uploadReportFile(patient.patient_token, session.session_id, filesToUpload[0]);
        setReports((prev) => [...prev, data]);
      } else {
        const dataList = await uploadMultipleReportFiles(patient.patient_token, session.session_id, filesToUpload);
        setReports((prev) => [...prev, ...dataList]);
      }
      setUploadStatus('');
    } catch (err) {
      console.error('File upload error:', err);
      setError('Report upload failed. You can continue without reports or try another file.');
    } finally {
      setUploading(false);
      setUploadStatus('');
      if (e.target) e.target.value = '';
    }
  };

  const handleRemoveReport = (indexToRemove) => {
    setReports((prev) => prev.filter((_, idx) => idx !== indexToRemove));
  };

  const handleSaveAndContinue = async () => {
    if (!height || !weight || parseFloat(height) <= 30 || parseFloat(weight) <= 1) {
      setError('Please provide valid height and weight');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const vData = await submitVitals(
        patient.patient_token,
        height,
        weight,
        ayushSystem,
        session?.session_id
      );
      onVitalsCompleted({
        height_cm: vData.height_cm,
        weight_kg: vData.weight_kg,
        bmi: vData.bmi,
        bmi_category: vData.bmi_category,
        ayush_system: ayushSystem,
        reports
      });
    } catch (err) {
      console.error('Vitals submission error:', err);
      setError(err?.message || 'Failed to record vitals. Please check connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <div className="text-center space-y-1">
        <h2 className="text-2xl font-bold text-slate-800">Vitals & Optional Reports</h2>
        <p className="text-xs text-slate-500">
          Enter your basic measurements. Diagnostic reports are completely optional.
        </p>
      </div>

      {/* Height & Weight Inputs with Code-Computed BMI */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-slate-800">Physical Measurements</h3>
          <span className="px-2.5 py-1 bg-amber-100 text-amber-900 text-[11px] font-semibold rounded-full uppercase">
            Self-Reported
          </span>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">
              Height / कद (cm)
            </label>
            <input
              type="number"
              value={height}
              onChange={(e) => setHeight(e.target.value)}
              placeholder="e.g. 170"
              className="w-full px-3 py-3 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-600 focus:outline-none text-base"
              min="50"
              max="250"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">
              Weight / वजन (kg)
            </label>
            <input
              type="number"
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              placeholder="e.g. 68"
              className="w-full px-3 py-3 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-600 focus:outline-none text-base"
              min="10"
              max="250"
            />
          </div>
        </div>

        {/* Real-time Computed BMI Display */}
        <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-500">Computed Body Mass Index (BMI):</p>
            <p className="text-lg font-bold text-slate-800">
              {bmi} <span className="text-xs font-normal text-slate-500">kg/m²</span>
            </p>
          </div>
          <div className="text-right">
            <span className={`text-sm font-bold ${bmiColor}`}>
              {bmiCategory}
            </span>
            <p className="text-[10px] text-slate-400">Formula: weight / (height_m)²</p>
          </div>
        </div>
      </div>

      {/* Diagnostic Report Upload (Explicitly Optional) */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-base font-semibold text-slate-800">Upload Reports or Prescriptions</h3>
              <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 text-[10px] font-bold rounded uppercase">
                Optional
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              If you don't have reports right now, you can skip this step completely.
            </p>
          </div>
        </div>

        {/* Hidden Reliable File Input with Multiple File Support */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="application/pdf,image/*,.pdf,.jpg,.jpeg,.png"
          onChange={handleFileUpload}
          style={{ display: 'none' }}
        />

        {/* Upload Trigger Button / Dropzone */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="border-2 border-dashed border-slate-300 hover:border-emerald-600 rounded-xl p-5 flex flex-col items-center justify-center cursor-pointer bg-slate-50 hover:bg-emerald-50/40 transition w-full min-h-[110px]"
        >
          <Upload className="w-8 h-8 text-emerald-700 mb-1" />
          <span className="text-sm font-semibold text-slate-800">
            {uploading ? (uploadStatus || 'Processing Documents...') : (reports.length > 0 ? '+ Add More Reports / Photos' : 'Tap to Select One or Multiple Files')}
          </span>
          <span className="text-xs text-slate-400 mt-0.5">Select multiple PDFs, lab reports, or prescription photos at once</span>
        </button>

        {uploading && (
          <p className="text-xs text-emerald-700 font-medium text-center animate-pulse">
            {uploadStatus || 'Transcribing documents without diagnosis...'}
          </p>
        )}

        {/* Extracted Reports Display */}
        {reports.length > 0 && (
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between">
              <p className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Attached Reports ({reports.length}):
              </p>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="text-xs text-emerald-700 font-bold hover:underline flex items-center space-x-1"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add another</span>
              </button>
            </div>
            {reports.map((rep, idx) => (
              <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2 text-xs">
                <div className="flex items-center justify-between font-medium text-slate-800">
                  <span className="flex items-center space-x-1.5 truncate">
                    <FileText className="w-4 h-4 text-emerald-700 flex-shrink-0" />
                    <span className="truncate">{rep.file_name}</span>
                  </span>
                  <div className="flex items-center space-x-2 flex-shrink-0">
                    <span className="text-emerald-700 flex items-center space-x-1 text-[11px]">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Uploaded</span>
                    </span>
                    <button
                      type="button"
                      onClick={() => handleRemoveReport(idx)}
                      title="Remove this report"
                      className="p-1 text-slate-400 hover:text-red-600 rounded transition"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {rep.lab_values?.length > 0 && (
                  <div className="pl-5 space-y-1">
                    {rep.lab_values.map((lv, lIdx) => (
                      <p key={lIdx} className="text-slate-600">
                        • <b>{lv.test_name}:</b> {lv.raw_value}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {error && (
        <p className="text-xs text-red-600 font-medium bg-red-50 p-2.5 rounded-lg border border-red-200">
          {error}
        </p>
      )}

      {/* Primary Action Button */}
      <button
        onClick={handleSaveAndContinue}
        disabled={loading}
        className="w-full bg-emerald-700 hover:bg-emerald-800 text-white font-semibold py-3.5 rounded-lg shadow transition flex items-center justify-center space-x-2 min-h-touch text-base"
      >
        {loading ? (
          <span>Saving Vitals...</span>
        ) : (
          <>
            <span>
              {reports.length > 0 
                ? `Proceed to Voice Interview (${reports.length} report attached)` 
                : 'Proceed to Voice Interview (Without Reports)'}
            </span>
            <ArrowRight className="w-5 h-5" />
          </>
        )}
      </button>
    </div>
  );
}
