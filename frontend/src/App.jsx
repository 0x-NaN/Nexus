import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext.jsx';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import DashboardLayout from './components/DashboardLayout.jsx';
import { ProtectedRoute, PublicRoute } from './components/AuthRoutes.jsx';

const API_BASE = 'http://localhost:8000';
const WS_BASE = 'ws://localhost:8000/ws';

export default function App() {
  const [agents, setAgents] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [killSwitchState, setKillSwitchState] = useState('active');
  const [wsConnected, setWsConnected] = useState(false);
  const [simulatorStatus, setSimulatorStatus] = useState(null);

  const [llmTestResult, setLlmTestResult] = useState(null);
  const [llmTestLoading, setLlmTestLoading] = useState(false);
  const [llmTestTier, setLlmTestTier] = useState('auto');
  const [llmTestScenario, setLlmTestScenario] = useState('');

  useEffect(() => {
    fetch(`${API_BASE}/agents`).then(r => r.json()).then(setAgents).catch(console.error);
    fetch(`${API_BASE}/kill-switch`).then(r => r.json()).then(d => setKillSwitchState(d.state)).catch(console.error);
    fetch(`${API_BASE}/simulator/status`).then(r => r.json()).then(setSimulatorStatus).catch(console.error);
  }, []);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    ws.onopen = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === 'transaction_event') setTransactions(p => [msg.data, ...p].slice(0, 100));
      else if (msg.type === 'kill_switch_event') setKillSwitchState(msg.data.state);
      else if (msg.type === 'agent_update') setAgents(p => p.map(a => a.id === msg.data.agent_id ? { ...a, spend_total: parseFloat(msg.data.spend_total) } : a));
    };
    return () => ws.close();
  }, []);

  const isKilled = killSwitchState === 'killed';

  return (
    <div>
      <Routes>
        <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
        <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
        <Route path="/" element={
          <ProtectedRoute>
            <DashboardLayout
              agents={agents} transactions={transactions}
              killSwitchState={killSwitchState} wsConnected={wsConnected}
              simulatorStatus={simulatorStatus} isKilled={killSwitchState === 'killed'}
            />
          </ProtectedRoute>
        } />
      </Routes>
    </div>
  );
}