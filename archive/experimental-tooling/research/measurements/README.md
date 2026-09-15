# research/measurements

Raw output from the verification harnesses in `tools/`, and the pooled figures
derived from it.

Every number that appears in `CONFLICTS.md` traces to a file here. If a claim in the
matrix cannot be traced to a log in this directory, it should not be in the matrix.

---

## Files

```
README.md                     this file
DERIVED.md                     pooled figures used in CONFLICTS.md, with trial counts

c10-android.txt                C10 harness, Android — 1 session
c10-ipad.txt                   C10 harness, iPadOS — 1 session
c10-iphone.txt                 C10 harness, iOS — 1 session

c3-c6-android.txt              C3/C6 harness, Android — 3 sessions concatenated
                                (05:50, 05:41, 05:09), steps 1-10
c3-c6-ipad.txt                 C3/C6 harness, iPadOS — 1 session, steps 1-10
c3-c6-iphone.txt               C3/C6 harness, iOS — 1 session, steps 1-10
c3-c6-macos.txt                C3/C6 harness, macOS Chrome 142, mouse — 2 sessions
                                concatenated (05:53, 05:56); the second re-runs
                                steps 4 and 6 only, with horizontal-only drags

c3-c6-android-s11-12.txt       C3/C6 harness, Android — steps 11-12 only
                                (touch-action × dblclick, card target)
c3-c6-ipad-s11-12.txt          C3/C6 harness, iPadOS — steps 11-12 only
c3-c6-iphone-s11-12.txt        C3/C6 harness, iOS — steps 11-12 only

c8-c9-c11-c13-android.txt      C8/C9/C11/C13 harness, Android — 1 session, all 11 steps
c8-c9-c11-c13-ipad.txt         C8/C9/C11/C13 harness, iPadOS — 1 session, all 11 steps
c8-c9-c11-c13-iphone.txt       C8/C9/C11/C13 harness, iOS — 1 session, all 11 steps
c8-c9-c11-c13-macos.txt        C8/C9/C11/C13 harness, macOS, trackpad — 1 session,
                                steps 1, 3-11 (step 2 needs momentum scroll,
                                not applicable to mouse/trackpad)
```

**Note on session counts**: only Android (C3/C6) and macOS (C3/C6) needed more than
one recording session — Android because the settle-timer bug (see issue 1) required
re-running, macOS because early large drags left the clipped stage area (issue 6).
iPad and iPhone needed one session each for every harness. An earlier version of
this file incorrectly listed two iPad C3/C6 sessions (`ipad-1.txt`, `ipad-2.txt`);
there was only ever one.

## Devices

| label   | OS / browser                         | viewport     | touch points                        |
| ------- | ------------------------------------ | ------------ | ----------------------------------- |
| android | Android 10 / Chrome 143              | 412×892 @3.5 | 5                                   |
| ipad    | iPadOS 26.6 / Safari 26.6 (iPad Pro) | 1024×1366 @2 | 5                                   |
| iphone  | iOS 18.7 / Safari                    | 375×667 @2   | 5                                   |
| macos   | macOS 26.6.2 / Chrome 142            | 2140×1391 @2 | 0 (mouse), trackpad for pinch steps |

All measurements taken 2026-08-29.

iPadOS reports a Macintosh user agent. It is identified here by `maxTouchPoints > 1`
and confirmed by hand. Do not trust the `ua-detect` line on that device.

---

## Known instrumentation issues

These affect how the logs should be read. `DERIVED.md` figures account for all of
them; where an earlier pooled figure did not, it has been corrected there and noted
with a ⟳.

**1. `dur` was negative in two of the three Android C3/C6 sessions.**
The gesture length subtracted the 700 ms settle window even when the gesture was
force-closed early by the next `pointerdown`. Fixed mid-project by recording
`endAt` at `pointerup` — visible as the difference between the earliest-dated block
in `c3-c6-android.txt` (positive `dur`) and the two later-recorded blocks
(negative `dur` in places). `dist`, `clickAt`, `ctxAt`, and the fired-event set are
unaffected by this bug in every session — all figures in `DERIVED.md` use those
fields, not `dur`, except the click-delay figures, which use `clickAt` minus `dur`
computed only from the sessions where `dur` is positive.

