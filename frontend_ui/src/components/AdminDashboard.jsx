import React, { useEffect, useState } from 'react';

export default function AdminDashboard({ viewData, severity, dispatchMode, metricsData }) {
  const isCriticalPending = dispatchMode === 'MANUAL_PENDING';
  const isBypassActive = dispatchMode === 'AUTO_EMERGENCY_BYPASS';
  const isWarningPending = dispatchMode === 'MANUAL';
  const queueDensity = metricsData?.current_queue_density ?? 0;
  const avgWaitTime = metricsData?.avg_wait_time_minutes ?? 0;
  const avgProcessingTime = metricsData?.avg_processing_time_minutes ?? 0;
  const accumulationRate = metricsData?.accumulation_rate_per_min ?? 0;
  const luggageThresholdMinutes = metricsData?.luggage_stationary_threshold_minutes ?? 10;
  const zoneAnalysis = metricsData?.zone_analysis ?? {};
  const waitingCount = zoneAnalysis?.zone_1_people_count ?? 0;
  const checkInCount = zoneAnalysis?.zone_2_people_count ?? 0;
  const trendStatus = metricsData?.trend_analysis?.proc_time_slope ?? 'STABLE';

  // Dùng để nhớ incident nào đã bị dismiss, tránh việc popup tự bật lại
  // ngay lập tức ở lần polling kế tiếp khi backend vẫn còn gửi cùng 1 dispatchMode.
  const incidentKey = `${dispatchMode}|${viewData?.pop_up_title ?? ''}|${viewData?.alert ?? ''}`;
  const [dismissedKey, setDismissedKey] = useState(null);

  // Khi có incident MỚI (key khác với lần dismiss trước) -> tự động cho phép hiện lại.
  useEffect(() => {
    if (dismissedKey !== null && dismissedKey !== incidentKey) {
      setDismissedKey(null);
    }
  }, [incidentKey, dismissedKey]);

  const handleDismiss = () => setDismissedKey(incidentKey);

  const showCriticalOverlay = isCriticalPending && dismissedKey !== incidentKey;
  const showWarningOverlay = isWarningPending && dismissedKey !== incidentKey;
  const showBypassBanner = isBypassActive && dismissedKey !== incidentKey;

  return (
    <div className="relative min-h-[80vh] w-full">
      {/* Underlying Baseline Monitor Display */}
      <div className={`space-y-6 transition-filter duration-300 ${(showCriticalOverlay || showWarningOverlay) ? 'blur-sm pointer-events-none select-none' : ''}`}>
        <div className="border border-slate-800 bg-slate-950 p-6 rounded-lg">
          <h2 className="text-xs font-mono tracking-wider text-slate-400 uppercase">Executive Overview</h2>
          <p className="mt-4 text-sm text-slate-300 font-mono">
            {viewData.log_summary || "Autonomous Background Agent is balancing terminal operations."}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="border border-slate-800 bg-slate-950 p-4 rounded-lg">
            <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Queue Density</div>
            <div className="mt-2 text-2xl font-bold text-emerald-400 font-mono">{queueDensity}</div>
          </div>
          <div className="border border-slate-800 bg-slate-950 p-4 rounded-lg">
            <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Avg Wait Time</div>
            <div className="mt-2 text-2xl font-bold text-slate-100 font-mono">{avgWaitTime.toFixed(1)}m</div>
          </div>
          <div className="border border-slate-800 bg-slate-950 p-4 rounded-lg">
            <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Avg Processing</div>
            <div className="mt-2 text-2xl font-bold text-slate-100 font-mono">{avgProcessingTime.toFixed(1)}m</div>
          </div>
          <div className="border border-slate-800 bg-slate-950 p-4 rounded-lg">
            <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Accumulation</div>
            <div className="mt-2 text-2xl font-bold text-slate-100 font-mono">{accumulationRate.toFixed(2)}</div>
          </div>
          <div className="border border-slate-800 bg-slate-950 p-4 rounded-lg">
            <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Luggage Threshold</div>
            <div className="mt-2 text-2xl font-bold text-amber-400 font-mono">{luggageThresholdMinutes}m</div>
          </div>
        </div>

        <div className="border border-slate-800 bg-slate-950 p-4 rounded-lg">
          <h3 className="text-xs font-mono tracking-wider text-slate-400 uppercase">Zone Split</h3>
          <div className="mt-3 grid grid-cols-2 gap-3 text-sm font-mono">
            <div className="rounded border border-slate-800 bg-slate-900/80 p-3">
              <div className="text-[10px] uppercase tracking-widest text-slate-500">Zone 1</div>
              <div className="mt-1 text-slate-100 font-bold">Waiting Area</div>
              <div className="mt-1 text-slate-400">People: {waitingCount}</div>
            </div>
            <div className="rounded border border-slate-800 bg-slate-900/80 p-3">
              <div className="text-[10px] uppercase tracking-widest text-slate-500">Zone 2</div>
              <div className="mt-1 text-slate-100 font-bold">Check-in Area</div>
              <div className="mt-1 text-slate-400">People: {checkInCount}</div>
            </div>
          </div>
        </div>

        <div className="border border-slate-800 bg-slate-950 p-4 rounded-lg">
          <h3 className="text-xs font-mono tracking-wider text-slate-400 uppercase">Processing Trend</h3>
          <p className="mt-2 text-sm text-slate-300 font-mono">{trendStatus}</p>
        </div>
      </div>

      {/* CRITICAL INCIDENT OVERLAY: 20-Second Escalation Window Module */}
      {showCriticalOverlay && (
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
                <button
                  onClick={handleDismiss}
                  className="flex-1 bg-red-700 hover:bg-red-600 text-white font-mono text-xs font-bold py-2.5 rounded transition-colors uppercase"
                >
                  Approve Deployment
                </button>
                <button
                  onClick={handleDismiss}
                  className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs py-2.5 rounded transition-colors uppercase"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CRITICAL BYPASS ALERT: Appears when Admin exceeds 20-second timeout */}
      {showBypassBanner && (
        <div className="mt-6 border border-red-900 bg-red-950/20 p-6 rounded-lg relative">
          <button
            onClick={handleDismiss}
            aria-label="Dismiss"
            className="absolute top-3 right-3 text-slate-500 hover:text-slate-300 font-mono text-xs uppercase"
          >
            ✕
          </button>
          <h3 className="text-sm font-mono font-bold text-red-400 uppercase">{viewData.alert}</h3>
          <p className="mt-2 text-sm font-mono text-slate-300 leading-relaxed">{viewData.details}</p>
        </div>
      )}

      {/* MEDIUM INCIDENT OVERLAY: Compounding Bottleneck Authorization */}
      {showWarningOverlay && (
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
                <button
                  onClick={handleDismiss}
                  className="flex-1 bg-amber-700 hover:bg-amber-600 text-slate-950 font-mono text-xs font-bold py-2.5 rounded transition-colors uppercase"
                >
                  Execute Redistribution
                </button>
                <button
                  onClick={handleDismiss}
                  className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs py-2.5 rounded transition-colors uppercase"
                >
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