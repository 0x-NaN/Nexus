# Motion Design — Nexus Governance

**Library**: motion.dev (formerly Framer Motion)  
**Version**: Latest  
**Integration scope**: React component animations only

---

## Core Principle: Functional Motion Only

motion.dev is added with a **hard scope constraint**: animations must be triggered by real data changes or user interactions. Motion serves clarity, never decoration. This preserves the "authority through restraint" design philosophy from DESIGN.md.

---

## What Counts as "Functional"

Animate these state changes:
- **New audit trail entry**: Slide up + fade in (0.3s ease-out, 10px translate)
- **Spend-cap progress bar**: Width and background-color transitions as the meter fills (0.3s ease)
- **Kill-switch toggle**: Button press animation (`translateY(-1px)` on hover, `translateY(1px)` on active; 0.2s all)
- **Kill-switch state change**: Agent cards fade opacity to 0.6 (0.3s transition) when fleet is halted; restore to 1.0 when active
- **Decision badges appearance**: Flagged and denied badges fade in with background + text color transitions (0.2s)
- **Kill-switch glow**: Red glow on active state, green glow on restored state (shadow transitions, 0.3s)

---

## What is NOT Allowed

Never add these, even though the library supports them:
- **Page entrance orchestration**: Staggered animations on load, fade-in sequences, hero-section reveals
- **Loading spinners**: Rotating loaders, bouncing indicators, or skeleton animations in content areas
- **Parallax**: Depth-based scroll effects
- **Decorative motion**: Any animation that plays without a corresponding state change or user action
- **Attention-grabbing sequences**: Pulsing, flashing, or eye-catching patterns unrelated to data

---

## Implementation Notes

- **Transition timing**: Keep all animations 150–300ms (smooth, not laggy; not so fast they feel jarring)
- **Easing functions**: Use `ease-out` for appearances, `ease-in-out` for continuous transitions
- **API usage**: motion.dev's declarative syntax (AnimatePresence, motion.div, Variants) generates clean, agent-friendly code
- **Bundle impact**: motion.dev is ~40KB gzipped; no performance concerns at this scale
- **Testing**: Verify animations trigger only on actual data/state changes, never gratuitously on component render

---

## Aligns With

- **DESIGN.md Do's**: "Do animate interactive state changes (hover, active, kill-switch toggle) within 150–200ms"
- **DESIGN.md Don'ts**: "Don't add decorative motion"
- **context.md Phase 1**: motion.dev integration is a planned addition

---

*Motion design policy — Nexus governance 2026*
