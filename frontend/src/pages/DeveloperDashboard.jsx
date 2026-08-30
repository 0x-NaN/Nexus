import React, { useState, useEffect } from 'react';
import { Database, AlertTriangle, Activity, BarChart, Server, Plus, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function DeveloperDashboard() {
  const [resetting, setResetting] = useState(false);
  const [message, setMessage] = useState('');
  
  const [agents, setAgents] = useState([]);
  const [formData, setFormData] = useState({ name: '', category: '', spend_cap: 100 });
  const [adding, setAdding] = useState(false);

  const fetchAgents = () => {
    fetch('http://localhost:8000/agents')
      .then(r => r.json())
      .then(setAgents)
      .catch(console.error);
  };

  useEffect(() => {
    fetchAgents();
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
    } catch (e) {
      setMessage(`Error: ${e.message}`);
    } finally {
      setResetting(false);
    }
  };

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
        <Link to="/" className="text-sm text-zinc-400 hover:text-white bg-white/5 px-4 py-2 rounded-md border border-white/10">
          &larr; Back to Main App
        </Link>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        
        {/* Master Controls */}
        <section className="bg-zinc-900/50 border border-white/5 p-6 rounded-lg shadow-2xl">
          <h2 className="text-lg font-semibold flex items-center gap-2 mb-4 text-zinc-300">
            <Database size={18} /> Database Management
          </h2>
          <p className="text-sm text-zinc-500 mb-6">
            Resetting the database will wipe all audit trail history and restore the agent fleet to the default seed configuration.
          </p>

          <button
            onClick={handleResetDB}
            disabled={resetting}
            className="w-full py-3 bg-red-950/40 hover:bg-red-900/60 text-red-400 border border-red-900/50 rounded-md font-bold transition-colors flex items-center justify-center gap-2"
          >
            {resetting ? <Activity size={18} className="animate-spin" /> : <AlertTriangle size={18} />}
            {resetting ? 'WIPING DATABASE...' : 'FORCE RESET DATABASE'}
          </button>

          {message && (
            <div className="mt-4 p-3 bg-emerald-950/30 text-emerald-400 border border-emerald-900/50 rounded text-sm">
              {message}
            </div>
          )}
        </section>

        {/* Observability Links */}
        <section className="bg-zinc-900/50 border border-white/5 p-6 rounded-lg shadow-2xl">
          <h2 className="text-lg font-semibold flex items-center gap-2 mb-4 text-zinc-300">
            <BarChart size={18} /> Observability (Phase 2)
          </h2>
          <p className="text-sm text-zinc-500 mb-6">
            Deep stats, hardware metrics, and structured logs are handled by the standalone Grafana/Prometheus stack.
          </p>
          
          <div className="flex flex-col gap-3">
            <a href="http://localhost:3000" target="_blank" rel="noreferrer" className="flex items-center justify-between p-4 bg-black/40 hover:bg-black/60 border border-white/5 rounded-md transition-colors group">
              <div>
                <strong className="block text-zinc-200">Grafana Dashboard</strong>
                <span className="text-xs text-zinc-500">Port 3000 • admin/admin</span>
              </div>
              <span className="text-purple-400 group-hover:translate-x-1 transition-transform">↗</span>
            </a>
          </div>
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
