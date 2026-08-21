# motion-design.md — Nexus Motion Policy

## Decision
motion.dev is added to the frontend stack. The design system's "Authority Through Restraint" principle is preserved — this library is here for functional motion, not decorative animation. Every animation must be triggered by a real data change or user action. Nothing plays just because a page loaded or a component mounted.

---

## What counts as functional motion (allowed)

**Audit trail entries**
New entries slide in from the top of the feed when they arrive via WebSocket. Short duration (~200ms), ease-out. Communicates that new data arrived without demanding attention the way a flash or color-pulse would.

**Spend-meter transitions**
The progress bar fill animates its width and color as spend_total updates. Color transition is the more important part — green → orange → red as the agent approaches and crosses the cap thresholds. This isn't decoration; the color change IS the signal.

**Kill switch state change**
On activation: the button shifts color, the glow intensifies (box-shadow), and agent cards drop to reduced opacity (fleet halted visual). On restoration: reverse. These transitions should feel fast and definitive — ~150ms. The motion confirms the action before the user even looks for confirmation text.

**Flagged/denied badge appearance**
When a transaction is flagged or denied, the badge entrance should be slightly weighted — not instant pop, not a slow fade, something between (~100ms ease-in). Denied feels more abrupt than flagged; that's intentional and fine.

---

## What is NOT allowed (even though the library is available)

- Page-entrance orchestration sequences (staggered hero text, cascading card reveals)
- Loading spinners or skeleton screens in content areas — if data isn't loaded, show a static placeholder or nothing
- Parallax or scroll-linked effects of any kind
- Any animation that plays without being triggered by a real data change or explicit user action
- Hover microanimations that aren't already present via CSS (don't add motion.dev hover effects just because you can)
- Looping idle animations on the dashboard when nothing is happening

---

## Integration notes
- Import only what's needed from motion.dev — don't pull in the full bundle for three specific transitions
- Prefer CSS variables for durations/easings so they're consistent with the existing design token system (`--transition-fast: 0.15s`, etc.)
- If a transition can be done cleanly with plain CSS, do it with plain CSS — motion.dev is for cases where it adds genuine control (e.g. exit animations, physics-based spring on the kill-switch glow) that CSS alone can't do cleanly
