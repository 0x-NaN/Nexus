---
name: Codestreet Governance
description: Real-time policy enforcement and fleet-wide revocation dashboard for AI payment agents
colors:
  accent: "#f59e0b"
  accent-deep: "#d97706"
  accent-muted: "rgba(245, 158, 11, 0.15)"
  bg-primary: "#09090b"
  bg-secondary: "#18181b"
  bg-card: "rgba(24, 24, 27, 0.6)"
  border: "rgba(255, 255, 255, 0.1)"
  text-primary: "#f4f4f5"
  text-secondary: "#a1a1aa"
  semantic-green: "#10b981"
  semantic-red: "#ef4444"
  semantic-orange: "#f59e0b"
  semantic-blue: "#3b82f6"
typography:
  body:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    letterSpacing: "0.05em"
    textTransform: "uppercase"
  mono:
    fontFamily: "JetBrains Mono, monospace"
    fontSize: "0.75rem"
    fontWeight: 400
rounded:
  sm: "4px"
  md: "8px"
  lg: "12px"
  pill: "9999px"
spacing:
  xs: "0.25rem"
  sm: "0.5rem"
  md: "1rem"
  lg: "1.25rem"
  xl: "2rem"
components:
  button-primary:
    backgroundColor: "{colors.semantic-red}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "0.75rem 1.5rem"
  button-primary-hover:
    backgroundColor: "#dc2626"
    rounded: "{rounded.md}"
    padding: "0.75rem 1.5rem"
  button-outline:
    backgroundColor: "transparent"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "0.75rem 1.5rem"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.md}"
    padding: "0.35rem 0.7rem"
  badge-allowed:
    backgroundColor: "rgba(16, 185, 129, 0.1)"
    textColor: "{colors.semantic-green}"
    rounded: "{rounded.pill}"
    padding: "0.25rem 0.75rem"
  badge-denied:
    backgroundColor: "rgba(239, 68, 68, 0.1)"
    textColor: "{colors.semantic-red}"
    rounded: "{rounded.pill}"
    padding: "0.25rem 0.75rem"
  badge-flagged:
    backgroundColor: "rgba(245, 158, 11, 0.1)"
    textColor: "{colors.semantic-orange}"
    rounded: "{rounded.pill}"
    padding: "0.25rem 0.75rem"
  card:
    backgroundColor: "{colors.bg-card}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  progress-bar:
    height: "6px"
    rounded: "{rounded.pill}"
---

# Design System: Codestreet Governance

## 1. Overview

**Creative North Star: "The Watchtower"**

A real-time oversight dashboard built for command, not decoration. Like a Bloomberg terminal reimagined for AI governance — the interface is dark, dense with signal, and every pixel has a job. The Watchtower watches the agent fleet, surfaces anomalies instantly, and puts a single definitive action (the kill switch) within arm's reach at all times.

The system rejects generic SaaS admin patterns (identical card grids, sidebar nav tropes) and fintech navy-and-gold clichés. Authority comes from restraint: near-black backgrounds, minimal color reserved for semantic states, and typography that lets data breathe. Glassmorphism is used sparingly — only for container surfaces where depth separation clarifies hierarchy.

**Key Characteristics:**
- **Data-first density:** Information is scannable, not overwhelming. The audit trail is a feed, not a spreadsheet.
- **Semantic color language:** Green = allowed, red = denied, orange = flagged. Amber accent denotes system governance controls. Color never decorates — it communicates.
- **Instant feedback:** Interactive elements respond with zero perceived latency. State changes (hover, active, kill-switch toggle) are visibly acknowledged within 150–200ms.
- **Bloomberg-inspired depth:** Dark gradient backgrounds create ambient atmosphere. Glass panels provide subtle surface separation without visual clutter.

## 2. Colors

A restrained palette built around a near-black foundation. Accent color (amber) is used sparingly for the governance brand element; semantic colors carry the real communicative weight.

