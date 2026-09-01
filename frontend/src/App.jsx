import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route } from 'react-router-dom';
import DashboardLayout from './components/DashboardLayout.jsx';
import DeveloperDashboard from './pages/DeveloperDashboard.jsx';

const API_BASE = 'http://localhost:8000';
const WS_BASE = 'ws://localhost:8000/ws';

export default function App() {
  const [agents, setAgents] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [killSwitchState, setKillSwitchState] = useState('active');
  const [wsConnected, setWsConnected] = useState(false);
  const [simulatorStatus, setSimulatorStatus] = useState(null);

  const fetchAgents = useCallback(() => {
    fetch(`${API_BASE}/agents`).then(r => r.json()).then(setAgents).catch(console.error);
  }, []);

  useEffect(() => {
    fetchAgents();
    fetch(`${API_BASE}/kill-switch`).then(r => r.json()).then(d => setKillSwitchState(d.state)).catch(console.error);
    fetch(`${API_BASE}/simulator/status`).then(r => r.json()).then(setSimulatorStatus).catch(console.error);
  }, [fetchAgents]);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    ws.onopen = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === 'transaction_event') {
        setTransactions(p => {
          const existing = p.findIndex(t => t.id === msg.data.id);
          if (existing >= 0) {
            const updated = [...p];
            updated[existing] = { ...updated[existing], ...msg.data };
            return updated;
          }
          return [msg.data, ...p].slice(0, 100);
        });
      }
      else if (msg.type === 'kill_switch_event') setKillSwitchState(msg.data.state);
      else if (msg.type === 'agent_update') setAgents(p => p.map(a => a.id === msg.data.agent_id ? { ...a, spend_total: parseFloat(msg.data.spend_total) } : a));
    };
    return () => ws.close();
  }, []);

  const isKilled = killSwitchState === 'killed';

  const onToggleKillSwitch = async () => {
    const newState = isKilled ? 'active' : 'killed';
    try {
      await fetch(`${API_BASE}/kill-switch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ state: newState })
      });
    } catch (e) { console.error(e); }
  };

  const onStartSimulator = async () => {
    try {
      await fetch(`${API_BASE}/simulator/start`, { method: 'POST' });
      const r = await fetch(`${API_BASE}/simulator/status`);
      setSimulatorStatus(await r.json());
    } catch (e) { console.error(e); }
  };

  const onStopSimulator = async () => {
    try {
      await fetch(`${API_BASE}/simulator/stop`, { method: 'POST' });
      const r = await fetch(`${API_BASE}/simulator/status`);
      setSimulatorStatus(await r.json());
    } catch (e) { console.error(e); }
  };

  const onTriggerMisbehavior = async (type) => {
    try {
      await fetch(`${API_BASE}/simulator/inject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ misbehavior_type: type }),
      });
    } catch (e) { console.error(e); }
  };

  return (
    <div className="min-h-screen bg-background text-foreground antialiased selection:bg-primary selection:text-primary-foreground">
      <Routes>
        <Route path="/dev" element={<DeveloperDashboard />} />
        <Route path="/" element={
          <DashboardLayout
            agents={agents} transactions={transactions}
            killSwitchState={killSwitchState} wsConnected={wsConnected}
            simulatorStatus={simulatorStatus} isKilled={isKilled}
            onToggleKillSwitch={onToggleKillSwitch}
            onStartSimulator={onStartSimulator}
            onStopSimulator={onStopSimulator}
            onTriggerMisbehavior={onTriggerMisbehavior}
            refreshAgents={fetchAgents}
          />
        } />
      </Routes>
    </div>
  );
}