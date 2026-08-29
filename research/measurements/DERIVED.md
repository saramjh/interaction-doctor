# DERIVED.md — pooled figures

Every figure quoted in `CONFLICTS.md`, with its trial count and source files.
Pooled across all sessions for a device unless noted.

---

## C10 — Drag ↔ Scroll

Harness: `tools/c10-drag-vs-scroll.html`
Sources: `c10-android.txt`, `c10-ipad.txt`, `c10-iphone.txt`

| step | config / gesture | Android | iPadOS | iOS | pooled |
|---|---|---|---|---|---|
| 1 | `auto` vertical | cancelled 5/5 | 5/5 | 5/5 | **15/15 cancelled** |
| 2 | `auto` horizontal | cancelled 5/5 | 4/5 | 2/6 | 11/16 cancelled |
| 3 | `none` vertical | drag 5/5 | 5/5 | 6/6 | **16/16 drag** |
| 4 | `none`, gap zone | scroll 3/3 | 3/3 | 2/3 | 8/9 scroll |
| 5 | `pan-y` vertical | cancelled 6/6 | 5/5 | 5/5 | **16/16 cancelled** |
| 6 | `pan-y` horizontal | drag 5/5 | 5/5 | 5/5 | **15/15 drag** |
| 7 | `pan-y` slow diagonal | drag 4/13 | drag 0/14 | drag 0/5 | 4/32 drag |
| 8 | `pan-x` vertical | drag 5/5 | dead 6/7 | dead 5/5 | platform-split |
| 9 | `manipulation` vertical | cancelled 6/6 | **both 6/6** | **both 5/5** | platform-split |
| 10 | `none`, no capture | drag 3/3 | 3/3 | 6/6 | **12/12 drag** |

Step 4 iPhone: 1 of 3 trials invalid (gap zone not yet excluded from drag). 2 valid.
Step 1: scroll position uncontrolled — cancellation result only. See README item 3.

**Simultaneous scroll under `manipulation`** (`scrollDuring`, px):

```
iPadOS   91 · 83 · 249 · 139 · 146 · 100      n=6
iOS      89 · 100 · 77 · 147 · 150            n=5
Android  0 in all 6 trials (pointer cancelled instead)
```

**Cancellation distance** — distance at the last `pointermove` before `pointercancel`:

```
Android   8.1 – 10.5 px    n=37
iPadOS   10.5 – 13.5 px    n=29   (step 7: dy clamped at ±11 px in 14/14)
iOS       5.5 – 15.0 px    n=15
```

`pointermove` counts per gesture — Android 4–145, iOS 2–10. iOS coalesces events, so
its distances are **upper bounds**, not thresholds. One iPhone trial cancelled at
5.5 px, below a conventional 8 px activation threshold.

---

## C12 — Swipe ↔ Scroll

No separate measurement. Derived entirely from C10 steps 5–7.
Measured as horizontal drag, not as a swipe with a commit threshold.

🚧 Not measured: commit distance, velocity thresholds, `click` after a completed swipe.

---

## C3 — Tap ↔ Drag

Harness: `tools/c3-c6-tap-longpress-drag.html`, steps 1–6
Sources: `c3c6-android-{1,2,3}.txt`, `c3c6-ipad-{1,2}.txt`, `c3c6-iphone.txt`,
`c3c6-macos-{1,2}.txt`

### Click cancellation distance

Steps 2 and 3, card target. Trials that produced `contextmenu` are excluded — those
were long presses, not taps.

**Android** — clean boundary, no overlap, n=22

```
click fired    1.8 · 3.5 · 5.6 · 6.3 · 7.1 · 7.9 px          max 7.9
no click       8.2 · 9.9 · 10.2 · 10.7 · 10.8 · 11.2 · 11.2
               11.9 · 13.0 · 13.5 · 13.7 · 15.6 · 15.6
               16.5 · 19.0 · 21.8 px                          min 8.2
```

Boundary lies between 7.9 and 8.2 px. Matches `ViewConfiguration.TOUCH_SLOP` = 8dp.

**iPadOS** — overlapping, n=39

