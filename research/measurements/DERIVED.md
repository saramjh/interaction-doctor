# DERIVED.md — pooled figures

Every figure quoted in `CONFLICTS.md`, with its trial count and source files.
Pooled across all sessions for a device unless noted.

**v4 — final for this measurement round.** Synchronized line-for-line with
`CONFLICTS.md` v4. All ten documented conflicts (C1, C2, C3, C6, C8, C9, C10,
C11, C12, C13) have been re-derived directly from the raw files in this
directory; no figure here was carried forward from an unverified earlier draft.

---

## C10 — Drag ↔ Scroll

Harness: `tools/c10-drag-vs-scroll.html`
Sources: `c10-android.txt`, `c10-ipad.txt`, `c10-iphone.txt` (one session each)

| step | config / gesture        | Android       | iPadOS       | iOS          | pooled              |
| ---- | ----------------------- | ------------- | ------------ | ------------ | ------------------- |
| 1    | `auto` vertical         | cancelled 5/5 | 5/5          | 5/5          | **15/15 cancelled** |
| 2    | `auto` horizontal       | cancelled 5/5 | 4/5          | 2/6          | 11/16 cancelled     |
| 3    | `none` vertical         | drag 5/5      | 5/5          | 6/6          | **16/16 drag**      |
| 4    | `none`, gap zone        | scroll 3/3    | 3/3          | 2/3          | 8/9 scroll          |
| 5    | `pan-y` vertical        | cancelled 6/6 | 5/5          | 5/5          | **16/16 cancelled** |
| 6    | `pan-y` horizontal      | drag 5/5      | 5/5          | 5/5          | **15/15 drag**      |
| 7    | `pan-y` slow diagonal   | drag 4/13     | drag 0/14    | drag 0/5     | 4/32 drag           |
| 8    | `pan-x` vertical        | drag 5/5      | dead 6/7     | dead 5/5     | platform-split      |
| 9    | `manipulation` vertical | cancelled 6/6 | **both 6/6** | **both 5/5** | platform-split      |
| 10   | `none`, no capture      | drag 3/3      | 3/3          | 6/6          | **12/12 drag**      |

Step 4 iPhone: 1 of 3 trials invalid (gap zone not yet excluded from drag). 2 valid.
Step 1: scroll position uncontrolled — cancellation result only. See README issue 3.
Every cell above was recounted directly from the raw files during audit; all match.

**Simultaneous scroll under `manipulation`** (`scrollDuring`, px):

```
iPadOS   91 · 83 · 249 · 139 · 146 · 100      n=6
iOS      89 · 100 · 77 · 147 · 150            n=5
Android  0 in all 6 trials (pointer cancelled instead)
```

**Cancellation distance** — distance at the last `pointermove` before
`pointercancel`, **scoped to steps 1 and 5 only** (a straight vertical drag
under `auto` and under `pan-y`):

```
Android    8.1 – 10.3 px   n=11
iPadOS    10.5 – 13.5 px   n=10
iOS        5.5 – 14.5 px   n=10
```

⟳ **Correction from earlier drafts**, which reported "Android 8.1–10.5 n=37,
iPadOS 10.5–13.5 n=29, iOS 5.5–15.0 n=15." Those figures do not correspond to
any reproducible subset of the raw data. Pooling _every_ cancelled trial across
all ten steps (including the gap-zone step 4, the `pan-x` "dead" cancellations
in step 8, and `manipulation` in step 9 — categorically different cancellation
types, not activation-threshold measurements) gives Android 8.1–11.9 n=34,
iPadOS 10.5–330.7 n=37, iOS 5.5–150.4 n=24 — a much wider and less meaningful
range, since step 8's "dead" cancellations alone run up to 149 px. Steps 1+5
are the only two steps that isolate a single straight vertical drag being
cancelled near its activation point, so they are the correct scope for an
"activation threshold" statistic. This scope was re-derived from the raw files
during audit, not assumed.

`pointermove` counts per gesture — Android 4–145, iOS 2–10 across the full
dataset. iOS coalesces events, so its distances are **upper bounds**, not
thresholds. One iPhone trial (step 1) cancelled at **5.5 px** — below a
conventional 8 px activation threshold.

---

## C12 — Swipe ↔ Scroll

No separate measurement. Derived entirely from C10 steps 5–7.
Measured as horizontal drag, not as a swipe with a commit threshold.

🚧 Not measured: commit distance, velocity thresholds, `click` after a completed swipe.

---

## C3 — Tap ↔ Drag

Harness: `tools/c3-c6-tap-longpress-drag.html`, steps 1–6
Sources: `c3-c6-android.txt` (3 sessions, concatenated), `c3-c6-ipad.txt` (1 session),
`c3-c6-iphone.txt` (1 session), `c3-c6-macos.txt` (2 sessions, concatenated)

### Click cancellation distance

Steps 2 and 3, card target. Trials that produced `contextmenu` are excluded — those
were long presses, not taps.

