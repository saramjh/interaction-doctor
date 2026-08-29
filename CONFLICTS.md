# CONFLICTS.md

> Entries are verified on real devices (desktop Chrome, iOS Safari,
> Android Chrome) before being marked complete. Entries still marked
> 🚧 have not been verified and are excluded from the skill.

## Matrix

|               | Tap | DoubleTap | LongPress | Drag | Swipe | Scroll | Pinch |
| ------------- | --- | --------- | --------- | ---- | ----- | ------ | ----- |
| **Tap**       | —   | C1        | C2        | C3   | ?     | ?      | ?     |
| **DoubleTap** | C1  | —         | ?         | ?    | ?     | ?      | ?     |
| **LongPress** | C2  | ?         | —         | C6   | ?     | C8     | ?     |
| **Drag**      | C3  | ?         | C6        | —    | C9    | C10    | C11   |
| **Swipe**     | ?   | ?         | ?         | C9   | —     | C12    | ?     |
| **Scroll**    | ?   | ?         | C8        | C10  | C12   | —      | C13   |
| **Pinch**     | ?   | ?         | ?         | C11  | ?     | C13    | —     |

## Legend

| Symbol | Meaning                                 |
| ------ | --------------------------------------- |
| `C{n}` | documented conflict — see section below |
| `?`    | not yet assessed                        |
| `—`    | not applicable (verified)               |
| `ok`   | no conflict (verified)                  |

---

### C1 — Tap ↔ DoubleTap

**Symptom**
🚧 unverified

**Cause**
🚧 unverified

**Resolution**
🚧 unverified

**Precedence**
🚧 unverified

**In the wild**
🚧 unverified

**How to verify**
🚧 unverified

**Verified on**
🚧 unverified

**References**
🚧 unverified

---

### C2 — Tap ↔ LongPress

**Symptom**
🚧 unverified

**Cause**
🚧 unverified

**Resolution**
🚧 unverified

**Precedence**
🚧 unverified

**In the wild**
🚧 unverified

**How to verify**
🚧 unverified

**Verified on**
🚧 unverified

**References**
🚧 unverified

---

### C3 — Tap ↔ Drag

**Symptom**
🚧 unverified

**Cause**
🚧 unverified

**Resolution**
🚧 unverified

**Precedence**
🚧 unverified

**In the wild**
🚧 unverified

**How to verify**
🚧 unverified

**Verified on**
🚧 unverified

**References**
🚧 unverified

---

### C4 — Tap ↔ Swipe 🚧 not yet documented

**Symptom**
🚧 unverified

**Cause**
🚧 unverified

**Resolution**
🚧 unverified

**Precedence**
🚧 unverified

**In the wild**
🚧 unverified

**How to verify**
🚧 unverified

**Verified on**
🚧 unverified

**References**
🚧 unverified

---

### C5 — DoubleTap ↔ Pinch 🚧 not yet documented

**Symptom**
🚧 unverified

**Cause**
🚧 unverified

**Resolution**
🚧 unverified

**Precedence**
🚧 unverified

**In the wild**
🚧 unverified

**How to verify**
🚧 unverified

**Verified on**
🚧 unverified

**References**
🚧 unverified

---

### C6 — LongPress ↔ Drag

**Symptom**
🚧 unverified

**Cause**
🚧 unverified

**Resolution**
🚧 unverified

**Precedence**
🚧 unverified

**In the wild**
🚧 unverified

**How to verify**
🚧 unverified

**Verified on**
🚧 unverified

**References**
🚧 unverified

---

### C7 — LongPress ↔ Swipe 🚧 not yet documented

**Symptom**
🚧 unverified

**Cause**
🚧 unverified

**Resolution**
🚧 unverified

**Precedence**
🚧 unverified

**In the wild**
🚧 unverified

**How to verify**
🚧 unverified

**Verified on**
🚧 unverified

**References**
🚧 unverified

---

### C8 — LongPress ↔ Scroll

