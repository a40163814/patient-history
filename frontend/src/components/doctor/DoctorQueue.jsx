import React, { useState, useEffect } from 'react';
import { 
  Users, AlertTriangle, FileWarning, CheckCircle, Clock, 
  RotateCcw, ArrowRight, ShieldAlert, Sparkles 
} from 'lucide-react';
import { fetchDoctorQueue, resetAndSeedDemo } from '../../services/api';

export default function DoctorQueue({ onSelectCase }) {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // 'all' | 'alerts' | 'mismatches'
  const [resetting, setResetting] = useState(false);

  const loadQueue = async () => {
    setLoading(true);
    try {
      const data = await fetchDoctorQueue();
      setQueue(data.queue || []);
    } catch (err) {
      console.error('Queue load failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const handleResetDemo = async () => {
    setResetting(true);
    try {
      await resetAndSeedDemo();
      await loadQueue();
    } catch (err) {
      console.error('Reset failed:', err);
    } finally {
      setResetting(false);
    }
  };

  const filteredQueue = queue.filter((item) => {
    if (filter === 'alerts') return item.has_red_flag;
    if (filter === 'mismatches') return item.mismatch_count > 0;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Dashboard Header & 1-Click Reset */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-xl font-bold text-slate-800">Ayush OPD Patient Queue</h2>
            <span className="px-2.5 py-0.5 bg-emerald-100 text-emerald-800 text-xs font-bold rounded-full">
              {queue.length} Active
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Priority sorted: Emergency triage alerts appear top priority, followed by lab mismatch flags.
          </p>
        </div>

        <button
          onClick={handleResetDemo}
          disabled={resetting}
          className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-lg border border-slate-300 flex items-center space-x-2 transition min-h-touch self-start md:self-auto"
        >
          <RotateCcw className={`w-4 h-4 ${resetting ? 'animate-spin' : ''}`} />
          <span>{resetting ? 'Resetting...' : '1-Click Reset & Seed (3 Demo Patients)'}</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-200 pb-2">
        {[
          { id: 'all', label: `All Patients (${queue.length})` },
          { id: 'alerts', label: `Red-Flag Alerts (${queue.filter(q => q.has_red_flag).length})` },
          { id: 'mismatches', label: `Lab Discrepancies (${queue.filter(q => q.mismatch_count > 0).length})` }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setFilter(tab.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              filter === tab.id
                ? 'bg-emerald-800 text-white'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Queue List */}
      {loading ? (
        <div className="text-center p-12 text-slate-400 animate-pulse">Loading priority queue...</div>
      ) : filteredQueue.length === 0 ? (
        <div className="bg-white p-8 rounded-xl border border-slate-200 text-center text-sm text-slate-500">
          No patient records match the selected filter.
        </div>
      ) : (
        <div className="space-y-3">
          {filteredQueue.map((item) => {
            const isRedFlag = item.has_red_flag;
            const hasMismatch = item.mismatch_count > 0;

            return (
              <div
                key={item.session_id}
                onClick={() => onSelectCase(item.session_id)}
                className={`p-4 rounded-xl border transition cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm hover:shadow-md ${
                  isRedFlag
                    ? 'bg-red-50/60 border-red-300 hover:border-red-500'
                    : hasMismatch
                    ? 'bg-amber-50/50 border-amber-300 hover:border-amber-500'
                    : 'bg-white border-slate-200 hover:border-emerald-600'
                }`}
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-slate-900 text-sm">
                      {item.patient_token}
                    </span>
                    <span className="text-xs text-slate-500">({item.phone_number})</span>

                    {/* Ayush Discipline Chip */}
                    <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                      {item.ayush_system}
                    </span>

                    {/* Language Badge */}
                    <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-slate-200 text-slate-800">
                      {item.language}
                    </span>
                  </div>

                  {/* Priority Badges */}
                  <div className="flex flex-wrap items-center gap-2">
                    {isRedFlag && (
                      <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-red-600 text-white animate-pulse">
                        <ShieldAlert className="w-3.5 h-3.5" />
                        <span>CRITICAL: {item.red_flag_category || 'Red-Flag Alert'}</span>
                      </span>
                    )}

                    {hasMismatch && (
                      <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500 text-white">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span>{item.mismatch_count} Lab Mismatch(es)</span>
                      </span>
                    )}

                    {item.is_approved && (
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-100 text-emerald-800">
                        <CheckCircle className="w-3 h-3" />
                        <span>Doctor Approved</span>
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-3 text-xs">
                  <div className="text-right text-slate-400">
                    <p>Status: <span className="font-medium text-slate-700">{item.status}</span></p>
                    <p>{new Date(item.started_at).toLocaleTimeString()}</p>
                  </div>
                  <button className="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white font-semibold rounded-lg flex items-center space-x-1 min-h-touch">
                    <span>Review Case</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
