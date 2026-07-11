import React from 'react';

export default function AdminDashboard({ viewData, severity, dispatchMode }) {
  const isCriticalPending = dispatchMode === 'MANUAL_PENDING';
  const isBypassActive = dispatchMode === 'AUTO_EMERGENCY_BYPASS';
  const isWarningPending = dispatchMode === 'MANUAL';

  return (
    <div className="relative min-h-[80vh] w-full">
      {/* Underlying Baseline Monitor Display */}
      <div className={`space-y-6 transition-filter duration-300 ${(isCriticalPending || isWarningPending) ? 'blur-sm pointer-events-none select-none' : ''}`}>
        <div className="border border-slate-800 bg-slate-950 p-6 rounded-lg">
          <h2 className="text-xs font-mono tracking-wider text-slate-400 uppercase">Executive Overview</h2>
          <p className="mt-4 text-sm text-slate-300 font-mono">
            {viewData.log_summary || "Autonomous Background Agent is balancing terminal operations."}
          </p>
        </div>
      </div>

      {/* CRITICAL INCIDENT OVERLAY: 20-Second Escalation Window Module */}
      {isCriticalPending && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm z-50">
          <div className="w-full max-w-xl border border-red-900 bg-slate-950 rounded-lg shadow-2xl overflow-hidden animate-fadeIn">
            <div className="bg-red-950 border-b border-red-900 px-4 py-3 flex justify-between items-center">
              <span className="text-xs font-mono tracking-widest font-bold text-red-400 uppercase">{viewData.pop_up_title}</span>
              <span className="px-2 py-0.5 rounded bg-red-900 text-white font-mono text-xs font-bold animate-pulse">
                TIMEOUT: {viewData.countdown_seconds}s
              </span>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-sm font-mono text-slate-300">{viewData.description}</p>
              <div className="bg-slate-900 p-4 rounded border border-slate-800">
                <span className="text-xs font-mono text-slate-500 uppercase">Proposed Mitigation Order</span>
                <p className="mt-1 text-sm font-mono text-red-200 font-bold">{viewData.proposed_action}</p>
              </div>
              <div className="flex space-x-3 pt-2">
                <button className="flex-1 bg-red-700 hover:bg-red-600 text-white font-mono text-xs font-bold py-2.5 rounded transition-colors uppercase">
                  Approve Deployment
                </button>
                <button className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs py-2.5 rounded transition-colors uppercase">
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CRITICAL BYPASS ALERT: Appears when Admin exceeds 20-second timeout */}
      {isBypassActive && (
        <div className="mt-6 border border-red-900 bg-red-950/20 p-6 rounded-lg">
          <h3 className="text-sm font-mono font-bold text-red-400 uppercase">{viewData.alert}</h3>
          <p className="mt-2 text-sm font-mono text-slate-300 leading-relaxed">{viewData.details}</p>
        </div>
      )}

      {/* MEDIUM INCIDENT OVERLAY: Compounding Bottleneck Authorization */}
      {isWarningPending && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm z-50">
          <div className="w-full max-w-xl border border-amber-900 bg-slate-950 rounded-lg shadow-2xl overflow-hidden">
            <div className="bg-amber-950 border-b border-amber-900 px-4 py-3">
              <span className="text-xs font-mono tracking-widest font-bold text-amber-400 uppercase">{viewData.pop_up_title}</span>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-sm font-mono text-slate-300">{viewData.description}</p>
              <div className="bg-slate-900 p-4 rounded border border-slate-800">
                <span className="text-xs font-mono text-slate-500 uppercase">Proposed Countermeasures</span>
                <p className="mt-1 text-sm font-mono text-amber-200 font-bold">{viewData.proposed_action}</p>
              </div>
              <div className="flex space-x-3 pt-2">
                <button className="flex-1 bg-amber-700 hover:bg-amber-600 text-slate-950 font-mono text-xs font-bold py-2.5 rounded transition-colors uppercase">
                  Execute Redistribution
                </button>
                <button className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs py-2.5 rounded transition-colors uppercase">
                  Decline
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}