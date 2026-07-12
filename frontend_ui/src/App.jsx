import React, { useState, useEffect } from 'react';
import OperatorDashboard from './components/OperatorDashboard';
import AdminDashboard from './components/AdminDashboard';

// Cấu hình 4 camera hiển thị song song. Mỗi camera có đường dẫn ảnh riêng
// (backend cần ghi ra current_frame1.jpg / _2.jpg / _3.jpg / _4.jpg tương ứng)
// và tốc độ refresh riêng (offsetMs để timer từng camera lệch nhau,
// tránh cả 4 cùng fetch dồn dập vào đúng 1 thời điểm).
const CAMERA_CONFIGS = [
  { id: 1, label: 'CHECKPOINT_CAMERA_01', framePath: '/current_frame1.jpg', intervalMs: 100, offsetMs: 0 },
  { id: 2, label: 'CHECKPOINT_CAMERA_02', framePath: '/current_frame2.jpg', intervalMs: 100, offsetMs: 25 },
  { id: 3, label: 'CHECKPOINT_CAMERA_03', framePath: '/current_frame3.jpg', intervalMs: 100, offsetMs: 50 },
  { id: 4, label: 'CHECKPOINT_CAMERA_04', framePath: '/current_frame4.jpg', intervalMs: 100, offsetMs: 75 },
];

const FALLBACK_IMAGE = "https://images.unsplash.com/photo-1542296332-2e4473fac563?q=80&w=600&auto=format&fit=crop";

// Map mã incident (trigger_incident) từ backend sang câu hiển thị dễ đọc.
// Tránh hardcode 1 câu cố định cho mọi loại cảnh báo - trước đây banner luôn
// hiện "SUSPECTED LUGGAGE DISPUTE" ngay cả khi sự kiện thật là ẩu đả, dẫn tới
// hiển thị sai sự thật đang xảy ra trên camera.
const INCIDENT_LABELS = {
  SUSPECTED_LUGGAGE_DISPUTE: 'DETECTION: SUSPECTED LUGGAGE DISPUTE',
  SUSPECTED_PHYSICAL_ALTERCATION: 'DETECTION: SUSPECTED PHYSICAL ALTERCATION',
  MEDICAL_EMERGENCY: 'DETECTION: MEDICAL EMERGENCY',
};

function getIncidentLabel(triggerIncident, severity) {
  if (triggerIncident && INCIDENT_LABELS[triggerIncident]) {
    return INCIDENT_LABELS[triggerIncident];
  }
  if (severity === 'CRITICAL') return 'CRITICAL INCIDENT FLAGGED';
  if (severity === 'WARNING') return 'ANOMALOUS ACTIVITY DETECTED';
  return null;
}

function CameraFeedPanel({ config, severity, triggerIncident }) {
  const [frameTick, setFrameTick] = useState(0);

  // Timer refresh RIÊNG cho từng camera - độc lập hoàn toàn với các camera còn lại.
  // offsetMs tạo độ trễ khởi động ban đầu để các timer không bắn cùng lúc.
  useEffect(() => {
    let intervalId;
    const timeoutId = setTimeout(() => {
      intervalId = setInterval(() => {
        setFrameTick(prev => prev + 1);
      }, config.intervalMs);
    }, config.offsetMs);

    return () => {
      clearTimeout(timeoutId);
      if (intervalId) clearInterval(intervalId);
    };
  }, [config.intervalMs, config.offsetMs]);

  return (
    <div className="relative aspect-video bg-slate-900 flex items-center justify-center overflow-hidden rounded-lg border border-slate-800">
      <img
        src={`${config.framePath}?t=${frameTick}`}
        alt={`AI Terminal Analytic Feed - ${config.label}`}
        className="w-full h-full object-cover"
        onError={(e) => {
          e.target.onerror = null;
          e.target.src = FALLBACK_IMAGE;
        }}
      />
      <div className="absolute top-3 left-3 flex items-center gap-2">
        <span className="px-2 py-0.5 rounded bg-slate-950/80 text-slate-300 border border-slate-700 font-mono text-[10px] tracking-wider">
          {config.label}
        </span>
        <span className="px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800 font-mono text-[10px]">
          STREAMING
        </span>
      </div>
      {(severity === 'WARNING' || severity === 'CRITICAL') && (
        <div className={`absolute bottom-3 left-3 right-3 border-2 p-2 rounded font-mono text-[11px] animate-pulse ${
          severity === 'CRITICAL'
            ? 'border-red-500 bg-red-950/70 text-red-400'
            : 'border-amber-500 bg-amber-950/70 text-amber-400'
        }`}>
          {severity === 'CRITICAL' ? '🚨' : '⚠️'} {getIncidentLabel(triggerIncident, severity)}
        </div>
      )}
    </div>
  );
}