**Android** — clean boundary, no overlap, n=46 (3 sessions pooled)

```
click fired    1.8 · 3.5 · 5.6 · 6.3 · 7.1 · 7.9 px          max 7.9    (n=6)
no click       8.2 – 62.2 px, spanning that range              min 8.2   (n=40)
```

Boundary lies between 7.9 and 8.2 px. Matches `ViewConfiguration.TOUCH_SLOP` = 8dp.

**iPadOS** — overlapping, n=20 (one session)

```
click fired    up to 42.0 px    (17 of 20 trials)
no click       from 20.6 px     (3 of 20 trials: 20.6, 35.0, 56.0 px)
overlap        20.6 – 42.0 px
```

**iOS** — overlapping, n=10

```
click fired    up to 44.8 px
no click       from 43.7 px
```

**macOS, mouse** — never suppressed by distance. 5/5 click at 39.7–49.1 px;
click observed after a 1195.6 px drag.

### Click after a large drag

| input | target       | drags | click fired |
| ----- | ------------ | ----- | ----------- |
| touch | card         | 37    | **0**       |
| touch | child button | 36    | **0**       |
| mouse | card         | 14    | **7**       |
| mouse | child button | 20    | **2**       |

Every mouse trial without a click released the cursor outside the element. The
child-button figure (20 drags, 2 clicks) excludes two near-zero-distance trials
in the second macOS session that were taps, not drags.

### Click delay after `pointerup` (`clickAt` minus `dur`, static tap, step 1)

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

Recounted across all three concatenated sessions, steps 2, 7, 8, 9:

```
range   494 – 513 ms
n       73
```

Never fired on iPadOS, iOS, or macOS in any trial.

### `user-select: none` (step 8)

|         | selection suppressed          | `contextmenu` suppressed   |
| ------- | ----------------------------- | -------------------------- |
| Android | yes, 0 `selectstart` in 17/17 | **no — 17/17 still fired** |
| iPadOS  | yes, `selChars` 0 in 14/14    | n/a (never fires)          |
| iOS     | yes, `selChars` 0 in 5/5      | n/a                        |

### `contextmenu` during long-press-then-drag (step 9, Android)

```
20 / 21 trials, all at ~500 ms, with the finger still moving
drag distances 80 – 372 px
```

### `pointercancel` during hold (Android, selection enabled — step 7)

```
6 / 37 trials, all at ~530 ms, shortly after selection engaged
0 / 17 with user-select: none (step 8)
```

### Long press → drag

Succeeded on all four platforms. iPadOS 9/9 and iOS 7/7 were clean with
`user-select: none` + `-webkit-touch-callout: none`. Android succeeded but fired
`contextmenu` mid-drag (see above).

### iOS selection length varies between trials

`selChars` was 6 in one step-7 trial and 12 in another (both held roughly
2.8–4.2 s). This shows final selected length is not fixed across separate
holds — it is not evidence of growth within a single hold, which was not
measured.

---

## C1 — Tap ↔ DoubleTap

Harness: `tools/c3-c6-tap-longpress-drag.html`, steps 11–12 (for `manipulation`
and `auto`), plus the original step 10 (for `none`)
Sources: `c3-c6-android-s11-12.txt`, `c3-c6-ipad-s11-12.txt`,
`c3-c6-iphone-s11-12.txt`, plus `c3-c6-android.txt` / `c3-c6-ipad.txt` /
`c3-c6-iphone.txt` step 10

### `dblclick`, by `touch-action` (pairs = tap-pairs, not raw individual taps)

|         | `manipulation` | `auto`    | `none`    |
| ------- | -------------- | --------- | --------- |
| Android | 6/6 pairs      | 3/5 pairs | 8/9 pairs |
| iPadOS  | 0/7 pairs      | 7/7 pairs | 0/3 pairs |
| iOS     | 0/10 pairs     | 4/4 pairs | 0/4 pairs |

⟳ **Correction**: the iPadOS `none` cell previously read "0/6". That was the raw
individual-tap count (6 taps = 3 pairs), inconsistent with the other two
platforms in the same row, which correctly reported pair counts (9 pairs = 18
taps for Android; 4 pairs = 8 taps for iOS). Corrected to **0/3 pairs** to match
that convention.

Safari suppresses `dblclick` under `manipulation` identically to `none`. Chrome
on Android fires it under all three values.

Desktop mouse: 2/3 pairs on macOS Chrome.

### Tap delay, first vs second (`click` timestamp minus `pointerup`)

```
                 first tap    second tap
iPadOS             ~36 ms        ~4 ms
iOS                ~36 ms        ~3 ms
Android           2 – 5 ms      2 – 5 ms
```

🚧 Double-tap zoom not measured. The harness page is `width=device-width` with
no horizontally overflowing content, so no zoom target existed to test against.

---

## C2 — Tap ↔ LongPress