**Symptom**
🚧 unverified

**Cause**
🚧 unverified

**Resolution**
🚧 unverified

**Precedence**
🚧 unverified

**In the wild**
🚧 unverified

**How to verify**
🚧 unverified

**Verified on**
🚧 unverified

**References**
🚧 unverified

---

### C9 — Drag ↔ Swipe

**Symptom**
🚧 unverified

**Cause**
🚧 unverified

**Resolution**
🚧 unverified

**Precedence**
🚧 unverified

**In the wild**
🚧 unverified

**How to verify**
🚧 unverified

**Verified on**
🚧 unverified

**References**
🚧 unverified

---

### C10 — Drag ↔ Scroll

**Symptom**

- The item moves, but the page or list scrolls at the same time.
- Trying to scroll the list drags an item instead.
- Drag works on desktop, does nothing on a phone.
- Drag starts, then freezes mid-gesture and the item never returns to place.
- Setting `touch-action: none` fixes dragging but the list stops scrolling entirely.

**Cause**

Touch scrolling is owned by the browser before any JavaScript runs. When a gesture
starts, the browser intersects the `touch-action` values of the touched element and
its ancestors up to the first containing scrolling element, and that decision is
fixed for the rest of the gesture — changing `touch-action` afterwards has no effect
on the gesture in progress.

`preventDefault()` cannot win this race. MDN states plainly that applications must
declare `touch-action` so the browser knows the intent _before any event listeners
have been invoked_. Chrome's scrolling intervention explains the underlying reason:
the browser must wait for a non-passive listener to finish just to learn whether it
will call `preventDefault()`, and with no listener in the way the compositor thread
produces frames independently of the main thread. Scrolling therefore starts on a
thread your handler is not on.

When the browser takes the pointer for viewport manipulation, the spec requires it
to suppress the pointer event stream: fire `pointercancel`, then `pointerout`,
`pointerleave`, and implicitly release pointer capture. This is not a browser quirk —
it is mandated behaviour, and it is why a drag that is "stuck" never receives
`pointerup`.

`manipulation` does not restrict panning at all. It only suppresses behaviours that
depend on multiple activations within a time window, such as double-tap to zoom. It
is not a drag-safe value, and on iOS it produces simultaneous drag and scroll
(see Precedence).

**Resolution**

Choose by which axis the drag needs.

```css
/* Horizontal drag inside a vertically scrolling list */
.item {
	touch-action: pan-y;
}

/* Drag owns the pointer completely (canvas, free-position dragging) */
.item {
	touch-action: none;
}
```

- `pan-y` — vertical scrolling still works, horizontal drag is yours.
  Measured: 15/15 horizontal drags succeeded across three devices.
- `none` — drag always wins. Measured: 16/16 drags succeeded, and 12/12 still
  succeeded with `setPointerCapture` disabled, so capture is not a prerequisite.
- `pan-x` — do not use on a vertically scrolling list. Android hands the vertical
  gesture to JavaScript, but iOS cancels the pointer _and does not scroll_, leaving
  the gesture dead in both directions (11/12 trials on iPhone and iPad).
- `manipulation` — never use on a draggable element. See Precedence.

The cost of `none` is real but narrower than it looks. `none` only suppresses
scrolling for gestures that _begin on that element_. Touching the container padding
between items still scrolls normally (8/9 trials). In a dense list, however, every
touch lands on an item, so the user experiences it as "the list will not scroll" —
this is exactly the trade-off reported in dnd-kit #453.

**Vertical drag in a vertical list has no clean CSS answer.** `pan-y` cancels every
vertical drag (16/16 across three devices), and `none` kills list scrolling. Any
vertical reorder must therefore distinguish the two gestures by something other
than direction — typically a hold delay before drag activation, which is the
approach dnd-kit's touch sensor takes.

Always handle `pointercancel`. It is the only signal you get when the browser wins,
and `pointerup` will not follow.

**Precedence**

