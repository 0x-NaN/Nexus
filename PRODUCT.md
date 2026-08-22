# Product

## Register

product

## Users

**Primary**: Small-org operators and engineering teams deploying autonomous AI agents who need a lightweight, self-hosted governance layer. They need to understand system state at a glance, configure per-agent policies, and have a credible audit trail for internal review or regulatory purposes.

**Secondary**: Ash (builder) — portfolio piece targeting fintech risk & controls roles (AmEx, JPM-type) and systems/ML-infra internship positions. Must signal: policy enforcement, real-time revocation, immutable audit logging, and engineering maturity (honest limitation disclosure, architecture-first process).

**Tertiary**: Open-source contributors and evaluators assessing Nexus as a base for their own agent governance needs.

## Product Purpose

A real-time governance dashboard for a simulated fleet of AI payment agents. Demonstrates:
- Per-agent spend caps with two-tier enforcement (flag at 90%, deny at 100%)
- Scope-based transaction validation
- Burst detection (rate limiting)
- Global kill switch — instant fleet-wide revocation
- Immutable audit trail with export

Success looks like: a judge watches the live demo for 30 seconds and immediately understands "this is a governance layer that can halt rogue AI agents before they cause damage." The kill-switch toggle is the demo's "wow" moment — it must feel instant and definitive.

Success looks like: an operator or evaluator opens the dashboard, watches agents transacting in real time, sees a violation get caught and the kill switch halt the fleet, and immediately understands this is production-credible governance infrastructure — not a demo toy.

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

Dark mode is intentional — matches the "command center" aesthetic and reads well in both office and presentation environments. Color is never the sole differentiator for decisions (badge text + color always present together). Auth (JWT/OIDC) is being added for real multi-user support. No specific WCAG level target currently, but contrast ratios should be checked during the motion.dev pass.