**2. iOS callout swallows alternate trials.**
Affects `c3-c6-iphone.txt` and `c3-c6-ipad.txt`, step 7. Once the native selection
callout opens, subsequent touches go to the overlay and never reach the page.
Trials alternate between a genuine long press (`dur` ≈ 900 ms+, `selChars` > 0) and
a tap that only dismissed the menu (`childClick`, `dur` < 100 ms). Discard the
dismissal trials when reading step 7. This is itself a finding — see C6,
Precedence, item 4.

**3. Scroll position was not controlled in C10 step 1.**
Every trial began with the list at the top, so the container could not scroll
upward. Only the cancellation result from that step is comparable across platforms;
`scrollAfter` is not.

**4. Gap zone was not instrumented in the C10 iPhone session.**
Step 4 trial 1 registered as a drag because the harness had not yet excluded the
gap zone from drag activation. 2 of 3 trials in that step remain valid.

**5. C3/C6 step 10 targeted the child button, not the card.**
The card contains a centred button, and it was tapped instead of the card body in
every one of the four steps-1-10 sessions. `dblclick` figures from step 10 are
valid — the event fires on the same path either way — but the card body itself was
only exercised later, in the `*-s11-12.txt` files, which is what C1 is built from.

**6. Early desktop drags left the clipped stage area.**
The first macOS session had large drags carry the card outside `#stage`'s clipped
bounds, so `mouseup` sometimes landed outside the element and suppressed `click`
for reasons unrelated to the platform. The second session's steps 4 and 6
(horizontal-only) are authoritative for those two steps; the first session is
authoritative for steps 1–3 and 7–10. Two near-zero-distance trials in the second
session's step 6 were taps, not drags, and are excluded from the child-button
large-drag count in `DERIVED.md`.

**7. Double-tap zoom could not be isolated in the original four sessions.**
The original steps 10-12 (before the harness was extended) ran under
`touch-action: none` throughout, which suppresses `dblclick` on iOS regardless of
platform behavior — producing the incorrect early conclusion that iOS never fires
`dblclick` at all. The `*-s11-12.txt` files correct this by varying `touch-action`
explicitly on the card itself. Actual page zoom (`visualViewport.scale`) still
could not be triggered reliably: the harness page is `width=device-width` with no
horizontally overflowing content, so Android found no block to zoom to, and on iOS
zoom occurred outside the card but not on it even under `auto` — meaning the card's
failure to zoom is not attributable to `touch-action`. See C1, marked 🚧.

**8. Page zoom was not reset between trials in the C13 `auto` step.**
Affects `c8-c9-c11-c13-ipad.txt` and `c8-c9-c11-c13-iphone.txt`, step 11.
`visualViewport.scale` carried over between trials instead of returning to 1.0, so
some readings reflect a pinch-in correcting a prior pinch-out rather than an
independent zoom failure. Steps 9-10 (`pan-y`, `none`) are unaffected. Treat the
exact `auto` zoom ratios in `DERIVED.md` as indicative rather than precise.

**9. Two-finger trackpad gestures produced no Pointer Events on macOS.**
`c8-c9-c11-c13-macos.txt`, steps 9-11: no `pointerdown` from a second contact was
ever observed. Trackpad pinch-zoom routes through `wheel` events with
`ctrlKey: true`, which this harness does not instrument. See C13, Verified on.

---

## How to reproduce

Serve the repository over LAN and open a harness on a real device.

```bash
python3 -m http.server 8000
ipconfig getifaddr en0
# phone → http://<ip>:8000/tools/c10-drag-vs-scroll.html
```

Append `?v=N` and increment it between edits. `http.server` sends no cache headers
and mobile browsers will silently serve a stale copy otherwise.

Simulators are not acceptable. Trackpad input in the iOS Simulator does not map to
real touch and `touch-action` behaves differently.

Start each trial with the scroll container near the middle of its range, not at an
edge — see instrumentation issue 3.

For the C13 pinch steps, reset `visualViewport.scale` to 1.0 between trials
(pinch back in, or reload) — see instrumentation issue 8.

**When pooling multiple sessions of the same measurement into one file, recount
every trial-count and boundary figure directly from the concatenated file rather
than carrying forward a number computed from a single session** — this is exactly
how the two counting errors in this document's earlier draft happened.