Measured, not derived from spec. Three devices, ten-step protocol, 5 trials per step.

| touch-action       | gesture          | Android 10 / Chrome 143 | iPadOS 26.6 / Safari | iOS 18.7 / Safari |
| ------------------ | ---------------- | ----------------------- | -------------------- | ----------------- |
| `auto`\*           | vertical         | cancelled 5/5           | cancelled 5/5        | cancelled 5/5     |
| `auto`             | horizontal       | cancelled 5/5           | cancelled 4/5        | cancelled 2/6     |
| `none`             | vertical         | drag 5/5                | drag 5/5             | drag 6/6          |
| `none`             | on container gap | scroll 3/3              | scroll 3/3           | scroll 2/3        |
| `pan-y`            | vertical         | cancelled 6/6           | cancelled 5/5        | cancelled 5/5     |
| `pan-y`            | horizontal       | drag 5/5                | drag 5/5             | drag 5/5          |
| `pan-y`            | slow diagonal    | **drag 4/13**           | cancelled 14/14      | cancelled 5/5     |
| `pan-x`            | vertical         | drag 5/5                | dead 6/7             | dead 5/5          |
| `manipulation`     | vertical         | cancelled 6/6           | **both 6/6**         | **both 5/5**      |
| `none`, no capture | vertical         | drag 3/3                | drag 3/3             | drag 6/6          |

\* Scroll position was not controlled in this run — every trial started with the
list at the top. Only the cancellation result is comparable across platforms.

Three findings that only appear when you test more than one platform:

1. **`manipulation` behaves oppositely on iOS and Android.** Android cancels the
   pointer like `auto`. iOS and iPadOS let the drag continue _while the container
   scrolls_, 11/11 trials, with 77–249 px of scroll during the gesture and no
   `pointercancel`. Testing only on Android will never reveal this.

2. **Slow diagonal movement is resolved differently.** Under `pan-y`, Android lets a
   slow diagonal drag survive — 4 of 13 trials stayed with JavaScript, including one
   at 5.5 s. iOS cancelled 19/19 regardless of speed, always at roughly 11 px of
   vertical travel. This is the mechanism behind vaul #358: on Android a diagonal
   gesture can begin a drag that the browser may still take away later, leaving the
   element mid-transform.

3. **Under `auto`, horizontal drag is not uniformly blocked.** Android cancelled all
   5 horizontal attempts even with no horizontal scroll container present. iOS
   allowed 4 of 6 through. Do not rely on `auto` for horizontal dragging either way.

Observed cancellation thresholds — distance at the last `pointermove` before
`pointercancel`:

```
Android    8.1 – 10.5 px    (consistent with ViewConfiguration TOUCH_SLOP = 8dp)
iPadOS    10.5 – 13.5 px
iOS        5.5 – 15.0 px
```

Read the iOS figures as upper bounds only. iOS reported 2–10 `pointermove` events
per gesture against Android's 10–145, so events are coalesced and the true
cancellation point may be earlier. One iPhone trial cancelled at **5.5 px** —
below a conventional 8 px activation threshold. **Do not assume your own slop will
fire before the browser cancels.**

Apple publishes no system-level equivalent of Android's touch slop constant. The
closest public number is SwiftUI's `DragGesture(minimumDistance:)` default of 10
points, which is a framework parameter and not an OS-wide threshold.

**In the wild**