// Một ô thống kê nhỏ: nhãn ở trên, giá trị lớn bên dưới.
function MetricStat({ label, value, unit }) {
  return (
    <div className="flex items-baseline justify-between border-b border-slate-800/70 py-2 last:border-b-0">
      <span className="text-[11px] font-mono uppercase tracking-wider text-slate-500">{label}</span>
      <span className="text-sm font-mono font-bold text-slate-100">
        {value}
        {unit ? <span className="ml-1 text-[10px] font-normal text-slate-500">{unit}</span> : null}
      </span>
    </div>
  );
}

// Khối metrics đi kèm mỗi camera. Backend hiện chỉ phát ra MỘT bộ metrics
// tổng (chokepoint_metrics.json) chứ chưa tách riêng theo từng camera, nên
// tạm thời cả 4 khối hiển thị cùng một nguồn dữ liệu, chỉ đổi nhãn theo
// camera. Nếu backend sau này trả về field dạng metrics.cameras[id], chỉ
// cần thay `metricsData` bên dưới bằng `metricsData?.cameras?.[config.id]`.
function CameraMetricsPanel({ config, metricsData }) {
  const queueDensity = metricsData?.current_queue_density ?? '—';
  const avgWait = metricsData?.avg_wait_time_minutes ?? '—';
  const avgProcessing = metricsData?.avg_processing_time_minutes ?? '—';

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4 flex flex-col justify-center">
      <div className="text-[10px] font-mono uppercase tracking-[0.25em] text-slate-500 mb-2">
        Metrics // {config.label}
      </div>
      <MetricStat label="Queue Density" value={queueDensity} />
      <MetricStat label="Avg Wait" value={avgWait} unit="min" />
      <MetricStat label="Avg Processing" value={avgProcessing} unit="min" />
    </div>
  );
}

// Một hàng: camera bên trái, metrics của chính camera đó bên phải.
function CameraRow({ config, severity, metricsData, isLast }) {
  return (
    <div className={`grid grid-cols-1 md:grid-cols-3 gap-4 py-4 ${!isLast ? 'border-b border-slate-800' : ''}`}>
      <div className="md:col-span-2">
        <CameraFeedPanel config={config} severity={severity} triggerIncident={metricsData?.trigger_incident} />
      </div>
      <div className="md:col-span-1">
        <CameraMetricsPanel config={config} metricsData={metricsData} />
      </div>
    </div>
  );
}

