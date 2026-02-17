# Cost Boxes Redesign

## Summary

Split single estimated cost box into two stacked boxes: Meta Ad Budget (blue) and Launchad Platform Fee (lime).

## File

`frontend/src/components/PublishView.tsx` lines 380-389

## Box 1 — Meta Ad Budget

- **Color:** Meta blue `#0668E1` (bg/10, border/30, text)
- **Label:** "Meta Ad Budget"
- **Amount:** `${budget * durationDays}` (e.g. $350)
- **Subtext:** `$50/day x 7 days`
- **Note:** "This budget is charged directly by Meta. Ensure your payment method is valid in your Meta Ads account."

## Box 2 — Launchad Platform Fee

- **Color:** Brand lime `#D4FF31` (current styling)
- **Label:** "Launchad Platform Fee"
- **Amount:** $29 (flat)

## Layout

- Stacked vertically (Box 1 on top, Box 2 below)
- No combined total

## Tailwind Config Change

Add `meta-blue: '#0668E1'` to `colors.brand` in `frontend/tailwind.config.js`.

## Complexity

SIMPLE