```
click fired    up to 42.9 px
no click       from 20.6 px
overlap        20.6 – 42.9 px
```

**iOS** — overlapping, n=10

```
click fired    up to 44.8 px
no click       from 43.7 px
```

**macOS, mouse** — never suppressed by distance. 5/5 click at 39.7–49.1 px;
click observed after a 1195.6 px drag.

### Click after a large drag

| input | target | drags | click fired |
|---|---|---|---|
| touch | card | 37 | **0** |
| touch | child button | 36 | **0** |
| mouse | card | 14 | **7** |
| mouse | child button | 20 | **2** |

Every mouse trial without a click released the cursor outside the element.
Two additional mouse trials on the child button were near-zero-distance taps and
correctly produced `childClick`; they are excluded from the drag counts above.

> Correction to `C3-section.md`: the child-button mouse row currently reads
> `18 / 2`. The correct count is **20 / 2**.

### Click delay after `pointerup`

```
Android    1 – 6 ms      n=5
macOS      0 – 2 ms      n=5
iPadOS    35 – 41 ms     n=5
iOS       32 – 55 ms     n=5
```

---

## C6 — LongPress ↔ Drag

Harness: same, steps 7–9. Same sources.

### `contextmenu` timing (Android only)

```
range   494 – 513 ms
n       ~60 trials across three sessions and steps 2, 7, 8, 9
spread  19 ms
```

Never fired on iPadOS, iOS, or macOS in any trial.

> Correction to `C6-section.md`: currently reads `495–513 ms, 30/30`.
> The correct figure is **494–513 ms, n ≈ 60**.

### `user-select: none` (step 8)

| | selection suppressed | `contextmenu` suppressed |
|---|---|---|
| Android | yes, 0 `selectstart` in 17/17 | **no — 17/17 still fired** |
| iPadOS | yes, `selChars` 0 in 14/14 | n/a (never fires) |
| iOS | yes, `selChars` 0 in 5/5 | n/a |

> Correction to `C6-section.md`: currently reads `12/12 still fired`.
> The correct figure is **17/17**.

### `contextmenu` during long-press-then-drag (step 9, Android)

```
19 / 21 trials, all at ~500 ms, with the finger still moving
drag distances 80 – 372 px
```

> Correction to `C6-section.md`: currently reads `11/13`. Correct figure is **19/21**.

### `pointercancel` during hold (Android, selection enabled)

```
6 / 37 trials, all at ~530 ms, shortly after selection engaged
0 / 17 with user-select: none
```

> Correction to `C6-section.md`: currently reads `4/21`. Correct figure is **6/37**.

### Long press → drag

Succeeded on all four platforms. iPadOS 9/9 and iOS 7/7 were clean with
`user-select: none` + `-webkit-touch-callout: none`. Android succeeded but fired
`contextmenu` mid-drag (see above).

### iOS selection growth

`selChars` rose from 6 to 12 within a single 2.8 s hold (`c3c6-ipad-2.txt`, step 7
trial 3). Selection expands while the finger remains down.

---

## C1 — Tap ↔ DoubleTap (data available, section not yet written)

Step 10. Target was the child button in every session — see README item 5.

| | tap pairs | `dblclick` fired |
|---|---|---|
| Android | 9 | **8** |
| iPadOS | 6 | **0** |
| iOS | 4 | **0** |
| macOS Chrome | 3 | 2 |

🚧 Double-tap zoom not measured. `touch-action: none` was in force throughout,
which suppresses it by definition.

---

## Figures NOT derived from measurement

Stated in `CONFLICTS.md` from primary sources only, not observed here:

- `touch-action` value semantics — W3C Pointer Events Level 3
- `pointercancel` suppression sequence — W3C Pointer Events Level 3
- default passive value for `touchstart` / `touchmove` — WHATWG DOM
- compositor-thread scrolling — Chrome Developers
- `TOUCH_SLOP = 8dp`, `PAGING_TOUCH_SLOP`, `DOUBLE_TAP_SLOP` — AOSP `ViewConfiguration`
- SwiftUI `DragGesture(minimumDistance:)` default of 10 pt — Apple

See `research/c10-sources.md`.
