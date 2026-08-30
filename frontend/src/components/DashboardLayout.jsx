import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  AlertCircle, ShieldAlert, ShieldCheck, Activity, TerminalSquare, 
  Search, Zap, Shield, LayoutDashboard, Users, Sun, Moon, Download, X, Plus
} from 'lucide-react';
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// ── Shared Spatial & Skeuomorphic Classes ───────────────────────────────────
const panelClass = "bg-card/60 backdrop-blur-2xl border border-border/50 shadow-2xl shadow-black/30 rounded-xl overflow-hidden transition-colors";
const buttonBase = "relative inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium transition-all rounded-lg select-none active:translate-y-[1px] active:shadow-none focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border border-border/50";
const skeuoShadows = "shadow-[inset_0_1px_0_rgba(255,255,255,0.1),0_2px_4px_rgba(0,0,0,0.2)] active:shadow-[inset_0_2px_4px_rgba(0,0,0,0.2)]";

// ── Interactive Dot Background ───────────────────────────────────────────────
// Brutalist color palette for light mode dot interactions
const LIGHT_PALETTE = [
  [255, 59,  48 ], // coral red
  [0,   122, 255], // electric blue
  [52,  199, 89 ], // lime green
  [175, 82,  222], // violet
  [255, 149, 0  ], // amber
  [255, 45,  146], // hot pink
];

