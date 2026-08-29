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

- Dragging a card also triggers its click handler — the item opens after you drop it.
- A tap does nothing on Android but works on iPhone, or the reverse.
- A button inside a draggable card stops responding once dragging is added.
- The first tap on a card feels sluggish on iOS.

**Cause**

Tap and drag share the same pointer stream. Something has to decide, after the
gesture ends, whether it was a tap. Browsers already make that decision for touch
input — but the rule differs by platform, and for mouse input there is effectively
no rule at all.

On touch, the browser suppresses the synthetic `click` once the pointer has moved
past its own slop distance. On Android that distance is exactly the platform
constant; on iOS it is larger and not purely distance-based.

On desktop, `click` is dispatched whenever `mousedown` and `mouseup` land in the
same element, regardless of how far the cursor travelled in between. A 1,195 px
drag still produced a `click` in measurement. The browser gives you nothing here —
you must suppress it yourself.

**Resolution**

Track whether the gesture exceeded a movement threshold, and gate the click on it.

```js
let moved = false

el.addEventListener("pointerdown", (e) => {
	moved = false
	start = { x: e.clientX, y: e.clientY }
})

el.addEventListener("pointermove", (e) => {
	if (Math.hypot(e.clientX - start.x, e.clientY - start.y) > 8) moved = true
})

el.addEventListener("click", (e) => {
	if (moved) {
		e.preventDefault()
		e.stopPropagation()
		return
	}
	onTap()
})
```

Do not skip this on the assumption that the browser handles it. It handles touch and
does nothing for mouse.

Use 8 px. Android's browser uses exactly that value, so matching it means your
handler and the browser agree on Android instead of disagreeing in the gap between
two thresholds.

Set `user-select: none` on the draggable element. On desktop, dragging across text
starts a selection, which suppresses `click` unpredictably and produced inconsistent
results in measurement until selection was disabled.

**Precedence**

Distance at which the synthetic `click` stops firing. Values pooled across three
sessions per device.

|                            | click fires up to | click suppressed from | boundary              |
| -------------------------- | ----------------- | --------------------- | --------------------- |
| Android 10 / Chrome 143    | 7.9 px            | 8.2 px                | **exact, no overlap** |
| iPadOS 26.6 / Safari       | 42.9 px           | 20.6 px               | overlapping 20–43 px  |
| iOS 18.7 / Safari          | 44.8 px           | 43.7 px               | overlapping 43–45 px  |
| macOS / Chrome 142 (mouse) | 1195 px           | —                     | **never suppressed**  |

Android's boundary falls exactly between 7.9 px and 8.2 px with no exceptions across
roughly 40 trials, matching `ViewConfiguration.TOUCH_SLOP` = 8dp. Treat that constant
as the real browser behaviour, not just an Android UI value.

iOS has no single distance threshold. A 20.6 px gesture was suppressed while a
42.9 px one was not, in the same session. Suppressed trials frequently coincided
with text selection engaging (`selChars > 0`), which suggests selection arbitration
participates in the decision. **Do not derive an iOS slop constant from these
numbers.**

After a long drag, touch platforms suppress `click` completely:

|                                   | drags | click fired |
| --------------------------------- | ----- | ----------- |
| touch, on the card                | 37    | **0**       |
| touch, starting on a child button | 36    | **0**       |
| mouse, on the card                | 14    | **7**       |
| mouse, starting on a child button | 18    | 2           |

Every mouse trial that did _not_ fire `click` was one where the cursor was released
outside the element. When the cursor stayed inside, `click` fired at any distance.
The child button is small, so a drag almost always ends outside it — which is why
child clicks appear to vanish under dragging.

Click timing after `pointerup` also differs:

```
Android    2 – 6 ms      effectively immediate
macOS       1 – 2 ms      effectively immediate
iPadOS     32 – 41 ms
iOS        32 – 55 ms
```

The iOS delay is the source of "the first tap feels slow". It is not your handler.

**In the wild**

