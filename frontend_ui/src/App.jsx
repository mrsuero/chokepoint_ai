import React, { useState, useEffect } from 'react';
import OperatorDashboard from './components/OperatorDashboard';
import AdminDashboard from './components/AdminDashboard';

export default function App() {
  // Authorization role state: 'OPERATOR' or 'ADMIN'
  const [currentRole, setCurrentRole] = useState('ADMIN');
  const [systemState, setSystemState] = useState(null);

  // Poll configuration: Fetch UI state payload from backend engine every 1 second
  useEffect(() => {
    const fetchSystemState = async () => {
      try {
        // In live deployment, replace with backend server endpoint
        const response = await fetch('/agent_ui_state.json');
        const data = await response.json();
        setSystemState(data);
      } catch (error) {
        console.error("Error reading live agent UI state payload:", error);
      }
    };

    const interval = setInterval(fetchSystemState, 1000);
    return () => clearInterval(interval);
  }, []);

  if (!systemState) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-900 text-slate-100">
        <p className="text-sm tracking-wider font-mono">INITIALIZING SYSTEM DATA CONTEXT...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-slate-900 text-slate-100 font-sans antialiased">
      {/* Role Navigation Bar for Hackathon Demo evaluation */}
      <header className="flex items-center justify-between border-b border-slate-800 bg-slate-950 px-6 py-3">
        <div className="flex items-center space-x-3">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <h1 className="text-sm font-mono tracking-widest font-bold text-slate-200">CHOKEPOINT AI // CORE SYSTEM</h1>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono text-slate-400 mr-2">DEMO SIMULATION ROLE:</span>
          <button 
            onClick={() => setCurrentRole('OPERATOR')}
            className={`px-3 py-1 rounded text-xs font-mono transition-colors ${currentRole === 'OPERATOR' ? 'bg-blue-600 text-white font-bold' : 'bg-slate-800 text-slate-400'}`}
          >
            OPERATOR
          </button>
          <button 
            onClick={() => setCurrentRole('ADMIN')}
            className={`px-3 py-1 rounded text-xs font-mono transition-colors ${currentRole === 'ADMIN' ? 'bg-red-600 text-white font-bold' : 'bg-slate-800 text-slate-400'}`}
          >
            ADMIN
          </button>
        </div>
      </header>

      {/* Conditional Interface Allocation Layer */}
      <main className="p-6">
        {currentRole === 'OPERATOR' ? (
          <OperatorDashboard viewData={systemState.operator_view} severity={systemState.severity} />
        ) : (
          <AdminDashboard viewData={systemState.admin_view} severity={systemState.severity} dispatchMode={systemState.dispatch_mode} />
        )}
      </main>
    </div>
  );
}