const DotBackground = ({ isLightMode }) => {
  const canvasRef = useRef(null);
  const mouseRef = useRef({ x: -200, y: -200 });
  const trailRef = useRef([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const SPACING = 32;
    const RADIUS = 1.4;
    const INFLUENCE = 130;
    const TRAIL_LIFETIME = 70;

    const draw = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      ctx.clearRect(0, 0, w, h);

      const mx = mouseRef.current.x;
      const my = mouseRef.current.y;

      const trail = trailRef.current;
      for (let i = trail.length - 1; i >= 0; i--) {
        trail[i].age++;
        if (trail[i].age > TRAIL_LIFETIME) trail.splice(i, 1);
      }

      const cols = Math.ceil(w / SPACING);

      for (let xi = 1; xi * SPACING < w; xi++) {
        for (let yi = 1; yi * SPACING < h; yi++) {
          const x = xi * SPACING;
          const y = yi * SPACING;
          const dMouse = Math.hypot(x - mx, y - my);
          let brightness = 0;

          if (dMouse < INFLUENCE) {
            brightness = Math.max(brightness, 1 - dMouse / INFLUENCE);
          }

          for (const tp of trail) {
            const dTrail = Math.hypot(x - tp.x, y - tp.y);
            const trailInfluence = INFLUENCE * (1 - tp.age / TRAIL_LIFETIME);
            if (dTrail < trailInfluence) {
              const b = (1 - dTrail / trailInfluence) * (1 - tp.age / TRAIL_LIFETIME);
              brightness = Math.max(brightness, b);
            }
          }

          const r = RADIUS + brightness * 2.5;

          let fillStyle;
          if (isLightMode) {
            if (brightness > 0.01) {
              // Pick a colour from the palette based on grid position
              const palIdx = (xi * 3 + yi * 7) % LIGHT_PALETTE.length;
              const [pr, pg, pb] = LIGHT_PALETTE[palIdx];
              const alpha = 0.15 + brightness * 0.85;
              fillStyle = `rgba(${pr},${pg},${pb},${alpha})`;

              // Glow ring at high brightness
              if (brightness > 0.5) {
                ctx.beginPath();
                ctx.arc(x, y, r + 3, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(${pr},${pg},${pb},${brightness * 0.15})`;
                ctx.fill();
              }
            } else {
              // Resting dots: subtle coloured tint based on position
              const palIdx = (xi * 3 + yi * 7) % LIGHT_PALETTE.length;
              const [pr, pg, pb] = LIGHT_PALETTE[palIdx];
              fillStyle = `rgba(${pr},${pg},${pb},0.07)`;
            }
          } else {
            // Dark mode: white dots
            const alpha = 0.10 + brightness * 0.60;
            fillStyle = `rgba(220,220,220,${alpha})`;
          }

          ctx.beginPath();
          ctx.arc(x, y, r, 0, Math.PI * 2);
          ctx.fillStyle = fillStyle;
          ctx.fill();
        }
      }
      animId = requestAnimationFrame(draw);
    };

    draw();

    const handleMove = (e) => {
      const x = e.clientX;
      const y = e.clientY;
      mouseRef.current = { x, y };

      const last = trailRef.current[trailRef.current.length - 1];
      if (!last || Math.hypot(x - last.x, y - last.y) > 3) {
        trailRef.current.push({ x, y, age: 0 });
        if (trailRef.current.length > 120) trailRef.current.shift();
      }
    };

    const handleLeave = () => {
      mouseRef.current = { x: -200, y: -200 };
    };

    window.addEventListener('mousemove', handleMove);
    window.addEventListener('mouseleave', handleLeave);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', handleMove);
      window.removeEventListener('mouseleave', handleLeave);
    };
  }, [isLightMode]);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 w-full h-full pointer-events-none z-0"
    />
  );
};

// ── Components ────────────────────────────────────────────────────────────────

const Badge = ({ children, variant = 'neutral', className }) => {
  const variants = {
    allowed: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20',
    denied: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20',
    flagged: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20',
    neutral: 'bg-foreground/5 text-foreground/70 border border-border/50',
    sim: 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20',
    'llm': 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20',
    'llm-hosted': 'bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20',
  };
  return (
    <span className={cn(`px-2.5 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider`, variants[variant] || variants.neutral, className)}>
      {children}
    </span>
  );
};

const ProgressBar = ({ value, max = 100, flaggedThreshold = 90 }) => {
  const pct = Math.min(100, (value / max) * 100);
  const isFlagged = pct >= flaggedThreshold;
  return (
    <div className="w-full h-2 rounded-full bg-black/20 dark:bg-black/40 overflow-hidden shadow-[inset_0_1px_3px_rgba(0,0,0,0.3)]">
      <motion.div
        className={cn("h-full rounded-full shadow-[inset_0_1px_0_rgba(255,255,255,0.3)]", isFlagged ? 'bg-amber-500' : 'bg-emerald-500')}
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
      className={cn(panelClass, "p-5 flex flex-col gap-4 border-t border-t-white/10 dark:border-t-white/5 relative z-10")}
      animate={{ opacity: isKilled ? 0.5 : 1 }}
      transition={{ duration: 0.2 }}
    >
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-semibold text-foreground">{agent.name}</h3>
          <p className="text-xs text-muted-foreground font-mono mt-1">{agent.id}</p>
        </div>
        <Badge variant="neutral">{agent.category}</Badge>
      </div>
      
      <div className="flex flex-col gap-1.5 mt-auto">
        <div className="flex justify-between items-end text-sm">
          <span className="text-muted-foreground">Spend Cap</span>
          <span className="font-mono text-foreground/80">
            <span className={isFlagged ? "text-amber-500" : ""}>${spent.toFixed(2)}</span> / ${cap.toFixed(2)}
          </span>
        </div>
        <ProgressBar value={spent} max={cap} flaggedThreshold={cap * 0.9} />
      </div>
    </motion.div>
  );
};

const KillSwitchSlider = ({ isKilled, onClick }) => (
  <div className="flex items-center gap-3 relative z-10">
    <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">{isKilled ? 'FLEET HALTED' : 'FLEET ACTIVE'}</span>
    <div 
      onClick={onClick}
      className={cn(
        "relative w-24 h-8 rounded-full cursor-pointer transition-colors duration-300 shadow-[inset_0_2px_6px_rgba(0,0,0,0.4)] border border-border",
        isKilled ? "bg-rose-600" : "bg-emerald-500"
      )}
    >
      <motion.div 
        animate={{ x: isKilled ? 64 : 4 }}
        transition={{ type: "spring", stiffness: 600, damping: 35 }}
        className="absolute top-1 w-6 h-6 rounded-full bg-gradient-to-b from-zinc-100 to-zinc-300 shadow-[0_2px_4px_rgba(0,0,0,0.3),inset_0_-2px_2px_rgba(0,0,0,0.1),inset_0_2px_2px_rgba(255,255,255,0.9)] border border-zinc-400 flex items-center justify-center"
      >
        <div className="w-1 h-3 rounded-full bg-zinc-400/60 shadow-inner" />
      </motion.div>
      <div className="absolute inset-0 flex items-center justify-between px-3 text-[10px] font-bold text-white/90 pointer-events-none select-none">
        <span className={cn("transition-opacity", isKilled ? "opacity-0" : "opacity-100")}>ON</span>
        <span className={cn("transition-opacity", isKilled ? "opacity-100" : "opacity-0")}>OFF</span>
      </div>
    </div>
  </div>
);

const ThemeKnob = ({ isLightMode, onToggle }) => {
  const rotation = isLightMode ? 40 : -40;

  return (
    <div className="flex items-center gap-2 relative z-10">
      <span className="text-[9px] font-bold text-muted-foreground uppercase tracking-widest select-none">DARK</span>
      <div
        onClick={onToggle}
        className="relative w-10 h-10 rounded-full cursor-pointer select-none"
        title={isLightMode ? "Switch to Dark" : "Switch to Bright"}
      >
        <div className="absolute inset-0 rounded-full bg-gradient-to-b from-zinc-800 to-zinc-600 shadow-[inset_0_2px_4px_rgba(0,0,0,0.6),0_1px_2px_rgba(255,255,255,0.05)] border border-zinc-500/30" />
        <motion.div
          animate={{ rotate: rotation }}
          transition={{ type: "spring", stiffness: 300, damping: 25 }}
          className="absolute inset-[3px] rounded-full bg-gradient-to-b from-zinc-300 to-zinc-500 shadow-[inset_0_2px_3px_rgba(255,255,255,0.5),inset_0_-2px_3px_rgba(0,0,0,0.3),0_2px_6px_rgba(0,0,0,0.4)] border border-zinc-400/50 flex items-center justify-center"
        >
          <div className="w-[3px] h-3 bg-zinc-700 rounded-full -mt-1 shadow-[inset_0_1px_1px_rgba(0,0,0,0.4)]" />
        </motion.div>
      </div>
      <span className="text-[9px] font-bold text-muted-foreground uppercase tracking-widest select-none">BRIGHT</span>
    </div>
  );
};

const TransactionRow = ({ tx }) => (
  <motion.div
    initial={{ opacity: 0, y: -10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, scale: 0.95 }}
    className={cn(
      "p-4 rounded-lg bg-foreground/5 border border-border/30 shadow-inner backdrop-blur-sm",
      "flex flex-col gap-2 relative z-10"
    )}
  >
    <div className="flex justify-between items-start">
      <div className="flex items-center gap-2">
        <span className="font-medium text-sm text-foreground/90">{tx.agent_name || tx.agent_id}</span>
        <Badge variant={tx.source === 'llm-hosted' ? 'llm-hosted' : (tx.source === 'llm-local' ? 'llm' : 'sim')}>
          {tx.source === 'llm-hosted' ? 'LLM ☁' : (tx.source === 'llm-local' ? 'LLM' : 'SIM')}
        </Badge>
      </div>
      <Badge variant={tx.decision}>{tx.decision}</Badge>
    </div>

    <div className="flex justify-between items-center text-xs text-muted-foreground">
      <span>{tx.category} • <span className="font-mono text-foreground/80">${parseFloat(tx.amount).toFixed(2)}</span></span>
      <span className="font-mono">{new Date(tx.timestamp).toLocaleTimeString()}</span>
    </div>

    {tx.reason && (
      <div className="text-xs text-rose-600 dark:text-rose-400/80 bg-rose-500/10 px-2 py-1.5 rounded mt-1 border border-rose-500/20">
        {tx.reason.replace(/_/g, ' ')}
      </div>
    )}

    {tx.is_injected_misbehavior && (
      <div className="text-xs text-amber-600 dark:text-amber-400/80 bg-amber-500/10 px-2 py-1.5 rounded mt-1 border border-amber-500/20">
        [Injected: {tx.misbehavior_type}]
      </div>
    )}
  </motion.div>
);

const SidebarItem = ({ icon: Icon, label, active, onClick }) => (
  <button onClick={onClick} className={cn(
    "flex items-center gap-3 px-3 py-2 w-full rounded-md text-sm font-medium transition-colors text-left relative z-10",
    active ? "bg-foreground/10 text-foreground shadow-inner" : "text-muted-foreground hover:bg-foreground/5 hover:text-foreground"
  )}>
    <Icon size={18} />
    {label}
  </button>
);

// ── Overlay Window Content (Spatial UI) ─────────────
const OverlayView = ({ title, onClose, children }) => (
  <motion.div
    initial={{ opacity: 0, scale: 0.95, y: 10 }}
    animate={{ opacity: 1, scale: 1, y: 0 }}
    exit={{ opacity: 0, scale: 0.95, y: 10 }}
    transition={{ type: "spring", stiffness: 400, damping: 30 }}
    className="absolute inset-4 z-50 rounded-2xl bg-card/30 backdrop-blur-[40px] border border-border/30 shadow-2xl flex flex-col overflow-hidden"
  >
    <header className="h-16 border-b border-border/30 flex items-center justify-between px-6 bg-foreground/5">
      <h2 className="text-lg font-semibold">{title}</h2>
      <button onClick={onClose} className="p-2 rounded-md hover:bg-foreground/10 text-muted-foreground hover:text-foreground transition-colors">
        <X size={20} />
      </button>
    </header>
    <div className="flex-1 overflow-hidden flex">
      {children}
    </div>
  </motion.div>
);

// ── Fleet Agents Overlay ───────────────────────────────────────────────────
const FleetAgentsView = ({ agents }) => {
  return (
    <div className="flex w-full h-full">
      {/* List of Agents */}
      <div className="flex-1 p-8 overflow-y-auto">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-6">Active Agents Directory</h3>
        <div className="flex flex-col gap-4">
          {agents.map(a => (
            <div key={a.id} className="p-4 bg-foreground/5 border border-border/30 rounded-lg max-w-4xl">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="text-lg font-semibold">{a.name}</h4>
                  <p className="text-xs font-mono text-muted-foreground">{a.id}</p>
                </div>
                <Badge variant="neutral">{a.category}</Badge>
              </div>
              <div className="mt-4 p-3 bg-background/50 rounded text-sm text-foreground/80 border border-border/20">
                <p><strong>System Prompt / Role:</strong> Specialized AI agent tasked with operations in the <span className="text-amber-500 font-mono">{a.category}</span> domain. Hard limit at <strong>${a.spend_cap}</strong> per transaction cycle.</p>
                <p className="mt-2 text-xs text-muted-foreground">* Custom behavior scripts can be injected via the Ollama endpoint.</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};


// ── Main Layout ─────────────────────────────────────────────────────────────

export default function DashboardLayout({
  agents, transactions, killSwitchState, wsConnected,
  simulatorStatus, isKilled, onToggleKillSwitch,
  onStartSimulator, onStopSimulator, onTriggerMisbehavior,
  refreshAgents
}) {
  const [activeView, setActiveView] = useState('dashboard');
  const [isLightMode, setIsLightMode] = useState(false);

  useEffect(() => {
    if (isLightMode) {
      document.documentElement.classList.add('light');
    } else {
      document.documentElement.classList.remove('light');
    }
  }, [isLightMode]);

  const handleExportTrail = () => {
    const lines = transactions.map(tx => 
      `[${new Date(tx.timestamp).toLocaleString()}] ${tx.decision.toUpperCase()} | Agent: ${tx.agent_name || tx.agent_id} | Amount: $${tx.amount} | Reason: ${tx.reason || 'N/A'}`
    );
    const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nexus-audit-trail-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden selection:bg-amber-500/30 transition-colors duration-500 relative">
      
      {/* Interactive Dot Background tracks window-wide */}
      <DotBackground isLightMode={isLightMode} />

      {/* ── Left Sidebar (Admin Navigation) ── */}
      <aside className="w-64 border-r border-border/50 bg-card/30 flex flex-col backdrop-blur-3xl z-20">
        <div className="p-6 flex items-center gap-3 border-b border-border/50">
          <div className="p-2 bg-gradient-to-br from-zinc-700 to-zinc-900 rounded-lg shadow-inner border border-white/10 dark:border-white/5">
            <ShieldAlert size={24} className={isKilled ? "text-rose-500" : "text-emerald-500"} />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight bg-gradient-to-r from-foreground to-foreground/60 bg-clip-text text-transparent">NEXUS</h1>
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-semibold">Governance</p>
          </div>
        </div>

        <nav className="p-4 flex-1 flex flex-col gap-1">
          <SidebarItem icon={LayoutDashboard} label="Dashboard" active={activeView === 'dashboard'} onClick={() => setActiveView('dashboard')} />
          <SidebarItem icon={Users} label="Fleet Agents" active={activeView === 'agents'} onClick={() => setActiveView('agents')} />
        </nav>

        <div className="p-4 border-t border-border/50">
          <div className={cn(panelClass, "p-4 flex items-center gap-3")}>
            <span className={cn("w-2 h-2 rounded-full animate-pulse", wsConnected ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" : "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.8)]")} />
            <span className="text-xs font-medium text-foreground/80">
              {wsConnected ? 'System Live' : 'Disconnected'}
            </span>
          </div>
        </div>
      </aside>

      {/* ── Main Content Area ── */}
      <div className="flex-1 flex flex-col relative z-10 overflow-hidden">
        {/* Subtle background geometric glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-emerald-500/5 blur-[120px] rounded-full pointer-events-none z-0" />

        {/* Top Header */}
        <header className="h-20 border-b border-border/50 bg-card/20 backdrop-blur-md flex items-center justify-between px-8 z-20 relative">
          <div>
            <h2 className="text-xl font-semibold">Fleet Overview</h2>
            <p className="text-sm text-muted-foreground">Real-time policy enforcement and monitoring</p>
          </div>
          <div className="flex items-center gap-6">
             <ThemeKnob isLightMode={isLightMode} onToggle={() => setIsLightMode(!isLightMode)} />
             <div className="w-px h-8 bg-border/50" />
             <KillSwitchSlider isKilled={isKilled} onClick={onToggleKillSwitch} />
          </div>
        </header>

        {/* Scrollable Content or Overlay */}
        <div className="flex-1 relative overflow-hidden z-10">
          
          <AnimatePresence>
            {activeView === 'agents' && (
              <OverlayView title="Fleet Agents Directory" onClose={() => setActiveView('dashboard')}>
                <FleetAgentsView agents={agents} refreshAgents={refreshAgents} />
              </OverlayView>
            )}
          </AnimatePresence>

          <main className={cn("absolute inset-0 overflow-y-auto p-8 flex gap-8 z-[1] transition-opacity duration-300", activeView !== 'dashboard' ? 'opacity-30 pointer-events-none' : 'opacity-100')}>
            
            {/* Left Column (Grid & Controls) */}
            <div className="flex-1 flex flex-col gap-8 max-w-5xl">
              {/* Agent Grid */}
              <section>
                <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
                  <Users size={16} /> Active Agents
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {agents.map(agent => (
                    <AgentCard key={agent.id} agent={agent} isKilled={isKilled} />
                  ))}
                </div>
              </section>

              {/* Debug Panels */}
              <section className="grid grid-cols-1 xl:grid-cols-2 gap-4 mt-4">
                
                {/* Simulator Panel */}
                <div className={cn(panelClass, "p-6 flex flex-col z-10 relative")}>
                  <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
                    <TerminalSquare size={16} /> Simulator Console
                  </h3>
                  
                  <div className="flex flex-col gap-4">
                    <button
                      className={cn(buttonBase, skeuoShadows, "bg-secondary hover:bg-secondary/80 text-secondary-foreground w-full")}
                      onClick={simulatorStatus?.running ? onStopSimulator : onStartSimulator}
                    >
                      {simulatorStatus?.running ? 'Stop Ambient Noise' : 'Start Ambient Noise'}
                    </button>

                    <div className="h-px bg-border/50 my-2" />
                    
                    <span className="text-xs text-muted-foreground font-medium">INJECT MISBEHAVIOR</span>
                    <div className="grid grid-cols-3 gap-2">
                      <button className={cn(buttonBase, skeuoShadows, "bg-secondary hover:bg-rose-900/10 text-rose-600 dark:text-rose-400")} onClick={() => onTriggerMisbehavior('overspend')}>
                        <Zap size={14} /> Overspend
                      </button>
                      <button className={cn(buttonBase, skeuoShadows, "bg-secondary hover:bg-rose-900/10 text-rose-600 dark:text-rose-400")} onClick={() => onTriggerMisbehavior('off_scope')}>
                        <Search size={14} /> Off Scope
                      </button>
                      <button className={cn(buttonBase, skeuoShadows, "bg-secondary hover:bg-rose-900/10 text-rose-600 dark:text-rose-400")} onClick={() => onTriggerMisbehavior('burst')}>
                        <Activity size={14} /> Burst
                      </button>
                    </div>
                  </div>
                </div>

              </section>
            </div>

            {/* Right Column (Audit Trail) */}
            <aside className="w-[400px] flex flex-col shrink-0">
              <div className={cn(panelClass, "flex-1 flex flex-col h-[calc(100vh-140px)] sticky top-0 z-10 relative")}>
                <header className="p-4 border-b border-border/50 bg-foreground/5 flex justify-between items-center">
                  <h3 className="text-sm font-semibold text-foreground/90 flex items-center gap-2">
                    <Shield size={16} className="text-amber-500" /> Live Audit Trail
                  </h3>
                  <button onClick={handleExportTrail} className="text-xs flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors">
                    <Download size={14} /> TXT
                  </button>
                </header>
                <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3 scrollbar-hide">
                  <AnimatePresence mode="popLayout">
                    {transactions.length === 0 ? (
                      <div className="flex flex-col items-center justify-center h-full text-muted-foreground gap-3">
                        <Activity size={32} className="opacity-50" />
                        <p className="text-sm">Waiting for events...</p>
                      </div>
                    ) : (
                      transactions.map((tx) => (
                        <TransactionRow key={tx.id} tx={tx} />
                      ))
                    )}
                  </AnimatePresence>
                </div>
              </div>
            </aside>

          </main>
        </div>
      </div>
    </div>
  );
}