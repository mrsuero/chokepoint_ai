import React, { useState, useEffect } from 'react';
import OperatorDashboard from './components/OperatorDashboard';
import AdminDashboard from './components/AdminDashboard';

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
  const [frameTick, setFrameTick] = useState(0);

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

  // Refresh dynamic camera frame buffer every 100ms
  useEffect(() => {
    if (!isAuthenticated) return;
    const frameInterval = setInterval(() => {
      setFrameTick(prev => prev + 1);
    }, 100);
    return () => clearInterval(frameInterval);
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

      <main className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Columns: Live Video Analytics Monitor */}
        <div className="lg:col-span-2 space-y-4">
          <div className="border border-slate-800 bg-slate-950 rounded-lg overflow-hidden">
            <div className="border-b border-slate-800 bg-slate-900/50 px-4 py-2.5 flex justify-between items-center">
              <span className="text-xs font-mono tracking-wider text-slate-300">LIVE FEED // CHECKPOINT_CAMERA_01</span>
              <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-mono text-[10px]">STREAMING</span>
            </div>
            <div className="relative aspect-video bg-slate-900 flex items-center justify-center overflow-hidden">
              {/* Image stream fetching live processed frames from backend */}
              <img 
                src={`/current_frame.jpg?t=${frameTick}`} 
                alt="AI Terminal Analytic Feed"
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.target.src = "https://images.unsplash.com/photo-1542296332-2e4473fac563?q=80&w=600&auto=format&fit=crop"; // Placeholder fallback
                }}
              />
              {/* Geometric AI Overlay Markers if incident triggers */}
              {systemState.severity === 'WARNING' && (
                <div className="absolute top-4 left-4 border-2 border-amber-500 bg-amber-950/70 p-2 rounded font-mono text-xs text-amber-400 animate-pulse">
                  ⚠️ DETECTION: SUSPECTED LUGGAGE DISPUTE AT WORKSTATION ZONE 1
                </div>
              )}
              {systemState.severity === 'CRITICAL' && (
                <div className="absolute top-4 left-4 border-2 border-red-500 bg-red-950/70 p-2 rounded font-mono text-xs text-red-400 animate-pulse">
                  🚨 CRITICAL INCIDENT FLAGGED
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: AI Insights & Directives */}
        <div className="space-y-6">
          {currentRole === 'OPERATOR' ? (
            <OperatorDashboard viewData={systemState.operator_view} severity={systemState.severity} metricsData={metricsState} />
          ) : (
            <AdminDashboard viewData={systemState.admin_view} severity={systemState.severity} dispatchMode={systemState.dispatch_mode} metricsData={metricsState} />
          )}
        </div>
      </main>
    </div>
  );
}