- [embla-carousel #24](https://github.com/davidjerleke/embla-carousel/issues/24) — dragging the
  carousel and releasing fires a `click` on the child element. Reproduced on
  desktop: `click` fired after drags of 560–1195 px.
- [motion #363](https://github.com/motiondivision/motion/issues/363) — `mousedown` never fires on
  children of a draggable element. 🚧 Not verified: this harness observes `click`,
  not `mousedown`.

**How to verify**

Use `tools/c3-c6-tap-longpress-drag.html`, steps 1–6.

Minimum reproduction:

1. Attach both a click handler and pointer-based dragging to one element.
2. On a phone, tap without moving — click fires. Move ~15 px and release —
   on Android the click is gone, on iOS it usually survives.
3. On desktop, drag the element 300 px and release inside it — click fires.
4. Put a button inside the element and drag starting from the button. The button's
   click disappears on touch, and on desktop only when the cursor lands outside it.

**Verified on**

- Android 10 / Chrome 143 · 412×892 @3.5 · 2026-08-29
- iPadOS 26.6 / Safari 26.6 (iPad Pro) · 1024×1366 @2 · 2026-08-29
- iOS 18.7 / Safari (iPhone) · 375×667 @2 · 2026-08-29
- macOS 26.6.2 / Chrome 142 (mouse) · 2140×1391 @2 · 2026-08-29

Measured with `touch-action: none` throughout, to isolate this conflict from
[C10](#c10--drag--scroll).

**References**

- [Android — `ViewConfiguration.getScaledTouchSlop()`](https://developer.android.com/reference/android/view/ViewConfiguration)
- [W3C Pointer Events Level 3](https://www.w3.org/TR/pointerevents3/)
- [MDN — `Element: click` event](https://developer.mozilla.org/en-US/docs/Web/API/Element/click_event)
- 🚧 Needed: the UI Events clause specifying that `click` targets the nearest common
  ancestor of `mousedown` and `mouseup`. Behaviour observed but clause not yet cited.

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

- Holding an item opens the browser's own menu instead of starting the drag.
- Long-press works on Android but nothing happens on iPhone.
- Text gets selected and a blue callout appears when the user tries to hold and drag.
- After the iOS callout appears, the next tap does nothing — it only dismisses the menu.
- Long-press-to-drag freezes partway through on Android.

**Cause**

Every platform already assigns a meaning to holding a finger down, and each assigns
a different one.

Android Chrome fires `contextmenu` at a fixed delay. iOS and iPadOS Safari fire no
`contextmenu` at all — they begin a text selection and present a native callout.
Desktop browsers have no long-press concept whatsoever; holding the mouse button for
two seconds produces an ordinary `click` on release.

So there is no cross-platform event that means "the user held down". Any long-press
interaction has to be implemented with your own timer, and the platform's native
behaviour has to be suppressed separately on each platform — with a different
mechanism for each.

**Resolution**

Three separate pieces are required. None of them is sufficient alone.

```css
.holdable {
	touch-action: none;
	user-select: none;
	-webkit-user-select: none;
	-webkit-touch-callout: none; /* iOS: suppress the selection callout */
}
```

```js
el.addEventListener("contextmenu", (e) => e.preventDefault()) // Android
```

```js
let timer = null // all platforms
el.addEventListener("pointerdown", (e) => {
	timer = setTimeout(onLongPress, 500)
})
;["pointerup", "pointercancel"].forEach((t) =>
	el.addEventListener(t, () => {
		clearTimeout(timer)
		timer = null
	}),
)
el.addEventListener("pointermove", (e) => {
	if (movedBeyond(8)) {
		clearTimeout(timer)
		timer = null
	}
})
```

- `user-select: none` stops iOS selection and the Android selection path, but **does
  not stop Android's `contextmenu`** — that still fired 12/12 with selection
  disabled. The `preventDefault` above is not optional.
- `-webkit-touch-callout: none` is what removes the iOS callout. Without it the
  callout appears and swallows the following touch.
- The timer is the only portable detector. `contextmenu` never fires on iOS, so
  using it as the long-press signal produces a feature that silently does not exist
  on iPhone.
- Clear the timer on `pointermove` past threshold as well as on `pointerup` and
  `pointercancel`. A hold that turns into a drag is not a long press.

Use 500 ms. Android's own `contextmenu` fires within 495–513 ms across 30 trials, so
matching it keeps your handler aligned with the platform rather than racing it.

**Precedence**

|                                          | Android 10 / Chrome 143   | iPadOS 26.6     | iOS 18.7       | macOS Chrome (mouse) |
| ---------------------------------------- | ------------------------- | --------------- | -------------- | -------------------- |
| `contextmenu` on hold                    | **495–513 ms, 30/30**     | never           | never          | never                |
| text selection on hold                   | via `selectstart`         | `selChars` 5–12 | `selChars` 5–6 | on drag only         |
| `pointercancel` on hold                  | intermittent, ~530 ms     | none            | none           | none                 |
| hold then release                        | menu opens                | callout opens   | callout opens  | ordinary `click`     |
| `user-select: none` blocks selection     | yes                       | yes             | yes            | yes                  |
| `user-select: none` blocks `contextmenu` | **no, 12/12 still fired** | n/a             | n/a            | n/a                  |
| long-press → drag works                  | yes                       | yes             | yes            | yes                  |

Four findings worth stating separately:

1. **Android's `contextmenu` is remarkably precise.** 495–513 ms across every trial
   in three sessions, a spread of 18 ms. It is a reliable reference point, and also
   a reliable hazard.

2. **`contextmenu` fires mid-drag.** In the long-press-then-drag step it fired in
   11/13 Android trials, always at ~500 ms, while the finger was still moving. If it
   is not prevented, the native menu opens on top of an in-progress drag.

3. **Android can cancel the pointer stream during a hold.** With selection enabled,
   `pointercancel` appeared in 4/21 trials, all at ~530 ms — shortly after the
   selection engaged. With `user-select: none`, it never occurred. A long-press drag
   over selectable text can therefore lose its pointer stream on Android for reasons
   unrelated to scrolling.

4. **The iOS callout blocks the next touch.** Once the native selection callout is
   open, subsequent touches go to the overlay rather than the page — `pointerdown`
   never arrives. During measurement this was unmistakable: trials alternated
   between a genuine long press and a tap that only dismissed the menu. In a real
   app, the user's next tap is consumed by the menu and appears to do nothing.

On iOS the selection also grows while the finger is held: `selChars` went from 6 to
12 within a single 2.8 s hold. The longer the user holds, the more text is selected.

**In the wild**

- [dnd-kit #1398](https://github.com/clauderic/dnd-kit/issues/1398) — draggable elements
  activating only on long press, with a request for minimal activation delay.

🚧 Additional real-world reports for this pair not yet collected.

**How to verify**

Use `tools/c3-c6-tap-longpress-drag.html`, steps 7–9. Step 7 uses default text
settings, step 8 applies `user-select: none` and `-webkit-touch-callout: none`, and
step 9 holds and then drags.

On iOS, dismiss the callout between trials — while it is open the page receives no
pointer events, and a trial run without dismissing it produces alternating garbage.

Minimum reproduction:

1. Add a 500 ms timer-based long press to an element containing text.
2. Hold on Android — the native context menu opens over your handler.
3. Hold on iPhone — text is selected and a callout appears; no `contextmenu` fires.
4. Hold on desktop for two seconds and release — an ordinary `click` fires.
5. Apply `user-select: none` only. iOS is fixed; Android still opens the menu.

**Verified on**

- Android 10 / Chrome 143 · 412×892 @3.5 · 2026-08-29
- iPadOS 26.6 / Safari 26.6 (iPad Pro) · 1024×1366 @2 · 2026-08-29
- iOS 18.7 / Safari (iPhone) · 375×667 @2 · 2026-08-29
- macOS 26.6.2 / Chrome 142 (mouse) · 2140×1391 @2 · 2026-08-29

Measured with `touch-action: none` throughout, to isolate this conflict from
[C10](#c10--drag--scroll).

🚧 Not verified: whether the Android `contextmenu` delay is configurable or varies
by device, and whether `-webkit-touch-callout` has any effect on iPadOS in
desktop-class Safari specifically.

**References**

- [W3C Pointer Events Level 3 — suppressing a pointer event stream](https://www.w3.org/TR/pointerevents3/)
- [MDN — `Element: contextmenu` event](https://developer.mozilla.org/en-US/docs/Web/API/Element/contextmenu_event)
- [MDN — `user-select`](https://developer.mozilla.org/en-US/docs/Web/CSS/user-select)
- [MDN — `-webkit-touch-callout`](https://developer.mozilla.org/en-US/docs/Web/CSS/-webkit-touch-callout)
- [Android — `ViewConfiguration.getLongPressTimeout()`](https://developer.android.com/reference/android/view/ViewConfiguration)

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
