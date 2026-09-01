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

- Double-tap handling works on Android but never fires on iPhone or iPad.
- The first tap feels sluggish on iOS, as if the app hesitates.
- A single tap handler runs twice when the user double-taps.
- Adding `touch-action` to fix a scrolling problem silently breaks double-tap.

**Cause**

A tap cannot be resolved at the moment the finger lifts. The browser has to wait to
see whether a second tap follows, and only then decide whether to dispatch one
`click` or a `click` pair plus `dblclick`. That wait is the delay users feel.

`touch-action` participates in this decision. The Pointer Events spec defines
`manipulation` as permitting panning and continuous zooming while explicitly _not_
triggering behaviours that depend on multiple activations within a set period —
double-tap to zoom being the named example. In practice Safari extends that
suppression to the `dblclick` event itself, while Chrome on Android does not.

This is the same divergence documented in [C10](#c10--drag--scroll), where
`manipulation` cancels the pointer on Android but allows simultaneous drag and
scroll on iOS. One value, two interpretations.

**Resolution**

Do not use `dblclick` for touch interfaces.

```js
// Portable: resolve the pair yourself
let lastTap = 0
el.addEventListener("pointerup", (e) => {
	if (e.pointerType === "mouse") return // let dblclick handle mouse
	const now = performance.now()
	if (now - lastTap < 300) {
		onDoubleTap()
		lastTap = 0
	} else {
		lastTap = now
	}
})
```

Use 300 ms. That is Android's `DOUBLE_TAP_TIMEOUT`, and matching it keeps your
handler aligned with the platform on the one browser that also fires `dblclick`.

If you must rely on `dblclick`, do not set `touch-action: none` or `manipulation` on
that element, or it will never fire on iOS. Note that this conflicts directly with
the fix for C10, which requires `none` or `pan-y` on draggable elements — **an
element cannot be both reliably draggable and reliably double-tappable on iOS
through CSS alone.** Resolve the pair in JavaScript instead.

Prefer a different interaction. Double-tap is undiscoverable, has no keyboard
equivalent, and competes with the browser's own zoom. Where it exists it should
duplicate an action reachable another way.

**Precedence**

Three rapid tap pairs per device, per configuration. A "pair" is counted when the
second tap of a set was registered.

| `touch-action` | Android 10 / Chrome 143 | iPadOS 26.6 / Safari | iOS 18.7 / Safari |
| -------------- | ----------------------- | -------------------- | ----------------- |
| `auto`         | dblclick 3/5 pairs      | **7/7**              | **4/4**           |
| `manipulation` | dblclick **6/6 pairs**  | **0/7**              | **0/10**          |
| `none`         | dblclick 8/9 pairs      | 0/3                  | 0/4               |

Safari suppresses `dblclick` under both `manipulation` and `none`. Chrome on Android
fires it under all three values.

> An earlier session concluded that iOS never fires `dblclick`. That was wrong — the
> measurement had `touch-action: none` in force throughout. The value, not the
> platform, was responsible. Corrected here.

Desktop mouse input fires `dblclick` normally: 2/3 pairs on macOS Chrome.

**Tap delay, first tap vs second** (`click` timestamp minus `pointerup`):

```
                 first tap    second tap
iPadOS             ~36 ms        ~4 ms
iOS                ~36 ms        ~3 ms
Android           2 – 5 ms      2 – 5 ms
```

Safari holds the first `click` while it waits for a possible second tap; once the
pair resolves, the second fires immediately. This is the mechanism behind the
"first tap feels slow" complaint noted in [C3](#c3--tap--drag). Android does not
wait.

**In the wild**

🚧 No real-world issue reports collected for this pair yet.

**How to verify**

Use `tools/c3-c6-tap-longpress-drag.html`, steps 10–12. Step 10 runs under
`touch-action: none`, step 11 under `manipulation`, step 12 under `auto`.

Tap the card's text, not the child button — the button was the target in the first
session and the results, while still valid for `dblclick`, do not exercise the card.

Minimum reproduction:

1. Attach a `dblclick` handler to an element with `touch-action: auto`.
2. Double-tap on iPhone — it fires.
3. Change to `touch-action: manipulation` and repeat — it no longer fires on iOS,
   but still fires on Android.

**Verified on**

- Android 10 / Chrome 143 · 412×892 @3.5 · 2026-08-29
- iPadOS 26.6 / Safari 26.6 (iPad Pro) · 1024×1366 @2 · 2026-08-29
- iOS 18.7 / Safari (iPhone) · 375×667 @2 · 2026-08-29
- macOS 26.6.2 / Chrome 142 (mouse) · 2140×1391 @2 · 2026-08-29

🚧 **Double-tap zoom was not measured.** The harness page is `width=device-width`
with no horizontally overflowing content, so Android Chrome found no block to zoom
to and zoom never occurred anywhere on the page — inside or outside the test area.
On iOS, zoom occurred outside the card but not on it, which is not attributable to
`touch-action` since it also failed under `auto`. Isolating zoom behaviour needs a
page built for that purpose, with controlled viewport and zoomable content.

**References**

- [W3C Pointer Events Level 3 — the `touch-action` CSS property](https://www.w3.org/TR/pointerevents3/)
- [MDN — `Element: dblclick` event](https://developer.mozilla.org/en-US/docs/Web/API/Element/dblclick_event)
- [Android — `ViewConfiguration.getDoubleTapTimeout()`](https://developer.android.com/reference/android/view/ViewConfiguration)

---

### C2 — Tap ↔ LongPress

**Symptom**

- Long-pressing an item also triggers its tap action when the finger lifts.
- A long-press menu opens on Android; on iPhone the same hold does nothing.
- Holding the mouse button on desktop just fires an ordinary click after two seconds.
- The user holds to open a context menu, and the item navigates instead.

**Cause**

A long press is a tap that has not ended yet. Nothing distinguishes the two until a
timer expires, and the platform has already decided what that timer means before
your code sees the gesture — differently on each platform.

Android Chrome fires `contextmenu` at a fixed delay. Safari on iOS and iPadOS fires
no `contextmenu` at all; it begins a text selection and shows a native callout.
Desktop browsers have no long-press concept: a two-second hold produces a plain
`click` on release.

The tap side of the conflict is the part usually forgotten. Once your long press
activates, the pointer is still down, and when it lifts the browser will dispatch
`click` exactly as it would for a tap. Unless you suppress it, the long-press
action and the tap action both run.

**Resolution**

Arm a timer, and disarm the tap once it fires.

```js
let timer = null,
	longFired = false

el.addEventListener("pointerdown", () => {
	longFired = false
	timer = setTimeout(() => {
		longFired = true
		onLongPress()
	}, 500)
})
;["pointerup", "pointercancel"].forEach((t) =>
	el.addEventListener(t, () => {
		clearTimeout(timer)
		timer = null
	}),
)

el.addEventListener("pointermove", () => {
	if (movedBeyond(8)) {
		clearTimeout(timer)
		timer = null
	} // now a drag
})

el.addEventListener("click", (e) => {
	if (longFired) {
		e.preventDefault()
		e.stopPropagation()
		return
	}
	onTap()
})
```

The `click` guard is not optional. On desktop a two-second hold fired `click` in
10/10 trials — the long press and the tap both run without it.

Use 500 ms and an 8 px movement threshold. Both match the platform: Android's own
`contextmenu` fires within 494–513 ms, and its click-cancellation slop is exactly
8 px (see [C3](#c3--tap--drag)).

Suppress the native behaviours separately — the mechanism differs by platform and is
covered in [C6](#c6--longpress--drag). In short: `user-select: none` and
`-webkit-touch-callout: none` for iOS, plus `preventDefault()` on `contextmenu` for
Android, which `user-select` does not stop.

**Precedence**

|                            | Android 10 / Chrome 143 | iPadOS 26.6           | iOS 18.7              | macOS Chrome (mouse) |
| -------------------------- | ----------------------- | --------------------- | --------------------- | -------------------- |
| native long-press signal   | `contextmenu`           | text selection        | text selection        | **none**             |
| timing                     | 494–513 ms, n=73        | no fixed event        | no fixed event        | —                    |
| `click` after a 1–2 s hold | suppressed by menu      | suppressed by callout | suppressed by callout | **fires, 10/10**     |
| tap `click` delay          | 1–6 ms                  | 35–41 ms              | 32–55 ms              | 0–2 ms               |

Two consequences worth stating plainly:

1. **There is no cross-platform long-press event.** `contextmenu` fires only on
   Android. Building on it produces a feature that silently does not exist on iOS
   and on desktop.

2. **Desktop is the case that leaks.** On touch the native menu or callout takes
   over and the tap is suppressed for you. On desktop nothing intervenes: holding
   for two seconds produced a normal `click` at 1552–2242 ms in every trial. Code
   tested only on a phone will fire both actions the first time it runs on a laptop.

The tap-side delay differs enough to matter for perceived responsiveness. Android
dispatches `click` 1–6 ms after `pointerup`; Safari waits 32–55 ms while it rules
out a second tap (see [C1](#c1--tap--doubletap)).

**In the wild**

- [dnd-kit #1398](https://github.com/clauderic/dnd-kit/issues/1398) — draggables activating
  only on long press, with a request for minimal activation delay.

🚧 Additional reports for this pair not yet collected.

**How to verify**

Use `tools/c3-c6-tap-longpress-drag.html`, steps 1, 7 and 8. Step 1 establishes the
tap baseline; steps 7 and 8 hold with and without selection suppression.

On iOS, dismiss the native callout between trials. While it is open the page
receives no pointer events at all — see C6.

Minimum reproduction:

1. Attach a 500 ms timer-based long press and a click handler to the same element.
2. Hold on desktop for two seconds and release. Both handlers run.
3. Hold on Android. The native menu opens over your handler.
4. Hold on iPhone. Nothing fires; text is selected instead.

**Verified on**

- Android 10 / Chrome 143 · 412×892 @3.5 · 2026-08-29
- iPadOS 26.6 / Safari 26.6 (iPad Pro) · 1024×1366 @2 · 2026-08-29
- iOS 18.7 / Safari (iPhone) · 375×667 @2 · 2026-08-29
- macOS 26.6.2 / Chrome 142 (mouse) · 2140×1391 @2 · 2026-08-29

Measured with `touch-action: none` throughout, to isolate this conflict from
[C10](#c10--drag--scroll).

**References**

- [Android — `ViewConfiguration.getLongPressTimeout()`](https://developer.android.com/reference/android/view/ViewConfiguration)
- [MDN — `Element: contextmenu` event](https://developer.mozilla.org/en-US/docs/Web/API/Element/contextmenu_event)
- [MDN — `user-select`](https://developer.mozilla.org/en-US/docs/Web/CSS/user-select)
- [W3C Pointer Events Level 3](https://www.w3.org/TR/pointerevents3/)

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

Distance at which the synthetic `click` stops firing. Session counts vary by
device — see `research/measurements/README.md`.

|                            | click fires up to | click suppressed from | boundary              |
| -------------------------- | ----------------- | --------------------- | --------------------- |
| Android 10 / Chrome 143    | 7.9 px            | 8.2 px                | **exact, no overlap** |
| iPadOS 26.6 / Safari       | 42.0 px           | 20.6 px               | overlapping 20–42 px  |
| iOS 18.7 / Safari          | 44.8 px           | 43.7 px               | overlapping 43–45 px  |
| macOS / Chrome 142 (mouse) | 1195 px           | —                     | **never suppressed**  |

Android's boundary falls exactly between 7.9 px and 8.2 px with no exceptions across
roughly 40 trials, matching `ViewConfiguration.TOUCH_SLOP` = 8dp. Treat that constant
as the real browser behaviour, not just an Android UI value.

iOS has no single distance threshold. A 20.6 px gesture was suppressed while a
42.0 px one was not, in the same session. Suppressed trials frequently coincided
with text selection engaging (`selChars > 0`), which suggests selection arbitration
participates in the decision. **Do not derive an iOS slop constant from these
numbers.**

After a long drag, touch platforms suppress `click` completely:

|                                   | drags | click fired |
| --------------------------------- | ----- | ----------- |
| touch, on the card                | 37    | **0**       |
| touch, starting on a child button | 36    | **0**       |
| mouse, on the card                | 14    | **7**       |
| mouse, starting on a child button | 20    | 2           |

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
  not stop Android's `contextmenu`** — that still fired 17/17 with selection
  disabled. The `preventDefault` above is not optional.
- `-webkit-touch-callout: none` is what removes the iOS callout. Without it the
  callout appears and swallows the following touch.
- The timer is the only portable detector. `contextmenu` never fires on iOS, so
  using it as the long-press signal produces a feature that silently does not exist
  on iPhone.
- Clear the timer on `pointermove` past threshold as well as on `pointerup` and
  `pointercancel`. A hold that turns into a drag is not a long press.

Use 500 ms. Android's own `contextmenu` fires within 494–513 ms across 73 trials, so
matching it keeps your handler aligned with the platform rather than racing it.

**Precedence**

|                                          | Android 10 / Chrome 143   | iPadOS 26.6     | iOS 18.7       | macOS Chrome (mouse) |
| ---------------------------------------- | ------------------------- | --------------- | -------------- | -------------------- |
| `contextmenu` on hold                    | **494–513 ms, n=73**      | never           | never          | never                |
| text selection on hold                   | via `selectstart`         | `selChars` 5–12 | `selChars` 5–6 | on drag only         |
| `pointercancel` on hold                  | intermittent, ~530 ms     | none            | none           | none                 |
| hold then release                        | menu opens                | callout opens   | callout opens  | ordinary `click`     |
| `user-select: none` blocks selection     | yes                       | yes             | yes            | yes                  |
| `user-select: none` blocks `contextmenu` | **no, 17/17 still fired** | n/a             | n/a            | n/a                  |
| long-press → drag works                  | yes                       | yes             | yes            | yes                  |

Four findings worth stating separately:

1. **Android's `contextmenu` is remarkably precise.** 495–513 ms across every trial
   in three sessions, a spread of 18 ms. It is a reliable reference point, and also
   a reliable hazard.

2. **`contextmenu` fires mid-drag.** In the long-press-then-drag step it fired in
   20/21 Android trials, always at ~500 ms, while the finger was still moving. If it
   is not prevented, the native menu opens on top of an in-progress drag.

3. **Android can cancel the pointer stream during a hold.** With selection enabled,
   `pointercancel` appeared in 6/37 trials, all at ~530 ms — shortly after the
   selection engaged. With `user-select: none`, it never occurred (0/17). A
   long-press drag over selectable text can therefore lose its pointer stream on
   Android for reasons unrelated to scrolling.

4. **The iOS callout blocks the next touch.** Once the native selection callout is
   open, subsequent touches go to the overlay rather than the page — `pointerdown`
   never arrives. During measurement this was unmistakable: trials alternated
   between a genuine long press and a tap that only dismissed the menu. In a real
   app, the user's next tap is consumed by the menu and appears to do nothing.

Final selection length on iOS varied between separate holds — 6 characters in one
step-7 trial, 12 in another, both held roughly 2.8–4.2 s. This shows the selected
length is not fixed across holds; it is not evidence of growth within a single
hold, which was not measured here.

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

- Holding an item right after scrolling does nothing — the list has to fully stop first.
- A long-press menu that works fine on a settled screen never appears if the user
  touches while the list is still gliding.
- The hold sometimes triggers a drag of the settling scroll instead of the menu.

**Cause**

A long press assumes the pointer survives untouched for ~500 ms. Scrolling assumes
the opposite — that a touch during momentum means "stop the scroll." The two claims
collide whenever a user touches down before the list has fully settled, and in that
collision scrolling wins almost every time.

The platform's native long-press signal itself does not change with `touch-action`.
Android still fires `contextmenu` at the same delay documented in
[C6](#c6--longpress--drag); iOS still fires none, showing a silent text selection
instead. What C8 adds is what happens to that signal when the container has
residual velocity.

**Resolution**

Do not rely on a long-press firing reliably immediately after a fling. Either debounce
against recent scroll activity, or accept that the first touch after a fling
sometimes only stops the scroll and require a second, separate hold.

```js
let lastScrollAt = 0
scroller.addEventListener("scroll", () => {
	lastScrollAt = performance.now()
})

el.addEventListener("pointerdown", () => {
	if (performance.now() - lastScrollAt < 150) return // list still settling
	armLongPressTimer()
})
```

150 ms is a starting point, not a measured constant — tune it against your own
scroll deceleration curve. The point is structural: don't assume a hold started
during momentum will complete.

The rest of the mitigation is the same as C6 — suppress selection and the Android
context menu, and clear the timer on `pointercancel`.

**Precedence**

_Touching down while the list is still moving from a fling, held for 1.5 s:_

|                                           | Android 10 / Chrome 143 | iPadOS 26.6 | iOS 18.7   |
| ----------------------------------------- | ----------------------- | ----------- | ---------- |
| cancelled within ~100 ms                  | 10/18 (56%)             | 8/9 (89%)   | 9/10 (90%) |
| long-press signal despite motion          | 4/18 (22%)              | 0/9         | 0/10       |
| ambiguous — held, small scroll, no signal | 4/18 (22%)              | 1/9         | 1/10       |

**Touching during momentum scroll gets the pointer stream cancelled almost
immediately in the large majority of attempts, on every platform.** iOS is worse
than Android here — 89–90% instant cancellation versus 56%. A long press armed the
moment the list starts settling will fail far more often than it succeeds.

The four Android "ambiguous" trials are worth flagging even at this sample size:
the pointer survived 1.4–2.9 s with a few pixels of container scroll registered,
but `contextmenu` never fired — unlike the clean 494–513 ms timing seen when the
list is fully stationary (C6). This suggests residual momentum can suppress
Android's context-menu timer even without cancelling the pointer outright. 🚧 n=4,
not confirmed as a general rule.

_Touching down on a fully stationary list_ (`touch-action: none`) reproduces C6
exactly: Android fired `contextmenu` 6/6 at the usual ~500 ms; iPadOS and iOS fired
it 0/11, with a silent text selection instead. `touch-action` does not change this
— see C6 for the full breakdown.

**In the wild**

🚧 No real-world issue reports collected for this specific pair (long-press timing
against momentum scroll) yet. See C6 for general long-press platform-divergence
reports.

**How to verify**

Use `tools/c8-c9-c11-c13-scroll-swipe-pinch.html`, steps 1–3. Step 2 requires
flinging the list hard first, then touching down while it is still decelerating —
timing is imprecise by hand; expect to discard a few mistimed attempts.

Minimum reproduction:

1. Attach a 500 ms long-press timer to items in a scrolling list.
2. Fling the list, then immediately hold an item while it is still moving.
3. On any platform, the hold is cancelled almost immediately in most attempts.
4. Wait for the list to fully stop, then hold again — the long press now behaves
   as in C6.

**Verified on**

- Android 10 / Chrome 143 · 412×892 @3.5 · 2026-08-29
- iPadOS 26.6 / Safari 26.6 (iPad Pro) · 1024×1366 @2 · 2026-08-29
- iOS 18.7 / Safari (iPhone) · 375×667 @2 · 2026-08-29

Not applicable to desktop mouse input — there is no momentum scroll to collide with.

**References**

- [W3C Pointer Events Level 3 — suppressing a pointer event stream](https://www.w3.org/TR/pointerevents3/)
- See [C6](#c6--longpress--drag) for the underlying long-press platform divergence.
- See [C10](#c10--drag--scroll) for `pointercancel` mechanics generally.

---

### C9 — Drag ↔ Swipe

**Symptom**

- A horizontal swipe-to-delete sometimes scrolls the list instead of sliding the row.
- The same swipe gesture works reliably on Android but is inconsistent on iPhone.
- A swipe that starts slightly diagonal gets swallowed by the scroll every time on iOS.

**Cause**

Once `touch-action: pan-y` has resolved the axis contention documented in
[C12](#c12--swipe--scroll), a second question remains: does the browser actually
honor a clean horizontal gesture as belonging to JavaScript for the gesture's full
duration, or can it still reclaim the pointer partway through? The two platforms
answer differently.

**Resolution**

Same as C12 — `touch-action: pan-y`, gate on horizontal intent, handle
`pointercancel` by resetting position. What C9 adds: on iOS, budget for the
gesture failing partway even when it started as a clean horizontal swipe. Do not
treat `pan-y` as a guarantee there.

```js
el.addEventListener("pointercancel", () => {
	// On iOS this fires meaningfully more often than on Android
	// even for gestures that started unambiguously horizontal.
	resetToRestingPosition()
})
```

If the swipe drives a destructive action (delete, archive), do not commit it until
`pointerup` is received without an intervening `pointercancel`. A swipe that the
browser reclaims mid-gesture must be recoverable, not partially applied.

**Precedence**

`touch-action: pan-y` throughout, cancellation rate by gesture shape:

| gesture               | Android 10 / Chrome 143 | iPadOS 26.6   | iOS 18.7      |
| --------------------- | ----------------------- | ------------- | ------------- |
| fast horizontal flick | 0/8 cancelled           | 3/7 cancelled | 2/6 cancelled |
| slow horizontal drag  | 0/5 cancelled           | 3/7 cancelled | 2/6 cancelled |
| slow diagonal         | 0/5 cancelled           | 5/5 cancelled | 5/5 cancelled |

Android never lost a single horizontal or diagonal gesture to the scroll across 18
trials — once JavaScript takes the axis, it keeps it, regardless of speed or
straightness. **iOS reclaims 30–40% of gestures the user intended as clean
horizontal swipes**, and 100% of diagonal ones. This is not a matter of the user
swiping imprecisely — every cancelled trial here started with clear horizontal
displacement; iOS revoked the gesture partway through in spite of that.

Once a gesture activates as a drag, the axis classification itself did not flip
mid-gesture in any C9 trial on any platform — the instability is in whether the
browser cancels the stream outright, not in whether JavaScript's own axis
judgment changes (contrast [C11](#c11--drag--pinch), where axis flips did occur
under a different trigger).

This matches the diagonal-drag finding in [C10](#c10--drag--scroll): Android lets
slow, ambiguous motion stay with JavaScript far more readily than iOS does.

**In the wild**

- [motion #185](https://github.com/motiondivision/motion/issues/185) — small unwanted
  horizontal drags while scrolling past elements; the C12 case.
- [vaul #358](https://github.com/emilkowalski/vaul/issues/358) — diagonal movement
  starting a drag that does not settle back; directly matches the 100% iOS
  cancellation on diagonal motion measured here.

**How to verify**

Use `tools/c8-c9-c11-c13-scroll-swipe-pinch.html`, steps 4–6.

Minimum reproduction:

1. Attach a horizontal swipe action to a row inside a `pan-y` vertical list.
2. On Android, swipe fast, slow, and diagonally — all succeed.
3. On iPhone or iPad, repeat the same three motions several times each. A
   noticeable fraction of the horizontal ones, and nearly all diagonal ones, are
   cancelled mid-gesture.

**Verified on**

- Android 10 / Chrome 143 · 412×892 @3.5 · 2026-08-29
- iPadOS 26.6 / Safari 26.6 (iPad Pro) · 1024×1366 @2 · 2026-08-29
- iOS 18.7 / Safari (iPhone) · 375×667 @2 · 2026-08-29
- macOS Chrome 142 (mouse) · 2140×1391 @2 · 2026-08-29 — mouse drags never
  cancelled (0/15 across all three gesture shapes), as expected: there is no
  competing scroll gesture to arbitrate against with a single mouse pointer.

**References**

- [W3C Pointer Events Level 3 — suppressing a pointer event stream](https://www.w3.org/TR/pointerevents3/)
- See [C10](#c10--drag--scroll) and [C12](#c12--swipe--scroll) for the underlying
  mechanics this conflict builds on.

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
`pointercancel`, scoped to a straight vertical drag under `auto` and under `pan-y`
(steps 1 and 5 only; excludes the gap-zone, `pan-x`, and `manipulation` steps,
whose cancellations are not activation-threshold measurements — see
`research/measurements/DERIVED.md`):

```
Android    8.1 – 10.3 px    n=11   (consistent with ViewConfiguration TOUCH_SLOP = 8dp)
iPadOS    10.5 – 13.5 px    n=10
iOS        5.5 – 14.5 px    n=10
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

- Dragging an object on a canvas, then a second finger accidentally lands nearby,
  and the drag jumps or resizes unexpectedly.
- Adding a second finger mid-drag sometimes cancels the interaction entirely on iOS.
- A drag-then-pinch gesture (common when repositioning and scaling in one motion)
  behaves differently depending on `touch-action`.

**Cause**

A single-pointer drag and a two-pointer pinch are, at the DOM level, the same
pointer stream gaining a participant. Nothing distinguishes "the user wants to
pinch now" from "a second finger brushed the screen" except how many pointers are
currently down — and what the browser does with that second pointer depends on
`touch-action`, inherited from the pinch-vs-scroll arbitration covered in
[C13](#c13--scroll--pinch).

**Resolution**

Track pointer count explicitly and decide intent from it, rather than assuming a
drag stays a drag:

```js
const active = new Map()

el.addEventListener("pointerdown", (e) => {
	active.set(e.pointerId, { x: e.clientX, y: e.clientY })
	if (active.size === 2) startPinch([...active.values()])
})
```

Do not assume `touch-action: none` alone is sufficient to keep a drag-to-pinch
transition alive on iOS — see Precedence. Test the transition explicitly rather
than inferring it from single-pointer drag behavior.

If the element must support pinch-to-scale, `none` measured more reliably than
`pan-y` for keeping the second pointer's stream alive long enough to read a scale
value.

**Precedence**

Starting a one-finger drag, then adding a second finger without releasing the first:

|                                                   | Android 10 / Chrome 143 | iPadOS 26.6 | iOS 18.7 |
| ------------------------------------------------- | ----------------------- | ----------- | -------- |
| `none` — pinch scale captured                     | 5/6                     | 4/6         | 3/6      |
| `none` — stayed single-pointer drag               | 1/6                     | 2/6         | 3/6      |
| `pan-y` — cancelled near-instantly on 2nd pointer | 0/6                     | 4/12        | 8/12     |
| `pan-y` — pinch scale captured despite `pan-y`    | 4/6                     | 3/12        | 0/12     |

Two things worth separating from the noise:

1. **Under `pan-y`, adding a second finger triggers a near-instant
   `pointercancel` far more often on iOS than on Android.** iOS cancelled 8 of 12
   attempts within single-digit milliseconds of the second pointer arriving.
   Android cancelled none. This is consistent with the drag-vs-scroll asymmetry
   throughout this document — iOS treats `pan-y` as a narrower grant than Android
   does.

2. **Android allowed pinch scale to register under `pan-y` in 4 of 6 trials** —
   spec-inconsistent, matching the same divergence found in
   [C13](#c13--scroll--pinch) for page zoom. `pan-y` is not a reliable way to
   block or permit pinch on Android; it is inconsistent even within this small
   sample.

🚧 Sample sizes here are small and manual two-finger placement is imprecise by
hand — treat the direction of each platform difference as more reliable than the
exact ratios.

Axis reclassification (a drag that changes from horizontal to vertical mid-gesture,
independent of pinch) was observed on all three touch platforms, most often
coincident with the second pointer landing — suggesting the arrival of a second
touch perturbs the first pointer's apparent trajectory enough to flip the
single-axis judgment described in [C9](#c9--drag--swipe).

**In the wild**

🚧 No real-world issue reports collected for this specific pair yet.

**How to verify**

Use `tools/c8-c9-c11-c13-scroll-swipe-pinch.html`, steps 7–8. Requires two fingers
on a real device; cannot be approximated with a mouse (see Verified on).

Minimum reproduction:

1. Start a one-finger drag on an element with `touch-action: none`.
2. Without lifting, add a second finger and pinch. Observe whether pinch scale is
   readable via the pointer stream.
3. Repeat with `touch-action: pan-y` on iOS specifically — expect frequent
   immediate cancellation the moment the second finger lands.

**Verified on**

- Android 10 / Chrome 143 · 412×892 @3.5 · 2026-08-29
- iPadOS 26.6 / Safari 26.6 (iPad Pro) · 1024×1366 @2 · 2026-08-29
- iOS 18.7 / Safari (iPhone) · 375×667 @2 · 2026-08-29

Not measurable on desktop with a mouse — a mouse can only ever produce one
pointer, so this conflict does not exist there. macOS trackpad two-finger
gestures were attempted but produced no Pointer Events at all in this harness
(see [C13](#c13--scroll--pinch)); trackpad pinch routes through `wheel` events,
out of scope here.

**References**

- [W3C Pointer Events Level 3 — Pointer Capture](https://www.w3.org/TR/pointerevents3/)
- See [C9](#c9--drag--swipe), [C10](#c10--drag--scroll), and
  [C13](#c13--scroll--pinch) for the mechanics this conflict combines.

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

- Pinching an item inside a scrollable list zooms the whole page on one platform
  but not another, with the exact same code.
- `touch-action: pan-y`, chosen to fix drag-vs-scroll ([C10](#c10--drag--scroll)),
  appears to also block pinch-zoom during testing — until the app ships to a
  different platform, where it does not.
- Native double-tap-to-zoom or pinch-to-zoom fires unexpectedly inside an app that
  never intended to support page zoom at all.

**Cause**

`pan-y` and `pinch-zoom` are declared independently in the touch-action spec —
permitting one does not, on paper, imply anything about the other.
`manipulation` is defined as permitting panning _and_ continuous zooming together;
`pan-y` alone says nothing about zoom. In principle, `pan-y` should leave pinch
handling exactly as unconstrained (or as blocked) as it would be without any
`touch-action` at all, since zoom is a separate axis of the same property.

**Measured behavior does not match that reading, and it does not match consistently
across platforms.** iOS treats `pan-y` as if it blocks zoom completely — identical
to `none`. Android does not; under `pan-y`, page zoom fired in nearly every trial,
behaving like `auto`.

**Resolution**

Do not rely on `pan-y` to suppress pinch-zoom. Its effect on zoom is
platform-dependent and, on Android, indistinguishable from having no restriction
at all.

```css
/* If pinch-zoom must be blocked, say so explicitly */
.no-native-zoom {
	touch-action: pan-y pinch-zoom;
} /* still permits pinch-zoom — see below */
```

There is no combination of `pan-x`/`pan-y` that reliably blocks zoom on Android
while still permitting one-axis panning, in this measurement. The only value that
blocked zoom on **every** platform tested was `none` — which also blocks all
panning, the trade-off already documented in [C10](#c10--drag--scroll).

If an element needs vertical scroll _and_ no pinch-zoom, that combination could not
be produced reliably by `touch-action` alone in this test. Suppressing zoom while
preserving scroll likely requires additional JavaScript-side handling (tracking
pointer count and calling `preventDefault()` on multi-pointer gestures) rather than
a CSS-only solution. 🚧 not verified — this measurement establishes the gap, not a
confirmed fix.

**Precedence**

Page zoom (`visualViewport.scale` change of >2%) observed during a two-finger
pinch-out gesture on an item:

| `touch-action` | Android 10 / Chrome 143     | iPadOS 26.6           | iOS 18.7                  |
| -------------- | --------------------------- | --------------------- | ------------------------- |
| `pan-y`        | **zoomed 6/6** valid trials | zoomed 0/5            | zoomed 0/8                |
| `none`         | zoomed 0/5                  | zoomed 0/6            | zoomed 0/5                |
| `auto`         | zoomed 4/5                  | zoomed 6/6 (see note) | zoomed in ≥2/8 (see note) |

**This is the central finding of the session.** Under `pan-y`:

- **Android zoomed on 6 of 6 valid attempts** — behaving exactly like `auto`.
- **iPadOS and iOS zoomed on 0 of 13 combined attempts** — behaving exactly like
  `none`.

A developer who tests only on iPhone will conclude `pan-y` is sufficient to block
unwanted pinch-zoom while preserving scroll. The same code, unchanged, will zoom on
Android on essentially every attempt. The reverse is equally true: a developer who
wants zoom available together with vertical panning, and tests only on Android,
will find `pan-y` provides it — and lose zoom entirely when the same build reaches
an iPhone.

Under `none`, all three platforms agree — zoom is fully blocked, 0/16 combined.
This is the one value with consistent cross-platform behavior for this conflict.

🚧 Measurement caveat on the `auto` row: zoom was not reset to 1.0 between trials
in the iPadOS and iOS sessions, so consecutive readings sometimes reflect a
pinch-in correcting a prior pinch-out rather than an independent zoom failure. The
`pan-y` and `none` rows above are not affected by this — they showed no zoom
activity to accumulate. Treat the exact `auto` ratios as indicative, not exact; the
qualitative finding (`auto` permits zoom on all three platforms) still holds, as at
least one clean zoom event was captured on each platform under `auto`.

**In the wild**

🚧 No real-world issue reports collected for this specific pair yet. The
`pan-y`-does-not-block-zoom-on-Android behavior does not appear to be documented
in MDN's `touch-action` page or the W3C spec examples at the time of writing.

**How to verify**

Use `tools/c8-c9-c11-c13-scroll-swipe-pinch.html`, steps 9–11. The harness reads
`visualViewport.scale` directly — no need to judge zoom by eye. Reset zoom to 1.0
between trials (two-finger pinch-in, or reload) before starting the next one; the
iPadOS/iOS `auto` measurements above were compromised by skipping this step.

Minimum reproduction:

1. Set `touch-action: pan-y` on a scrollable list item.
2. Pinch-out on the item on an Android phone — the page zooms.
3. Repeat the identical gesture on an iPhone or iPad — the page does not zoom.

**Verified on**

- Android 10 / Chrome 143 · 412×892 @3.5 · 2026-08-29
- iPadOS 26.6 / Safari 26.6 (iPad Pro) · 1024×1366 @2 · 2026-08-29
- iOS 18.7 / Safari (iPhone) · 375×667 @2 · 2026-08-29

**Trackpad pinch on macOS Chrome produced no Pointer Events at all** — 0 of 17
attempts across all three `touch-action` values registered as `pointerdown`/multi-
pointer activity in this harness. Two-finger trackpad gestures on this build were
occasionally read by the browser as a secondary click instead (`contextmenu` fired
at 1–2 ms in several trials), not as a pinch. Trackpad pinch-zoom routes through
`wheel` events with `ctrlKey: true`, which this harness does not instrument. **This
means touch-based `touch-action` mitigation has no bearing on trackpad zoom** — a
desktop trackpad user can zoom a page regardless of any `touch-action` value set on
its elements, because the browser never treats it as a touch gesture in the first
place. 🚧 confirmed as a gap in this harness's coverage, not independently verified
against the `wheel`/`ctrlKey` path.

**References**

- [W3C Pointer Events Level 3 — the `touch-action` CSS property](https://www.w3.org/TR/pointerevents3/)
- [MDN — `touch-action`](https://developer.mozilla.org/en-US/docs/Web/CSS/touch-action)
- [MDN — `VisualViewport.scale`](https://developer.mozilla.org/en-US/docs/Web/API/VisualViewport/scale)
- 🚧 Needed: a primary source (WebKit or Chromium bug tracker / release notes)
  explaining why Chrome's `pan-y` implementation permits pinch-zoom while
  WebKit's does not. Behaviour measured; engine-level explanation not yet found.
