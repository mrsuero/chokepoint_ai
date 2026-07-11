import React from 'react';

export default function OperatorDashboard({ viewData, severity, metricsData }) {
  const queueDensity = metricsData?.current_queue_density ?? 0;
  const avgWaitTime = metricsData?.avg_wait_time_minutes ?? 0;
  const avgProcessingTime = metricsData?.avg_processing_time_minutes ?? 0;
  const accumulationRate = metricsData?.accumulation_rate_per_min ?? 0;
  const luggageThresholdMinutes = metricsData?.luggage_stationary_threshold_minutes ?? 10;
  const zoneAnalysis = metricsData?.zone_analysis ?? {};
  const waitingCount = zoneAnalysis?.zone_1_people_count ?? 0;
  const checkInCount = zoneAnalysis?.zone_2_people_count ?? 0;
  const trendStatus = metricsData?.trend_analysis?.proc_time_slope ?? 'STABLE';

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

      <div className="grid grid-cols-2 gap-3">
        <div className="border border-slate-800 bg-slate-950 p-4 rounded-lg">
          <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Queue Density</div>
          <div className="mt-2 text-2xl font-bold text-emerald-400 font-mono">{queueDensity}</div>
          <div className="text-xs text-slate-400 font-mono">Passengers currently in queue zone</div>
        </div>
        <div className="border border-slate-800 bg-slate-950 p-4 rounded-lg">
          <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Avg Wait Time</div>
          <div className="mt-2 text-2xl font-bold text-slate-100 font-mono">{avgWaitTime.toFixed(1)}m</div>
          <div className="text-xs text-slate-400 font-mono">Estimated passenger waiting time</div>
        </div>
        <div className="border border-slate-800 bg-slate-950 p-4 rounded-lg">
          <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Avg Processing</div>
          <div className="mt-2 text-2xl font-bold text-slate-100 font-mono">{avgProcessingTime.toFixed(1)}m</div>
          <div className="text-xs text-slate-400 font-mono">Counter-side processing time</div>
        </div>
        <div className="border border-slate-800 bg-slate-950 p-4 rounded-lg">
          <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Accumulation</div>
          <div className="mt-2 text-2xl font-bold text-slate-100 font-mono">{accumulationRate.toFixed(2)}</div>
          <div className="text-xs text-slate-400 font-mono">Passengers per minute</div>
        </div>
        <div className="border border-slate-800 bg-slate-950 p-4 rounded-lg">
          <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Luggage Threshold</div>
          <div className="mt-2 text-2xl font-bold text-amber-400 font-mono">{luggageThresholdMinutes}m</div>
          <div className="text-xs text-slate-400 font-mono">Stationary luggage before suspicion</div>
        </div>
      </div>

      <div className="border border-slate-800 bg-slate-950 p-4 rounded-lg">
        <h3 className="text-xs font-mono tracking-wider text-slate-400 uppercase">Zone Split</h3>
        <div className="mt-3 grid grid-cols-2 gap-3 text-sm font-mono">
          <div className="rounded border border-slate-800 bg-slate-900/80 p-3">
            <div className="text-[10px] uppercase tracking-widest text-slate-500">Zone 1</div>
            <div className="mt-1 text-slate-100 font-bold">Check-in Area</div>
            <div className="mt-1 text-slate-400">People: {waitingCount}</div>
          </div>
          <div className="rounded border border-slate-800 bg-slate-900/80 p-3">
            <div className="text-[10px] uppercase tracking-widest text-slate-500">Zone 2</div>
            <div className="mt-1 text-slate-100 font-bold">Waiting Area</div>
            <div className="mt-1 text-slate-400">People: {checkInCount}</div>
          </div>
        </div>
      </div>

      <div className="border border-slate-800 bg-slate-950 p-4 rounded-lg">
        <h3 className="text-xs font-mono tracking-wider text-slate-400 uppercase">Processing Trend</h3>
        <div className="mt-2 flex items-center justify-between">
          <span className="text-sm font-mono text-slate-200">{trendStatus}</span>
          <span className={`text-xs font-mono px-2 py-0.5 rounded border ${
            trendStatus === 'INCREASING_NON_STOP' ? 'border-red-800 text-red-300 bg-red-950/30' : 'border-slate-700 text-slate-300 bg-slate-900'
          }`}>
            LIVE
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