Harness: `tools/c3-c6-tap-longpress-drag.html`, steps 1, 7, 8
Sources: same as C3/C6 — reuses those figures directly, no separate measurement.

### `click` after a 1–2 s hold, desktop mouse

```
10/10 trials fired a plain click, 1552 – 2242 ms
```

---

## C8 — LongPress ↔ Scroll

Harness: `tools/c8-c9-c11-c13-scroll-swipe-pinch.html`, steps 1–3
Sources: `c8-c9-c11-c13-android.txt`, `c8-c9-c11-c13-ipad.txt`, `c8-c9-c11-c13-iphone.txt`
(one session each)

### Touching down during momentum scroll, held 1.5 s (step 2)

|                                           | Android | iPadOS | iOS  |
| ----------------------------------------- | ------- | ------ | ---- |
| cancelled within ~100 ms                  | 10/18   | 8/9    | 9/10 |
| long-press signal fired despite motion    | 4/18    | 0/9    | 0/10 |
| ambiguous — held, minor scroll, no signal | 4/18    | 1/9    | 1/10 |

Recounted trial-by-trial during audit; Android's 10/4/4 split over 18 trials
confirmed exact. 🚧 The four Android "ambiguous" trials are n=4 — flagged as a
possible pattern, not confirmed.

### Static hold, list fully stopped (steps 1, 3)

Reproduces C6: Android `contextmenu` 11/11 (steps 1+3 combined) at ~500 ms;
iPadOS and iOS 0/13, silent selection instead. `touch-action` made no difference.

---

## C9 — Drag ↔ Swipe

Harness: `tools/c8-c9-c11-c13-scroll-swipe-pinch.html`, steps 4–6
Sources: same three touch files, plus `c8-c9-c11-c13-macos.txt` for the mouse row

`touch-action: pan-y` throughout.

| gesture               | Android       | iPadOS        | iOS           |
| --------------------- | ------------- | ------------- | ------------- |
| fast horizontal flick | 0/8 cancelled | 3/7 cancelled | 2/6 cancelled |
| slow horizontal drag  | 0/5 cancelled | 3/7 cancelled | 2/6 cancelled |
| slow diagonal         | 0/5 cancelled | 5/5 cancelled | 5/5 cancelled |

Mouse (macOS): 0/15 cancelled across all three gesture shapes.

No axis-classification flip observed mid-gesture in any C9 trial on any platform.

---

## C11 — Drag ↔ Pinch

Harness: same, steps 7–8
Sources: `c8-c9-c11-c13-android.txt`, `c8-c9-c11-c13-ipad.txt`, `c8-c9-c11-c13-iphone.txt`

|                                                   | Android | iPadOS | iOS  |
| ------------------------------------------------- | ------- | ------ | ---- |
| `none` — pinch scale captured                     | 5/6     | 4/6    | 3/6  |
| `none` — stayed single-pointer drag               | 1/6     | 2/6    | 3/6  |
| `pan-y` — cancelled near-instantly on 2nd pointer | 0/6     | 4/12   | 8/12 |
| `pan-y` — pinch scale captured despite `pan-y`    | 4/6     | 3/12   | 0/12 |

🚧 Small sample, manual two-finger placement imprecise by hand. Direction of
each platform difference is more reliable than the exact ratio.

Not measurable on desktop (single pointer, or no Pointer Events from trackpad — see C13).

---

## C13 — Scroll ↔ Pinch

Harness: same, steps 9–11
Sources: `c8-c9-c11-c13-android.txt`, `c8-c9-c11-c13-ipad.txt`, `c8-c9-c11-c13-iphone.txt`,
`c8-c9-c11-c13-macos.txt`

Page zoom (`visualViewport.scale` change >2%) during a two-finger pinch-out:

| `touch-action` | Android                                         | iPadOS        | iOS            |
| -------------- | ----------------------------------------------- | ------------- | -------------- |
| `pan-y`        | **zoomed 6/6** valid (1 invalid trial excluded) | zoomed 0/5    | zoomed 0/8     |
| `none`         | zoomed 0/5                                      | zoomed 0/6    | zoomed 0/5     |
| `auto`         | zoomed 4/5                                      | zoomed 6/6 🚧 | zoomed ≥2/8 🚧 |

🚧 `auto` row: `visualViewport.scale` was not reset between trials on iPadOS and
iOS. Treat exact ratios as indicative; at least one clean zoom event was captured
on each platform under `auto`.

**Flagship divergence**: under `pan-y`, Android behaves like `auto` (zoom
permitted, 6/6) while iOS/iPadOS behave like `none` (zoom blocked, 0/13 combined)
— opposite readings of the identical CSS declaration.

### Trackpad (macOS)

0/17 attempts across all three `touch-action` values produced any Pointer Event
from a second contact. Trackpad pinch routes through `wheel` + `ctrlKey`, not
Pointer Events — out of this harness's coverage.

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