- [dnd-kit #453](https://github.com/clauderic/dnd-kit/issues/453) — with `touch-action: none`
  the item drags but the list will not scroll; with `auto` the draggable gets stuck.
  Both halves of this trade-off reproduced.
- [motion #1506](https://github.com/motiondivision/motion/issues/1506) — a scroll input
  being read as a drag input on mobile reorder.
- [motion #185](https://github.com/motiondivision/motion/issues/185) — scrolling a list of
  horizontally draggable items produces small unwanted drags on each item touched.
- [vaul #358](https://github.com/emilkowalski/vaul/issues/358) — diagonal movement starts a
  drag that does not return to position after release. See Precedence finding 2.
- [vaul #555](https://github.com/emilkowalski/vaul/issues/555) — the iOS dock opening fires
  `pointercancel` and the drawer is left stranded between snap points.
- [dnd-kit #1955](https://github.com/clauderic/dnd-kit/issues/1955) — dragging cannot be
  initiated on some Android devices; touches are read as scroll.

**How to verify**

Use `tools/c10-drag-vs-scroll.html` on a real device over LAN. Ten steps, 3–5
trials each; the page reports a verdict 600 ms after release so that scrolling
which begins _after_ `pointercancel` is still counted.

Minimum reproduction without the harness:

1. Build a vertically scrolling list of draggable items.
2. Set `touch-action: auto` and drag an item down. The drag will not survive.
3. Set `none` and drag. The drag works; now try to scroll the list by touching an
   item — it will not scroll.
4. Set `pan-y` and drag horizontally, then vertically. Horizontal drags, vertical
   scrolls.
5. Set `manipulation` and drag vertically **on iOS**. Item and list move together.

Note: start each trial with the list scrolled to the middle. At the top or bottom
edge the container cannot scroll in one direction, and iOS rubber-band overscroll
still moves `scrollTop` while Android does not — the two are not comparable.

**Verified on**

- Android 10 / Chrome 143 · 412×892 @3.5 · 2026-08-29
- iPadOS 26.6 / Safari 26.6 (iPad Pro) · 1024×1366 @2 · 2026-08-29
- iOS 18.7 / Safari (iPhone) · 375×667 @2 · 2026-08-29

Desktop pointer input is unaffected by `touch-action` and is not covered here.

**References**

- [W3C Pointer Events Level 3 — the `touch-action` CSS property](https://www.w3.org/TR/pointerevents3/)
- [W3C Pointer Events Level 3 — suppressing a pointer event stream](https://www.w3.org/TR/pointerevents3/)
- [W3C Pointer Events Level 3 — pointer capture](https://www.w3.org/TR/pointerevents3/)
- [MDN — `touch-action`](https://developer.mozilla.org/en-US/docs/Web/CSS/touch-action)
- [Chrome Developers — making touch scrolling fast by default](https://developer.chrome.com/blog/scrolling-intervention)
- [Chrome Developers — inside look at modern web browser, part 4](https://developer.chrome.com/blog/inside-browser-part4)
- [WHATWG DOM — the default passive value](https://dom.spec.whatwg.org/#the-default-passive-value)
- [Android — `ViewConfiguration`](https://developer.android.com/reference/android/view/ViewConfiguration)
- [Apple — `DragGesture(minimumDistance:coordinateSpace:)`](<https://developer.apple.com/documentation/swiftui/draggesture/init(minimumdistance:coordinatespace:)>)

---

### C11 — Drag ↔ Pinch

**Symptom**
🚧 unverified

**Cause**
🚧 unverified

**Resolution**
🚧 unverified

**Precedence**
🚧 unverified

**In the wild**
🚧 unverified

**How to verify**
🚧 unverified

**Verified on**
🚧 unverified

**References**
🚧 unverified

---

### C12 — Swipe ↔ Scroll

**Symptom**

- Swiping a row sideways scrolls the list instead.
- Scrolling the list makes rows twitch sideways as the finger passes over them.
- Swipe-to-delete works on desktop with a mouse, does nothing on a phone.
- The row starts sliding, then stops partway and stays there.

**Cause**

A swipe is a horizontal drag with a commit threshold. The axis contention is
therefore identical to [C10](#c10--drag--scroll): the browser decides whether the
gesture belongs to scrolling before any listener runs, and takes the pointer stream
away with `pointercancel` when it does.

The difference from C10 is only in intent. A swipe needs one axis, not both, which
means `touch-action` can express the split exactly — unlike vertical dragging in a
vertical list, which has no clean CSS answer.

**Resolution**

```css
.swipeable-row {
	touch-action: pan-y;
}
```

Vertical scrolling stays with the browser, horizontal movement is yours. The Pointer
Events spec gives this exact case as its own worked example for `pan-y`: a carousel
declaring `pan-y` so it receives pointer events for horizontal panning without
interfering with vertical panning of the document.

Do not use `none` here. It buys nothing a swipe needs and kills list scrolling for
every touch that starts on a row — see C10 for the measured cost.

Gate the swipe on horizontal intent before moving anything:

```js
if (!active && Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 8) {
	active = true
}
```

Without this gate, a vertical scroll that begins with a few pixels of horizontal
wobble translates every row the finger crosses. That is the failure reported in
motion #185.

Handle `pointercancel` by returning the row to its resting position. A swipe that is
interrupted mid-travel and left in place is the same defect as a stuck drag.

**Precedence**

Measured under `touch-action: pan-y`, same protocol and devices as C10.

| gesture       | Android 10 / Chrome 143 | iPadOS 26.6 / Safari | iOS 18.7 / Safari |
| ------------- | ----------------------- | -------------------- | ----------------- |
| horizontal    | drag 5/5                | drag 5/5             | drag 5/5          |
| vertical      | cancelled 6/6           | cancelled 5/5        | cancelled 5/5     |
| slow diagonal | drag 4/13               | cancelled 14/14      | cancelled 5/5     |

Horizontal and vertical resolve cleanly and identically on all three platforms.
**Diagonal does not.** Android lets a slow diagonal gesture stay with JavaScript in
roughly a third of trials, so a row can begin sliding during what the user intends
as a scroll — and the browser may still reclaim the pointer later. iOS cancels
diagonals outright. This is why the horizontal-intent gate above is required rather
than optional: `pan-y` alone does not prevent a sideways leak on Android.

**In the wild**

- [motion #185](https://github.com/motiondivision/motion/issues/185) — scrolling a list of
  horizontally draggable elements produces a small horizontal drag on each element
  the finger touches.
- [vaul #358](https://github.com/emilkowalski/vaul/issues/358) — diagonal movement starts a
  drag that does not return to position after release.

**How to verify**

Use `tools/c10-drag-vs-scroll.html`, steps 5–7. The measurement is the same: a
horizontal drag inside a vertically scrolling container under `pan-y`.

Minimum reproduction:

1. Build a vertically scrolling list with rows that translate on horizontal drag.
2. Set `touch-action: pan-y` on the rows.
3. Swipe a row sideways — it moves; scroll vertically — the list scrolls.
4. Scroll vertically starting with a slight sideways wobble. Without a
   horizontal-intent gate, rows shift as the finger passes.
5. On Android, move slowly on a diagonal. The row may follow the finger.

**Verified on**

- Android 10 / Chrome 143 · 412×892 @3.5 · 2026-08-29
- iPadOS 26.6 / Safari 26.6 (iPad Pro) · 1024×1366 @2 · 2026-08-29
- iOS 18.7 / Safari (iPhone) · 375×667 @2 · 2026-08-29

Measured as horizontal drag, not as a full swipe interaction. 🚧 Not yet verified:
commit-distance and velocity thresholds for completing a swipe, and whether a
`click` fires on the row after a completed swipe (see C3).

**References**

- [W3C Pointer Events Level 3 — the `touch-action` CSS property](https://www.w3.org/TR/pointerevents3/)
- [W3C Pointer Events Level 3 — suppressing a pointer event stream](https://www.w3.org/TR/pointerevents3/)
- [MDN — `touch-action`](https://developer.mozilla.org/en-US/docs/Web/CSS/touch-action)

---

### C13 — Scroll ↔ Pinch

**Symptom**
🚧 unverified

**Cause**
🚧 unverified

**Resolution**
🚧 unverified

**Precedence**
🚧 unverified

**In the wild**
🚧 unverified

**How to verify**
🚧 unverified

**Verified on**
🚧 unverified

**References**
🚧 unverified
