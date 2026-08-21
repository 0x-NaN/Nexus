# Product

## Register

product

## Users

**Primary**: Hackathon judges at Codestreet 2026 finale. They evaluate in a live demo setting — the dashboard must communicate instantly: what the product does, that policy enforcement is working, and that the kill-switch mechanism is real-time. No onboarding, no tutorials. Every element visible in the first 5 seconds must reinforce the governance narrative.

**Secondary**: Ash (the solo builder) uses this for demo rehearsal and debugging. The simulator debug panel and live audit trail serve this workflow without compromising the judge-facing polish.

**Tertiary**: Portfolio piece for fintech risk & controls roles (AmEx, JPM-type). Must signal: policy enforcement, real-time revocation, immutable audit logging — controls/ops relevance, not ML modeling.

## Product Purpose

A real-time governance dashboard for a simulated fleet of AI payment agents. Demonstrates:
- Per-agent spend caps with two-tier enforcement (flag at 90%, deny at 100%)
- Scope-based transaction validation
- Burst detection (rate limiting)
- Global kill switch — instant fleet-wide revocation
- Immutable audit trail with export

Success looks like: a judge watches the live demo for 30 seconds and immediately understands "this is a governance layer that can halt rogue AI agents before they cause damage." The kill-switch toggle is the demo's "wow" moment — it must feel instant and definitive.

## Brand Personality

Precise. Authoritative. Polished.

- **Precise**: Every number, label, and status has clear meaning. No ambiguity in what a transaction decision means or why it was made.
- **Authoritative**: The interface projects control. Dark backdrop, deliberate spacing, confident typography. This is a command center, not a toy.
- **Polished**: Judges see craft — smooth animations, coherent color language, responsive layout. The demo is the product.

## Anti-references

- **Not generic SaaS**: No cookie-cutter admin template patterns (identical card grids, generic sidebar nav, Stock Illustration-style icons). Every element earns its place.
- **Not Bloomberg-terminal dense**: Data is scannable, not overwhelming. The audit trail is a feed, not a spreadsheet. Information hierarchy guides the eye.
- **Not typical fintech navy-and-gold**: Dark theme uses deep near-black backgrounds with purple or yellow accents instead of the standard blue/gold combo. The palette signals "different category" without sacrificing professional tone.

## Design Principles

1. **Demo-first hierarchy**: The kill-switch button and agent status are the hero elements. Everything else supports them. A judge should understand the state of the system in one glance.
2. **Transparent enforcement**: Every policy decision is visible in the audit trail with a clear reason. No hidden logic. The dashboard proves governance is working by showing its work.
3. **Real-time as the default**: The WebSocket feed and live-updating spend meters are not features — they're the only mode. Remove the concept of "refresh." The dashboard is always current.
4. **Authority through restraint**: Dark background, minimal color usage (green/red/orange carry semantic weight only), generous whitespace. The interface doesn't shout; it lets the data command attention.
5. **Instant feedback on critical actions**: The kill switch toggles with zero perceived latency. Visual feedback (glow, color shift, agent opacity change) confirms the action before the user looks for confirmation.

## Accessibility & Inclusion

Current approach is sufficient for the demo context. Dark mode is intentional for theater/judging conditions. No specific WCAG level target. Color is not the sole differentiator for decisions (badge text + color). Reduced motion is not a priority for this surface.