### Primary
- **Amber Accent** (#f59e0b): Used for the logo/title text gradient and brand identity elements. Never used as a surface color. Its rarity is the point — it signals "governance" without competing with semantic indicators.

### Semantic (system status)
- **Green** (#10b981 / oklch(0.62 0.18 150)): Allowed decisions, active/live indicators, healthy states.
- **Red** (#ef4444 / oklch(0.58 0.22 25)): Denied decisions, kill-switch active glow, critical alerts.
- **Orange** (#f59e0b / oklch(0.72 0.17 70)): Flagged decisions (near-cap warnings), injected misbehavior markers.
- **Blue** (#3b82f6 / oklch(0.58 0.16 250)): Accent icons, secondary information markers.

### Neutral
- **Near-Black** (#09090b): Primary background. The surface the interface sits on.
- **Dark Surface** (#18181b): Secondary panels, card backgrounds at full opacity.
- **Glass Card** (rgb(24, 24, 27, 0.6)): Card and panel surfaces with glassmorphism blur.
- **Border** (rgb(255, 255, 255, 0.1)): Subtle separation lines between surfaces.
- **Text Primary** (#f4f4f5): Headings, body copy, high-emphasis information.
- **Text Secondary** (#a1a1aa): Labels, timestamps, lower-emphasis metadata.

### Named Rules
**The Authority Through Restraint Rule.** Amber accent appears on ≤5% of any given screen. Its rarity is the signal. Semantic colors (green/red/orange) dominate the visible palette because they convey actual system state — decoration never competes with data.

## 3. Typography

**Body Font:** Inter (with system-ui sans fallback)
**Mono Font:** JetBrains Mono (for all monetary values, timestamps, and data)

**Character:** A single sans family carries the entire interface — display, body, labels — with mono reserved exclusively for data. No serif pairing, no display font. The typography is utilitarian and precise, like a terminal or instrumentation panel. JetBrains Mono provides clear character distinction for financial values ($1,234.56) where legibility is non-negotiable.

### Hierarchy
- **Title / Heading** (Inter 600, 1.125–1.5rem, 1.2): Section headers, agent names. Uses `text-wrap: balance` for even lines.
- **Body** (Inter 400, 0.875rem, 1.5): Transaction details, agent metadata, descriptions. Max line length 65–75ch.
- **Label** (Inter 600, 0.75rem, uppercase, 0.05em letter-spacing): Badges, category tags, pill indicators.
- **Data / Mono** (JetBrains Mono 400, 0.75–0.875rem, 1.4): All monetary amounts (`$47.43`), agent IDs (`agent_001`), timestamps, transaction IDs.

### Named Rules
**The One Family Rule.** No display fonts, no serif pairings. Inter + JetBrains Mono is the complete vocabulary. Variation comes from weight (400/500/600/700) and size, not font switching.

## 4. Elevation

The system uses a hybrid approach: surfaces are flat on the content plane and use subtle glassmorphism (backdrop-filter blur) for depth separation, rather than drop shadows. This creates the Bloomberg-terminal feel of layered information without the visual noise of cast shadows.

- **Primary surface (body bg):** Near-black, no shadow, no texture. The base plane.
- **Secondary surface (cards/panels):** Semi-transparent glass (`--bg-card: rgba(24,24,27,0.6)`) with `backdrop-filter: blur(12px)` and a 1px subtle border. These panels hover optically above the base plane.
- **Interactive elevation:** Buttons use `translateY(-1px)` on hover and `translateY(1px)` on active for tactile feedback. This is the only transform-based elevation in the system.

Shadows are reserved exclusively for the kill-switch button, where colored glows (`--shadow-glow-red` and `--shadow-glow-green`) provide urgent visual feedback for the system's most critical action.

### Shadow Vocabulary (kill-switch only)
- **Kill Switch Active** (0 0 15px rgba(239, 68, 68, 0.5)): Red glow when kill switch is engaged. High urgency.
- **Kill Switch Restored** (0 0 15px rgba(16, 185, 129, 0.2)): Green glow when agents are restored. Confirmation signal.

## 5. Components

### Buttons
- **Shape:** Gently rounded corners (8px radius). Pill shapes are reserved for badges only.
- **Primary/Danger (`btn-danger`):** Solid red background (`#ef4444`) with white text. On hover: darkens to `#dc2626`, lifts `translateY(-1px)`, shadow intensifies. On active: presses down `translateY(1px)`. Transition: all 0.2s.
- **Outline (`btn-outline`):** Transparent background, 1px `--border-color` stroke, `--text-primary` color. On hover: subtle white background (`rgba(255,255,255,0.05)`). No transform. Used for secondary and debug panel actions.
- **Ghost (Export CSV, inline controls):** Transparent background, minimal padding, `--text-secondary` color. On hover: brightens to `--text-primary`, subtle background fill.

### Badges
- **Style:** Pill shape (9999px border-radius), uppercase label, 0.05em letter-spacing, 0.75rem / 600 weight.
- **Decision badges:** Three semantic variants: `badge-allowed` (green tint bg + border, green text), `badge-denied` (red tint bg + border, red text), `badge-flagged` (orange tint bg + border, orange text). The border shares the same color as the text at lower opacity for a cohesive tinted appearance.
- **Category badges:** Neutral variant — white background at 10% opacity, `--text-secondary` color. Used for agent category labels.

### Cards (Agent Cards)
- **Corner Style:** Rounded (12px radius) — "glass-panel" class.
- **Background:** Semi-transparent glass (`rgba(24,24,27,0.6)` + `backdrop-filter: blur(12px)`).
- **Border:** 1px `var(--border-color)`. No shadow.
- **Internal Padding:** 1.25rem (20px).
- **Content:** Agent name + category badge at top, spend-cap progress bar below.
- **State:** When kill switch is active, card opacity drops to 0.6 with `transition: all 0.3s`. This provides immediate visual feedback of fleet-wide revocation.

### Progress Bar (Spend Cap)
- **Track:** Full-width, 6px height, pill shape. Background: `rgba(255,255,255,0.1)`.
- **Fill:** Animated width + background-color transition (0.3s ease). Color: green at <90%, red at ≥90% (flagged state). The color transition is as important as the width transition — it visually signals threshold crossing.

### Audit Trail (Feed Items)
- **Style:** 8px rounded container, `rgba(255,255,255,0.03)` background, 1px `--border-color` border.
- **Content:** Agent name + decision badge on top row, category + amount + timestamp on second row.
- **Entry animation:** `slideIn` — fades up from 10px with opacity (0.3s ease-out). New items appear at the top of the feed.
- **Reason/flag detail:** Collapsible-style inline sections below the main row. Denied transactions show red-tinted reason block; injected misbehaviors show orange marker.

### Debug Panel
- **Style:** Glass panel container (same as agent cards) with `1.25rem` padding.
- **Simulator toggle:** Outline button that reads "Start Simulator (Noise)" or "Stop Simulator (Noise)" based on `simulatorStatus.running`.
- **Inject buttons:** Outline buttons with red-tinted borders. Each carries a Lucide icon + label. Compact, utilitarian — these are dev tools, not user-facing controls.

## 6. Do's and Don'ts

### Do:
- **Do** use semantic color to communicate system state. Green = allowed/all good, red = denied/critical, orange = flagged/warning.
- **Do** keep the amber accent rare (≤5% of screen area). Its scarcity is what makes it read as "governance brand," not decoration.
- **Do** use JetBrains Mono for every monetary value, agent ID, and timestamp. This is non-negotiable for data legibility.
- **Do** animate interactive state changes (hover, active, kill-switch toggle) within 150–200ms with smooth easing.
- **Do** use glass-panel surfaces for card/container depth instead of drop shadows. Keep the Bloomberg-terminal layered feel.
- **Do** translate buttons down (`translateY(1px)`) on press for tactile confirmation.

### Don't:
- **Don't** use gradient text beyond the single title element. The `text-gradient` class is reserved for the "Codestreet Governance" heading only.
- **Don't** use glassmorphism on more than 60% of any screen. Glass is a container surface, not a page-wide aesthetic.
- **Don't** add decorative motion. No spinning loaders in content areas, no orchestrated page-entrance sequences, no parallax.
- **Don't** use display fonts in UI labels, buttons, or data. Inter + JetBrains Mono is the complete vocabulary.
- **Don't** fall into generic fintech patterns. The palette is near-black, semantic green/red/orange, and a rare amber accent.
- **Don't** side-stripe borders. No `border-left: 3px solid` colored accents on cards or list items. Use full borders, background tints, or nothing.
- **Don't** over-round corners. Cards top out at 12px; buttons at 8px. Pill shapes are for badges only.
