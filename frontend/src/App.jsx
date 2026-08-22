import React, { useState, useEffect, useRef, useCallback } from 'react';
import { AlertCircle, ShieldAlert, ShieldCheck, Activity, TerminalSquare, Search, Zap, FlaskConical, Cloud, Server, Cpu, RotateCcw } from 'lucide-react';

const API_BASE = 'http://localhost:8000';
const WS_BASE = 'ws://localhost:8000/ws';

export default function App() {
  const [agents, setAgents] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [killSwitchState, setKillSwitchState] = useState('active');
  const [wsConnected, setWsConnected] = useState(false);
  const [simulatorStatus, setSimulatorStatus] = useState(null);

  // Initial fetch
  useEffect(() => {
    fetch(`${API_BASE}/agents`)
      .then(res => res.json())
      .then(data => setAgents(data))
      .catch(console.error);

    fetch(`${API_BASE}/kill-switch`)
      .then(res => res.json())
      .then(data => setKillSwitchState(data.state))
      .catch(console.error);
      
    fetch(`${API_BASE}/simulator/status`)
      .then(res => res.json())
      .then(data => setSimulatorStatus(data))
      .catch(console.error);
  }, []);

  // WebSocket connection
  useEffect(() => {
    const ws = new WebSocket(WS_BASE);
    
    ws.onopen = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'transaction_event') {
        setTransactions(prev => [msg.data, ...prev].slice(0, 100)); // Keep last 100
      } else if (msg.type === 'kill_switch_event') {
        setKillSwitchState(msg.data.state);
      } else if (msg.type === 'agent_update') {
        setAgents(prev => prev.map(a => 
          a.id === msg.data.agent_id ? { ...a, spend_total: parseFloat(msg.data.spend_total) } : a
        ));
      }
    };

    return () => ws.close();
  }, []);

  const toggleKillSwitch = async () => {
    try {
      await fetch(`${API_BASE}/kill-switch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ triggered_by: 'dashboard' })
      });
    } catch (e) {
      console.error(e);
    }
  };

  const startSimulator = async () => {
    await fetch(`${API_BASE}/simulator/start`, { method: 'POST' });
    setSimulatorStatus(prev => ({ ...prev, running: true }));
  };

  const stopSimulator = async () => {
    await fetch(`${API_BASE}/simulator/stop`, { method: 'POST' });
    setSimulatorStatus(prev => ({ ...prev, running: false }));
  };

  const triggerMisbehavior = async (type) => {
    await fetch(`${API_BASE}/simulator/inject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agent_id: null, misbehavior_type: type })
    });
  };

  // LLM Degradation Test Panel State
  const [llmTestResult, setLlmTestResult] = useState(null);
  const [llmTestLoading, setLlmTestLoading] = useState(false);
  const [llmTestTier, setLlmTestTier] = useState('auto');
  const [llmTestScenario, setLlmTestScenario] = useState('');

  const runLlmTest = async (tier) => {
    setLlmTestLoading(true);
    setLlmTestResult(null);
    try {
      const res = await fetch(`${API_BASE}/simulator/test-llm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier, scenario: llmTestScenario || undefined })
      });
      const data = await res.json();
      setLlmTestResult(data);
    } catch (e) {
      setLlmTestResult({ error: `Request failed: ${e.message}`, tier_succeeded: null });
    } finally {
      setLlmTestLoading(false);
    }
  };

  const isKilled = killSwitchState === 'killed';

  return (
    <div className="app-container">
      <header className="header">
        <div>
          <h1 className="text-gradient" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.5rem', margin: 0 }}>
            <ShieldAlert size={28} color={isKilled ? 'var(--brand-red)' : 'var(--brand-green)'} />
            Nexus
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
            Real-time policy enforcement for AI agents
          </p>
        </div>
        
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: wsConnected ? 'var(--brand-green)' : 'var(--brand-red)' }} />
            {wsConnected ? 'Connected (Live)' : 'Disconnected'}
          </div>
          
          <button 
            className="btn btn-danger"
            style={{ 
              background: isKilled ? 'var(--brand-green)' : 'var(--brand-red)',
              boxShadow: isKilled ? 'var(--shadow-glow-green)' : 'var(--shadow-glow-red)'
            }}
            onClick={toggleKillSwitch}
          >
            {isKilled ? <ShieldCheck size={18} /> : <AlertCircle size={18} />}
            {isKilled ? 'RESTORE AGENTS' : 'GLOBAL KILL SWITCH'}
          </button>
        </div>
      </header>

      <main style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        
        {/* Agent Grid */}
        <section>
          <h2 style={{ fontSize: '1.125rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity size={20} className="text-gradient" />
            Active Fleet
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' }}>
            {agents.map(agent => {
              const cap = parseFloat(agent.spend_cap);
              const spent = parseFloat(agent.spend_total) || 0;
              const pct = Math.min(100, (spent / cap) * 100);
              const isFlagged = pct >= 90;
              
              return (
                <div key={agent.id} className="glass-panel" style={{ padding: '1.25rem', opacity: isKilled ? 0.6 : 1, transition: 'all 0.3s' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <h3 style={{ fontSize: '1rem' }}>{agent.name}</h3>
                    <span className="badge" style={{ background: 'rgba(255,255,255,0.1)', color: 'var(--text-secondary)' }}>
                      {agent.category}
                    </span>
                  </div>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Spend Cap</span>
                    <span className="mono">${spent.toFixed(2)} / ${cap.toFixed(2)}</span>
                  </div>
                  
                  <div className="progress-bg">
                    <div 
                      className="progress-fill" 
                      style={{ 
                        width: `${pct}%`,
                        background: isFlagged ? 'var(--brand-red)' : 'var(--brand-green)'
                      }} 
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </section>
        
        {/* Simulator Controls (Debug) */}
        <section className="glass-panel" style={{ padding: '1.25rem' }}>
          <h2 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <TerminalSquare size={18} />
            Simulator Debug Panel
          </h2>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
            {simulatorStatus?.running ? (
              <button className="btn btn-outline" onClick={stopSimulator}>Stop Simulator (Noise)</button>
            ) : (
              <button className="btn btn-outline" onClick={startSimulator}>Start Simulator (Noise)</button>
            )}
            
            <div style={{ width: '1px', height: '24px', background: 'var(--border-color)', margin: '0 0.5rem' }} />
            
            <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Inject:</span>
            <button className="btn btn-outline" onClick={() => triggerMisbehavior('overspend')} style={{ borderColor: 'rgba(239, 68, 68, 0.3)' }}>
              <Zap size={14} color="var(--brand-red)" /> Overspend
            </button>
            <button className="btn btn-outline" onClick={() => triggerMisbehavior('off_scope')} style={{ borderColor: 'rgba(239, 68, 68, 0.3)' }}>
              <Search size={14} color="var(--brand-red)" /> Off Scope
            </button>
            <button className="btn btn-outline" onClick={() => triggerMisbehavior('burst')} style={{ borderColor: 'rgba(239, 68, 68, 0.3)' }}>
              <Activity size={14} color="var(--brand-red)" /> Burst
            </button>
          </div>
        </section>

        {/* LLM Degradation Test Panel */}
        <section className="glass-panel" style={{ padding: '1.25rem' }}>
          <h2 style={{ fontSize: '1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FlaskConical size={18} />
            LLM Degradation Test Panel
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                Tier:
                <select 
                  value={llmTestTier} 
                  onChange={(e) => setLlmTestTier(e.target.value)}
                  disabled={llmTestLoading}
                  className="btn btn-outline"
                  style={{ padding: '0.35rem 0.7rem', fontSize: '0.75rem', background: 'transparent', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: '8px' }}
                >
                  <option value="auto">Auto (Hosted → Ollama → Scripted)</option>
                  <option value="hosted">Hosted API Only (HuggingFace)</option>
                  <option value="ollama">Local Ollama Only</option>
                  <option value="scripted">Scripted Fallback Only</option>
                </select>
              </label>
              <input
                type="text"
                placeholder="Custom scenario (optional)"
                value={llmTestScenario}
                onChange={(e) => setLlmTestScenario(e.target.value)}
                disabled={llmTestLoading}
                style={{ flex: 1, minWidth: '200px', padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: '0.875rem' }}
              />
              <button 
                className="btn btn-danger"
                onClick={() => runLlmTest(llmTestTier)}
                disabled={llmTestLoading}
                style={{ width: 'fit-content' }}
              >
                {llmTestLoading ? <RotateCcw size={16} className="animate-spin" /> : <FlaskConical size={16} />} Test
              </button>
            </div>

            {llmTestResult && (
              <div style={{ 
                padding: '1rem', 
                borderRadius: '8px', 
                background: llmTestResult.tier_succeeded ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                border: `1px solid ${llmTestResult.tier_succeeded ? 'var(--brand-green)' : 'var(--brand-red)'}`
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>
                    Tier Attempted: <code style={{ color: 'var(--brand-orange)' }}>{llmTestResult.tier_attempted}</code>
                  </span>
                  <span style={{ 
                    padding: '0.15rem 0.5rem', 
                    borderRadius: '4px', 
                    fontSize: '0.7rem', 
                    fontWeight: 800,
                    background: llmTestResult.tier_succeeded ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                    color: llmTestResult.tier_succeeded ? 'var(--brand-green)' : 'var(--brand-red)'
                  }}>
                    {llmTestResult.tier_succeeded ? `Succeeded: ${llmTestResult.tier_succeeded}` : 'FAILED'}
                  </span>
                </div>
                
                {llmTestResult.error && (
                  <div style={{ color: 'var(--brand-red)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                    Error: {llmTestResult.error}
                  </div>
                )}

                {llmTestResult.transactions && llmTestResult.transactions.length > 0 && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    <strong>Generated Transactions ({llmTestResult.transactions.length}):</strong>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', marginTop: '0.5rem' }}>
                      {llmTestResult.transactions.map((tx, i) => (
                        <div key={i} style={{ display: 'flex', gap: '1rem', fontFamily: 'monospace' }}>
                          <span>${parseFloat(tx.amount).toFixed(2)}</span>
                          <span>{tx.category}</span>
                          <span style={{ 
                            padding: '0.1rem 0.4rem', 
                            borderRadius: '4px', 
                            fontSize: '0.6rem',
                            background: tx.source === 'llm-hosted' ? 'rgba(245, 158, 11, 0.2)' : 
                                     tx.source === 'llm-local' ? 'rgba(245, 158, 11, 0.2)' : 
                                     'rgba(255,255,255,0.06)',
                            color: tx.source === 'sim' ? '#71717a' : '#fbbf24',
                            border: tx.source === 'sim' ? '1px solid rgba(255,255,255,0.1)' : '1px solid rgba(245, 158, 11, 0.4)'
                          }}>
                            {tx.source === 'llm-hosted' ? 'LLM ☁' : tx.source === 'llm-local' ? 'LLM' : 'SIM'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {llmTestResult.raw_response && (
                  <details style={{ marginTop: '1rem' }}>
                    <summary style={{ cursor: 'pointer', color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                      Raw Response (truncated)
                    </summary>
                    <pre style={{ marginTop: '0.5rem', padding: '0.5rem', background: 'rgba(0,0,0,0.3)', borderRadius: '4px', fontSize: '0.65rem', overflow: 'auto', whiteSpace: 'pre-wrap' }}>
                      {llmTestResult.raw_response}
                    </pre>
                  </details>
                )}
              </div>
            )}
          </div>
        </section>

      </main>

      {/* Sidebar: Event Log */}
      <aside className="glass-panel" style={{ display: 'flex', flexDirection: 'column', maxHeight: 'calc(100vh - 8rem)', overflow: 'hidden' }}>
        <div style={{ padding: '1.25rem', borderBottom: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '1.125rem' }}>Live Audit Trail</h2>
        </div>
        
        <div style={{ flex: 1, overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {transactions.length === 0 ? (
            <div style={{ color: 'var(--text-secondary)', textAlign: 'center', marginTop: '2rem' }}>
              Waiting for events...
            </div>
          ) : (
            transactions.map(tx => (
              <div key={tx.id} className="animate-slide-in" style={{ padding: '0.75rem', borderRadius: '8px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                  <span style={{ fontWeight: 500, fontSize: '0.875rem' }}>
                    {tx.agent_name || tx.agent_id}
                    {tx.source === 'llm-hosted' ? (
                      <span style={{ marginLeft: '0.5rem', display: 'inline-flex', alignItems: 'center', padding: '0.15rem 0.55rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 800, letterSpacing: '0.04em', background: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.4)', verticalAlign: 'middle' }}>LLM ☁</span>
                    ) : tx.source === 'llm-local' ? (
                      <span style={{ marginLeft: '0.5rem', display: 'inline-flex', alignItems: 'center', padding: '0.15rem 0.55rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 800, letterSpacing: '0.04em', background: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.4)', verticalAlign: 'middle' }}>LLM</span>
                    ) : (
                      <span style={{ marginLeft: '0.5rem', display: 'inline-flex', alignItems: 'center', padding: '0.15rem 0.55rem', borderRadius: '4px', fontSize: '0.65rem', fontWeight: 600, letterSpacing: '0.04em', background: 'rgba(255,255,255,0.06)', color: '#71717a', border: '1px solid rgba(255,255,255,0.1)', verticalAlign: 'middle' }}>SIM</span>
                    )}
                  </span>
                  <span className={`badge badge-${tx.decision}`}>{tx.decision}</span>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  <span>{tx.category} • <span className="mono">${parseFloat(tx.amount).toFixed(2)}</span></span>
                  <span className="mono" style={{ fontSize: '0.75rem' }}>{new Date(tx.timestamp).toLocaleTimeString()}</span>
                </div>
                
                {tx.reason && (
                  <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--brand-red)', background: 'rgba(239, 68, 68, 0.1)', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>
                    Reason: {tx.reason.replace(/_/g, ' ')}
                  </div>
                )}
                
                {tx.is_injected_misbehavior && (
                  <div style={{ marginTop: '0.25rem', fontSize: '0.7rem', color: 'var(--brand-orange)' }}>
                    [Injected Misbehavior: {tx.misbehavior_type}]
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </aside>
    </div>
  );
}