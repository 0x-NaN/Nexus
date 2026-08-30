import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  AlertCircle, ShieldAlert, ShieldCheck, Activity, TerminalSquare, 
  Search, Zap, FlaskConical, RotateCcw, Wifi, WifiOff, Shield
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';
const WS_BASE = 'ws://localhost:8000/ws';

// ── Components ────────────────────────────────────────────────────────────────

const Badge = ({ children, variant = 'neutral', className = '' }) => {
  const variants = {
    allowed: 'badge-allowed',
    denied: 'badge-denied',
    flagged: 'badge-flagged',
    neutral: 'badge-neutral',
    sim: 'badge-sim',
    llm: 'badge-llm',
    'llm-hosted': 'badge-llm-hosted',
    'llm-local': 'badge-llm-local',
  };
  return (
    <span className={`badge ${variants[variant]} ${className}`}>
      {children}
    </span>
  );
};

const ProgressBar = ({ value, max = 100, flaggedThreshold = 90 }) => {
  const pct = Math.min(100, (value / max) * 100);
  const isFlagged = pct >= flaggedThreshold;
  return (
    <div className="progress-bg" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
      <motion.div
        className={`progress-fill ${isFlagged ? 'flagged' : ''}`}
        style={{ width: `${pct}%` }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
      />
    </div>
  );
};

const AgentCard = ({ agent, isKilled }) => {
  const cap = parseFloat(agent.spend_cap);
  const spent = parseFloat(agent.spend_total) || 0;
  const pct = Math.min(100, (spent / cap) * 100);
  const isFlagged = pct >= 90;

  return (
    <motion.div
      key={agent.id}
      className="glass-panel agent-card"
      animate={{ 
        opacity: isKilled ? 0.5 : 1,
        filter: isFlagged ? 'drop-shadow(0 0 8px var(--brand-red))' : 'none'
      }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
    >
      <div className="agent-card-header">
        <h3 className="agent-card-name">{agent.name}</h3>
        <Badge variant="neutral">{agent.category}</Badge>
      </div>
      
      <div className="agent-card-spend">
        <span className="label">Spend Cap</span>
        <span className="mono">${spent.toFixed(2)} / ${cap.toFixed(2)}</span>
      </div>
      
      <ProgressBar value={spent} max={cap} flaggedThreshold={cap * 0.9} />
    </motion.div>
  );
};

const KillSwitchButton = ({ isKilled, onClick, disabled }) => (
  <motion.button
    className="btn btn-kill-switch"
    onClick={onClick}
    disabled={disabled}
    whileHover={{ scale: 1.02 }}
    whileTap={{ scale: 0.98 }}
    animate={{
      boxShadow: isKilled ? 'var(--shadow-glow-green)' : 'var(--shadow-glow-red)',
      background: isKilled ? 'var(--brand-green)' : 'var(--brand-red)',
    }}
    transition={{ duration: 0.15 }}
    style={{
      background: isKilled ? 'var(--brand-green)' : 'var(--brand-red)',
      boxShadow: isKilled ? 'var(--shadow-glow-green)' : 'var(--shadow-glow-red)',
    }}
  >
    {isKilled ? (
      <>
        <ShieldCheck size={18} />
        <span>RESTORE AGENTS</span>
      </>
    ) : (
      <>
        <AlertCircle size={18} />
        <span>GLOBAL KILL SWITCH</span>
      </>
    )}
  </motion.button>
);

const ConnectionStatus = ({ connected }) => (
  <div className="connection-status" title={connected ? 'WebSocket connected' : 'WebSocket disconnected'}>
    <span
      className="connection-dot"
      style={{
        background: connected ? 'var(--brand-green)' : 'var(--brand-red)',
        boxShadow: connected ? '0 0 8px var(--brand-green)' : 'none',
      }}
    />
    <span className="label">{connected ? 'Connected (Live)' : 'Disconnected'}</span>
  </div>
);

const SourceBadge = ({ source }) => {
  if (source === 'llm-hosted') {
    return <Badge variant="llm-hosted">LLM ☁</Badge>;
  }
  if (source === 'llm-local') {
    return <Badge variant="llm-local">LLM</Badge>;
  }
  return <Badge variant="sim">SIM</Badge>;
};

const TransactionRow = ({ tx }) => (
  <motion.div
    key={tx.id}
    className="transaction-row"
    initial={{ opacity: 0, y: -10, height: 0 }}
    animate={{ opacity: 1, y: 0, height: 'auto' }}
    exit={{ opacity: 0, y: 10, height: 0 }}
    transition={{ duration: 0.2, ease: 'easeOut' }}
  >
    <div className="transaction-header">
      <div className="transaction-agent">
        <span className="agent-name">{tx.agent_name || tx.agent_id}</span>
        <SourceBadge source={tx.source} />
      </div>
      <Badge variant={tx.decision}>{tx.decision}</Badge>
    </div>

    <div className="transaction-meta">
      <span>{tx.category} • <span className="mono">${parseFloat(tx.amount).toFixed(2)}</span></span>
      <span className="mono timestamp">{new Date(tx.timestamp).toLocaleTimeString()}</span>
    </div>

    {tx.reason && (
      <div className="transaction-reason">
        Reason: {tx.reason.replace(/_/g, ' ')}
      </div>
    )}

    {tx.is_injected_misbehavior && (
      <div className="transaction-injected">
        [Injected Misbehavior: {tx.misbehavior_type}]
      </div>
    )}
  </motion.div>
);

const LLMTestPanel = ({ onRunTest, loading, tier, setTier, scenario, setScenario, result }) => (
  <section className="glass-panel panel">
    <header className="panel-header">
      <FlaskConical size={18} />
      <h2>LLM Degradation Test Panel</h2>
    </header>

    <div className="llm-test-controls">
      <label className="control-group">
        <span className="label">Tier</span>
        <select
          value={tier}
          onChange={(e) => setTier(e.target.value)}
          disabled={loading}
          className="select"
        >
          <option value="auto">Auto (Hosted → Ollama → Scripted)</option>
          <option value="hosted">Hosted API Only (HuggingFace)</option>
          <option value="ollama">Local Ollama Only</option>
          <option value="scripted">Scripted Fallback Only</option>
        </select>
      </label>

      <label className="control-group scenario-input">
        <span className="label">Scenario</span>
        <input
          type="text"
          placeholder="Custom scenario (optional)"
          value={scenario}
          onChange={(e) => setScenario(e.target.value)}
          disabled={loading}
          className="input"
        />
      </label>

      <button
        className="btn btn-primary"
        onClick={() => onRunTest(tier)}
        disabled={loading}
      >
        {loading ? (
          <>
            <RotateCcw size={16} className="animate-spin" />
            <span>Testing…</span>
          </>
        ) : (
          <>
            <FlaskConical size={16} />
            <span>Run Test</span>
          </>
        )}
      </button>
    </div>

    {result && (
      <AnimatePresence mode="wait">
        <motion.div
          className={`llm-test-result ${result.tier_succeeded ? 'success' : 'error'}`}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
        >
          <div className="result-header">
            <div>
              <span className="label">Tier Attempted:</span>
              <code className="tier-code">{result.tier_attempted}</code>
            </div>
            <Badge variant={result.tier_succeeded ? 'allowed' : 'denied'}>
              {result.tier_succeeded ? `Succeeded: ${result.tier_succeeded}` : 'FAILED'}
            </Badge>
          </div>

          {result.error && (
            <div className="result-error">{result.error}</div>
          )}

          {result.transactions?.length > 0 && (
            <div className="result-transactions">
              <strong>Generated Transactions ({result.transactions.length}):</strong>
              <div className="transactions-list">
                {result.transactions.map((tx, i) => (
                  <div key={i} className="transaction-item">
                    <span className="mono">${parseFloat(tx.amount).toFixed(2)}</span>
                    <span className="category">{tx.category}</span>
                    <SourceBadge source={tx.source} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.raw_response && (
            <details className="result-raw">
              <summary>Raw Response (truncated)</summary>
              <pre>{result.raw_response}</pre>
            </details>
          )}
        </motion.div>
      </AnimatePresence>
    )}
  </section>
);

const SimulatorPanel = ({ status, onStart, onStop, onInject }) => (
  <section className="glass-panel panel">
    <header className="panel-header">
      <TerminalSquare size={18} />
      <h2>Simulator Debug Panel</h2>
    </header>

    <div className="simulator-controls">
      <button
        className="btn btn-outline"
        onClick={status?.running ? onStop : onStart}
      >
        {status?.running ? 'Stop Simulator (Noise)' : 'Start Simulator (Noise)'}
      </button>

      <div className="divider" />

      <span className="label">Inject Misbehavior:</span>

      <button
        className="btn btn-outline inject-btn"
        onClick={() => onInject('overspend')}
        style={{ borderColor: 'rgba(239, 68, 68, 0.4)' }}
      >
        <Zap size={14} style={{ color: 'var(--brand-red)' }} /> Overspend
      </button>

      <button
        className="btn btn-outline inject-btn"
        onClick={() => onInject('off_scope')}
        style={{ borderColor: 'rgba(239, 68, 68, 0.4)' }}
      >
        <Search size={14} style={{ color: 'var(--brand-red)' }} /> Off Scope
      </button>

      <button
        className="btn btn-outline inject-btn"
        onClick={() => onInject('burst')}
        style={{ borderColor: 'rgba(239, 68, 68, 0.4)' }}
      >
        <Activity size={14} style={{ color: 'var(--brand-red)' }} /> Burst
      </button>
    </div>
  </section>
);

export default function DashboardLayout({
  agents,
  transactions,
  killSwitchState,
  wsConnected,
  simulatorStatus,
  isKilled,
  onToggleKillSwitch,
  onStartSimulator,
  onStopSimulator,
  onTriggerMisbehavior,
  onRunLlmTest,
  llmTestResult,
  llmTestLoading,
  llmTestTier,
  setLlmTestTier,
  llmTestScenario,
  setLlmTestScenario,
  agents: agentsProp,
  transactions: transactionsProp,
  isKilled: isKilledProp,
  wsConnected: wsConnectedProp,
  simulatorStatus: simulatorStatusProp
}) {
  return (
    <div className="app-container">
      <header className="header">
        <div className="header-brand">
          <div className="logo">
            <ShieldAlert size={28} style={{ color: isKilled ? 'var(--brand-red)' : 'var(--brand-green)' }} />
            <span className="title">Nexus</span>
          </div>
          <p className="tagline">Real-time policy enforcement for AI agents</p>
        </div>

        <div className="header-actions">
          <ConnectionStatus connected={wsConnected} />
          <KillSwitchButton isKilled={isKilled} onClick={onToggleKillSwitch} />
        </div>
      </header>

      <div className="layout">
        <main className="main">
          {/* Agent Grid */}
          <section className="panel">
            <header className="panel-header">
              <Activity size={20} />
              <h2>Active Fleet</h2>
            </header>

            <div className="agent-grid">
              {agentsProp.map(agent => (
                <AgentCard key={agent.id} agent={agent} isKilled={isKilledProp} />
              ))}
            </div>
          </section>

          {/* Debug Panels */}
          <SimulatorPanel
            status={simulatorStatusProp}
            onStart={onStartSimulator}
            onStop={onStopSimulator}
            onInject={onTriggerMisbehavior}
          />

          <LLMTestPanel
            onRunTest={onRunLlmTest}
            loading={llmTestLoading}
            tier={llmTestTier}
            setTier={setLlmTestTier}
            scenario={llmTestScenario}
            setScenario={setLlmTestScenario}
            result={llmTestResult}
          />
        </main>

        {/* Sidebar: Event Log */}
        <aside className="sidebar glass-panel">
          <header className="panel-header">
            <h2>Live Audit Trail</h2>
          </header>

          <div className="audit-feed">
            <AnimatePresence mode="popLayout">
              {transactionsProp.length === 0 ? (
                <div className="audit-empty">
                  <Activity size={32} className="audit-empty-icon" />
                  <p>Waiting for events…</p>
                </div>
              ) : (
                transactionsProp.map((tx, i) => (
                  <TransactionRow key={tx.id} tx={tx} index={i} />
                ))
              )}
            </AnimatePresence>
          </div>
        </aside>
      </div>
    </div>
  );
}