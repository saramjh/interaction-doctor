---
name: New conflict entry
about: Fill in one of the blank cells in the CONFLICTS.md matrix
title: "C? — <GestureA> ↔ <GestureB>"
labels: ["conflict", "needs-verification"]
assignees: []
---

<!--
Before filing: check the Matrix table in CONFLICTS.md. If the cell you're
filling already has a `C{n}` id (not `?` or `🚧`), open a "wrong diagnosis"
issue instead — this template is for cells that are currently blank.
-->

## Which two gestures

<!-- Match the axis labels used in CONFLICTS.md: Tap, DoubleTap, LongPress, Drag, Swipe, Scroll, Pinch -->

- Gesture A:
- Gesture B:
- Matrix cell (row × column):

## Reproduction environment

<!-- List every device you tested on. A single device is not enough to open this issue —
     see "Real-device verification" below. -->

| Device | OS / browser | Viewport | Input |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

## Symptom

<!-- What actually happens, in plain language. Bullet points, one observation each.
     This becomes the **Symptom** field in CONFLICTS.md if the entry is accepted. -->

-
-

## Cause you've confirmed, and its source

<!-- State the mechanism, and the primary source backing it. Per project rule,
     only W3C / WHATWG / MDN / platform-official docs count as a source —
     no blog posts, no Stack Overflow. If you're not sure of the cause yet,
     say so instead of guessing; a symptom report without a confirmed cause
     is still useful, but will be marked 🚧 until the cause is sourced. -->

**Cause:**

**Source(s):**
-

## Real-device verification

<!-- Required. This project does not accept entries verified only in a simulator
     or emulator — see research/measurements/README.md, "Simulators are not
     acceptable." Check off every device you actually tested on a physical unit. -->

- [ ] Desktop Chrome
- [ ] iOS Safari (physical device)
- [ ] Android Chrome (physical device)

## Raw measurement log

<!-- If you used or extended a harness in tools/, attach the raw output
     (paste inline or link a file) the way research/measurements/*.txt does.
     If no harness fits yet, describe how you reproduced it manually. -->