export default function App() {
  // Authentication states
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');

  // System states
  const [currentRole, setCurrentRole] = useState('OPERATOR');
  const [systemState, setSystemState] = useState(null);
  const [metricsState, setMetricsState] = useState(null);

  // Poll system data structure context
  useEffect(() => {
    if (!isAuthenticated) return;
    const fetchSystemState = async () => {
      try {
        const [stateResponse, metricsResponse] = await Promise.all([
          fetch('/agent_ui_state.json'),
          fetch('/chokepoint_metrics.json'),
        ]);
        const stateData = await stateResponse.json();
        const metricsData = await metricsResponse.json();

        setSystemState(stateData);
        setMetricsState(metricsData);

        if (stateData.severity) {
          // Sync role securely with backend recommendations if preferred
        }
      } catch (error) {
        console.error("Error reading live agent UI state payload:", error);
      }
    };

    const interval = setInterval(fetchSystemState, 1000);
    return () => clearInterval(interval);
  }, [isAuthenticated]);

  const handleLogin = (e) => {
    e.preventDefault();
    // Simple but formal Hackathon Auth Evaluation
    if (username.toLowerCase() === 'admin' && password === 'admin123') {
      setCurrentRole('ADMIN');
      setIsAuthenticated(true);
    } else if (username.toLowerCase() === 'operator' && password === 'op123') {
      setCurrentRole('OPERATOR');
      setIsAuthenticated(true);
    } else {
      setLoginError('INVALID CREDENTIALS. ACCESS DENIED.');
    }
  };

  // --- LOGIN INTERFACE LAYER ---
  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen w-screen items-center justify-center bg-slate-950 font-mono text-slate-100">
        <form onSubmit={handleLogin} className="w-full max-w-md border border-slate-800 bg-slate-900 p-8 rounded-lg shadow-2xl space-y-6">
          <div className="text-center space-y-2">
            <h1 className="text-lg font-bold tracking-widest text-emerald-400">CHOKEPOINT AI</h1>
            <p className="text-xs text-slate-500 uppercase tracking-wider">Secure Access Control Terminal</p>
          </div>

          {loginError && (
            <div className="border border-red-900 bg-red-950/30 p-3 rounded text-xs text-red-400 font-bold">
              {loginError}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-xs text-slate-400 uppercase mb-1">User Identifier</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g., admin or operator"
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                required
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 uppercase mb-1">Security Cipher</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                required
              />
            </div>
          </div>

          <button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold py-2.5 rounded text-xs tracking-widest transition-colors uppercase">
            Authenticate Session
          </button>
        </form>
      </div>
    );
  }

  if (!systemState) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-900 text-slate-100">
        <p className="text-sm tracking-wider font-mono">INITIALIZING LIVE CONTEXT...</p>
      </div>
    );
  }

  // --- CORE DASHBOARD LAYER ---
  const isUrgentState = systemState.severity === 'CRITICAL' || systemState.severity === 'WARNING' || systemState.dispatch_mode === 'MANUAL_PENDING';
  const alertTitle = systemState?.admin_view?.pop_up_title || systemState?.operator_view?.banner || 'SYSTEM NOTICE';
  const alertBody = systemState?.admin_view?.description || systemState?.admin_view?.log_summary || systemState?.operator_view?.instruction || 'Monitoring live telemetry.';

  return (
    <div className="min-h-screen w-full bg-slate-900 text-slate-100 font-sans antialiased">
      <header className="flex items-center justify-between border-b border-slate-800 bg-slate-950 px-6 py-3">
        <div className="flex items-center space-x-3">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <h1 className="text-sm font-mono tracking-widest font-bold text-slate-200">CHOKEPOINT AI // EXECUTIVE</h1>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 px-3 py-1 rounded">
            <span className="text-xs font-mono text-slate-400">ACTIVE LOG: {currentRole}</span>
          </div>
          <button
            onClick={() => setIsAuthenticated(false)}
            className="text-xs font-mono text-red-400 hover:text-red-300 transition-colors"
          >
            LOGOUT
          </button>
        </div>
      </header>

      {isUrgentState && (
        <div className={`mx-6 mt-4 rounded-lg border px-4 py-3 shadow-lg ${
          systemState.severity === 'CRITICAL' || systemState.dispatch_mode === 'MANUAL_PENDING'
            ? 'border-red-900 bg-red-950/40'
            : 'border-amber-900 bg-amber-950/30'
        }`}>
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className={`text-[10px] font-mono uppercase tracking-[0.3em] ${
                systemState.severity === 'CRITICAL' || systemState.dispatch_mode === 'MANUAL_PENDING'
                  ? 'text-red-300'
                  : 'text-amber-300'
              }`}>
                Live Incident Alert
              </div>
              <div className="mt-1 text-sm font-mono font-bold text-slate-100">{alertTitle}</div>
              <div className="mt-1 text-sm font-mono text-slate-300">{alertBody}</div>
            </div>
            <div className={`shrink-0 rounded border px-3 py-1 text-xs font-mono font-bold uppercase ${
              systemState.severity === 'CRITICAL' || systemState.dispatch_mode === 'MANUAL_PENDING'
                ? 'border-red-800 text-red-300 bg-red-950/40'
                : 'border-amber-800 text-amber-300 bg-amber-950/30'
            }`}>
              {systemState.severity}
            </div>
          </div>
        </div>
      )}

      <main className="p-6 space-y-6">
        {/* 4 hàng: mỗi hàng = 1 camera + metrics của chính camera đó, đúng như bảng yêu cầu */}
        <div className="rounded-lg border border-slate-800 bg-slate-950/40 px-4 divide-y divide-slate-800">
          {CAMERA_CONFIGS.map((config, index) => (
            <CameraRow
              key={config.id}
              config={config}
              severity={systemState.severity}
              metricsData={metricsState}
              isLast={index === CAMERA_CONFIGS.length - 1}
            />
          ))}
        </div>

        {/* AI Insights & Directives, giữ nguyên bên dưới bảng camera/metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-3">
            {currentRole === 'OPERATOR' ? (
              <OperatorDashboard viewData={systemState.operator_view} severity={systemState.severity} metricsData={metricsState} />
            ) : (
              <AdminDashboard viewData={systemState.admin_view} severity={systemState.severity} dispatchMode={systemState.dispatch_mode} metricsData={metricsState} />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}