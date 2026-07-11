import React from 'react';

export default function OperatorDashboard({ viewData, severity }) {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="border border-slate-800 bg-slate-950 p-4 rounded-lg">
        <h2 className="text-xs font-mono tracking-wider text-slate-400 uppercase">Current Station Status</h2>
        <div className="mt-2 flex items-center space-x-4">
          <div className="text-sm font-mono font-bold">SYSTEM STATUS:</div>
          <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${
            severity === 'CRITICAL' ? 'bg-red-950 text-red-400 border border-red-800' :
            severity === 'WARNING' ? 'bg-amber-950 text-amber-400 border border-amber-800' :
            'bg-slate-900 text-slate-400 border border-slate-700'
          }`}>
            {severity}
          </span>
        </div>
      </div>

      {/* Live AI Command Directive Module */}
      <div className="border border-slate-800 bg-slate-950 rounded-lg overflow-hidden">
        <div className="border-b border-slate-800 bg-slate-900/50 px-4 py-3">
          <h3 className="text-xs font-mono tracking-wider text-slate-300">Autonomous Guidance Terminal</h3>
        </div>
        <div className="p-6 space-y-4">
          {viewData.banner && (
            <div className={`p-4 rounded border text-sm font-mono font-bold ${
              severity === 'CRITICAL' ? 'bg-red-950/30 border-red-900 text-red-400' : 'bg-blue-950/30 border-blue-900 text-blue-400'
            }`}>
              {viewData.banner}
            </div>
          )}
          <div className="bg-slate-900 p-4 rounded border border-slate-800">
            <h4 className="text-xs font-mono text-slate-500 uppercase">Required Action</h4>
            <p className="mt-2 text-sm font-mono text-slate-200 leading-relaxed">
              {viewData.instruction || "Monitoring baseline queue flows. No manual adjustments required at this timestamp."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}