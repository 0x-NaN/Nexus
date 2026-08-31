import React, { useState, useEffect } from 'react';
import { Database, AlertTriangle, Activity, BarChart, Server, Plus, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function DeveloperDashboard() {
  const [resetting, setResetting] = useState(false);
  const [message, setMessage] = useState('');
  
  const [agents, setAgents] = useState([]);
  const [formData, setFormData] = useState({ name: '', category: '', spend_cap: 100 });
  const [adding, setAdding] = useState(false);
  
  const [resolving, setResolving] = useState(false);
  const [resolveProgress, setResolveProgress] = useState(0);

  const [metrics, setMetrics] = useState(null);

  const fetchAgents = () => {
    fetch('http://localhost:8000/agents')
      .then(r => r.json())
      .then(setAgents)
      .catch(console.error);
  };

  const fetchMetrics = () => {
    fetch('http://localhost:8000/dev/metrics')
      .then(r => r.json())
      .then(setMetrics)
      .catch(console.error);
  };

  useEffect(() => {
    fetchAgents();
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleResetDB = async () => {
    if (!confirm('Are you sure you want to completely wipe the killswitch database and re-seed it?')) return;
    setResetting(true);
    setMessage('');
    try {
      await fetch('http://localhost:8000/dev/reset-db', { method: 'POST' });
      await new Promise(r => setTimeout(r, 500)); 
      setMessage('Database successfully reset and re-seeded.');
      fetchAgents();
      fetchMetrics();
    } catch (e) {
      setMessage(`Error: ${e.message}`);
    } finally {
      setResetting(false);
    }
  };

  // ... (keep the agent handlers the same)
  const handleAddAgent = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.category || !formData.spend_cap) return;
    setAdding(true);
    try {
      await fetch('http://localhost:8000/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      setFormData({ name: '', category: '', spend_cap: 100 });
      fetchAgents();
      fetchMetrics();
    } catch (err) {
      console.error(err);
    } finally {
      setAdding(false);
    }
  };

  const handleDeleteAgent = async (id) => {
    if (!confirm(`Delete agent ${id}?`)) return;
    try {
      await fetch(`http://localhost:8000/agents/${id}`, { method: 'DELETE' });
      fetchAgents();
      fetchMetrics();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 p-8 font-mono overflow-y-auto">
      <header className="flex justify-between items-center mb-8 border-b border-white/10 pb-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Server className="text-purple-500" /> 
            Nexus DevConsole
          </h1>
          <p className="text-zinc-500 text-sm mt-1">Master controls, Fleet Management & Observability</p>
        </div>
        <Link to="/" className="text-sm text-zinc-400 hover:text-white bg-white/5 px-4 py-2 rounded-md border border-white/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]">
          &larr; Back to Main App
        </Link>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        
        {/* Master Controls */}
        <section className="bg-zinc-900/50 border border-white/5 p-6 rounded-xl shadow-2xl backdrop-blur-sm relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl" />
          <h2 className="text-lg font-semibold flex items-center gap-2 mb-4 text-zinc-300">
            <Database size={18} /> Chaos Engineering & Resets
          </h2>
          <p className="text-sm text-zinc-500 mb-6 relative z-10">
            Simulate database connection drops to observe the fallback JSONL audit log system in action, or forcefully reset the agent seeds.
          </p>

          <div className="flex flex-col gap-3 relative z-10">
            <button
              onClick={async () => {
                const newState = !metrics?.chaos_db_failure_active;
                await fetch('http://localhost:8000/dev/chaos/db-failure', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ simulate_db_failure: newState })
                });
                fetchMetrics();
              }}
              className={`w-full py-3 border rounded-lg font-bold transition-all shadow-[inset_0_1px_0_rgba(255,255,255,0.1),0_2px_4px_rgba(0,0,0,0.2)] active:translate-y-[1px] active:shadow-none flex items-center justify-center gap-2 ${
                metrics?.chaos_db_failure_active
                  ? 'bg-amber-950/40 text-amber-400 border-amber-900/50 hover:bg-amber-900/60 animate-pulse'
                  : 'bg-black/40 text-zinc-400 border-white/10 hover:bg-white/5'
              }`}
            >
              <AlertTriangle size={18} />
              {metrics?.chaos_db_failure_active ? 'DB OUTAGE ACTIVE - CLICK TO RESTORE' : 'SIMULATE DB CONNECTION DROP'}
            </button>

            <button
              onClick={handleResetDB}
              disabled={resetting}
              className="w-full py-3 bg-red-950/40 hover:bg-red-900/60 text-red-400 border border-red-900/50 rounded-lg font-bold transition-all shadow-[inset_0_1px_0_rgba(255,255,255,0.1),0_2px_4px_rgba(0,0,0,0.2)] active:translate-y-[1px] active:shadow-none flex items-center justify-center gap-2"
            >
              {resetting ? <Activity size={18} className="animate-spin" /> : <Trash2 size={18} />}
              {resetting ? 'WIPING DATABASE...' : 'FORCE RESET DATABASE'}
            </button>
          </div>

          {message && (
            <div className="mt-4 p-3 bg-emerald-950/30 text-emerald-400 border border-emerald-900/50 rounded-lg text-sm relative z-10">
              {message}
            </div>
          )}
        </section>

        {/* Bento Grid Metrics Dashboard */}
        <section className="bg-zinc-900/50 border border-white/5 p-6 rounded-xl shadow-2xl backdrop-blur-sm relative overflow-hidden">
          <div className="absolute bottom-0 right-0 w-40 h-40 bg-blue-500/10 rounded-full blur-3xl" />
          <h2 className="text-lg font-semibold flex items-center gap-2 mb-4 text-zinc-300 relative z-10">
            <BarChart size={18} /> Telemetry & Metrics
          </h2>
          
          {!metrics ? (
            <div className="h-40 flex items-center justify-center text-zinc-500 animate-pulse relative z-10">Loading telemetry...</div>
          ) : (
            <div className="grid grid-cols-2 gap-3 relative z-10">
              
              <div className="bg-black/40 border border-white/5 p-4 rounded-lg flex flex-col justify-between group shadow-inner">
                <span className="text-xs text-zinc-500 uppercase font-semibold">DB Status</span>
                <div className="flex items-center gap-2 mt-2">
                  <div className={`w-2 h-2 rounded-full shadow-[0_0_8px_rgba(255,255,255,0.5)] ${metrics.db_status === 'connected' ? 'bg-emerald-500 shadow-emerald-500/50' : 'bg-amber-500 shadow-amber-500/50'}`} />
                  <span className={`text-sm font-bold ${metrics.db_status === 'connected' ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {metrics.db_status.toUpperCase()}
                  </span>
                </div>
              </div>

              <div className="bg-black/40 border border-white/5 p-4 rounded-lg flex flex-col justify-between group shadow-inner relative">
                <span className="text-xs text-zinc-500 uppercase font-semibold">Fallback Pending</span>
                <div className="flex justify-between items-end mt-1">
                  <div className="text-2xl font-bold text-zinc-200">
                    {metrics.pending_fallback_transactions}
                    <span className="text-xs text-zinc-600 ml-1">tx</span>
                  </div>
                  {metrics.pending_fallback_transactions > 0 && !resolving && (
                    <button 
                      onClick={async () => {
                        setResolving(true);
                        setResolveProgress(0);
                        
                        await fetch('http://localhost:8000/dev/fallbacks/resolve', { method: 'POST' });
                        
                        let progress = 0;
                        const interval = setInterval(() => {
                          progress += Math.random() * 15 + 5;
                          if (progress >= 100) {
                            clearInterval(interval);
                            setResolveProgress(100);
                            setTimeout(() => {
                              setResolving(false);
                              fetchMetrics();
                            }, 500);
                          } else {
                            setResolveProgress(progress);
                          }
                        }, 250);
                      }}
                      className="text-[10px] bg-emerald-900/40 hover:bg-emerald-800/60 text-emerald-400 border border-emerald-900/50 px-2 py-1 rounded font-bold transition-colors shadow-inner"
                    >
                      RESOLVE
                    </button>
                  )}
                </div>
                
                {/* Skeuomorphic Progress Track */}
                {resolving && (
                  <div className="absolute bottom-2 left-4 right-4">
                    <div className="w-full bg-black/80 rounded-full h-1.5 border border-white/5 shadow-[inset_0_2px_4px_rgba(0,0,0,0.8)] overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.8)] transition-all duration-200 ease-out"
                        style={{ width: `${Math.min(resolveProgress, 100)}%` }}
                      />
                    </div>
                    <div className="flex justify-between mt-1 px-1">
                      <span className="text-[8px] text-emerald-500 font-bold animate-pulse">SUB-AGENT PROCESSING...</span>
                      <span className="text-[8px] text-zinc-500 font-mono">{Math.round(resolveProgress)}%</span>
                    </div>
                  </div>
                )}
              </div>

              <div className="bg-black/40 border border-white/5 p-4 rounded-lg flex flex-col justify-between group shadow-inner">
                <span className="text-xs text-zinc-500 uppercase font-semibold">Kill Switch</span>
                <div className="flex items-center gap-2 mt-2">
                  <div className={`w-2 h-2 rounded-full shadow-[0_0_8px_rgba(255,255,255,0.5)] ${metrics.kill_switch === 'active' ? 'bg-emerald-500 shadow-emerald-500/50' : 'bg-rose-500 shadow-rose-500/50 animate-pulse'}`} />
                  <span className={`text-sm font-bold ${metrics.kill_switch === 'active' ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {metrics.kill_switch.toUpperCase()}
                  </span>
                </div>
              </div>

              <div className="bg-black/40 border border-white/5 p-4 rounded-lg flex flex-col justify-between group shadow-inner">
                <span className="text-xs text-zinc-500 uppercase font-semibold">Active Agents</span>
                <div className="text-2xl font-bold text-zinc-200 mt-1">
                  {metrics.active_agents_count}
                  <span className="text-xs text-zinc-600 ml-1">nodes</span>
                </div>
              </div>

              <div className="col-span-2 bg-gradient-to-r from-purple-900/20 to-black/40 border border-purple-500/20 p-4 rounded-lg shadow-inner">
                <div className="flex justify-between items-end">
                  <div className="flex flex-col">
                    <span className="text-xs text-purple-400/70 uppercase font-semibold">Fleet Spend</span>
                    <span className="text-2xl font-bold text-purple-300 mt-1">
                      ${metrics.total_fleet_spend.toFixed(2)}
                    </span>
                  </div>
                  <Activity size={24} className="text-purple-500/50" />
                </div>
              </div>

            </div>
          )}
        </section>

      </div>

      {/* Fleet Management */}
      <section className="bg-zinc-900/50 border border-white/5 p-6 rounded-lg shadow-2xl">
        <h2 className="text-lg font-semibold flex items-center gap-2 mb-4 text-zinc-300">
          <Server size={18} /> Fleet Management
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Add Agent Form */}
          <div>
            <h3 className="text-sm font-semibold text-zinc-400 mb-4 flex items-center gap-2">
              <Plus size={16} /> Deploy Custom Agent
            </h3>
            <form onSubmit={handleAddAgent} className="flex flex-col gap-4">
              <label className="flex flex-col gap-1.5 text-sm text-zinc-400">
                Agent Name
                <input 
                  type="text" required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})}
                  className="px-3 py-2 bg-black/40 border border-white/10 rounded-md outline-none focus:border-purple-500 text-zinc-200"
                  placeholder="e.g. Nexus Security Bot"
                />
              </label>
              
              <label className="flex flex-col gap-1.5 text-sm text-zinc-400">
                Category
                <input 
                  type="text" required value={formData.category} onChange={e => setFormData({...formData, category: e.target.value})}
                  className="px-3 py-2 bg-black/40 border border-white/10 rounded-md outline-none focus:border-purple-500 text-zinc-200"
                  placeholder="e.g. infosec, marketing, data"
                />
              </label>

              <label className="flex flex-col gap-1.5 text-sm text-zinc-400">
                Spend Limit ($)
                <input 
                  type="number" required min="1" step="0.01" value={formData.spend_cap} onChange={e => setFormData({...formData, spend_cap: parseFloat(e.target.value)})}
                  className="px-3 py-2 bg-black/40 border border-white/10 rounded-md outline-none focus:border-purple-500 text-zinc-200"
                />
              </label>

              <button 
                type="submit" disabled={adding}
                className="w-full py-3 bg-purple-950/40 hover:bg-purple-900/60 text-purple-400 border border-purple-900/50 rounded-md font-bold transition-colors mt-2"
              >
                {adding ? 'DEPLOYING...' : 'DEPLOY AGENT'}
              </button>
            </form>
          </div>

          {/* Active Agents List */}
          <div>
            <h3 className="text-sm font-semibold text-zinc-400 mb-4">Active Agents</h3>
            <div className="flex flex-col gap-2 max-h-[400px] overflow-y-auto pr-2">
              {agents.map(a => (
                <div key={a.id} className="p-3 bg-black/40 border border-white/5 rounded-md flex justify-between items-center group">
                  <div>
                    <div className="text-sm font-bold text-zinc-200">{a.name}</div>
                    <div className="text-xs text-zinc-500 font-mono">{a.id} • {a.category} • Cap: ${a.spend_cap}</div>
                  </div>
                  <button 
                    onClick={() => handleDeleteAgent(a.id)}
                    className="p-2 text-zinc-500 hover:text-red-400 hover:bg-red-950/30 rounded transition-colors"
                    title="Delete Agent"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
              {agents.length === 0 && (
                <div className="text-sm text-zinc-500 italic">No active agents.</div>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
