# research/measurements

Raw output from the verification harnesses in `tools/`, and the pooled figures
derived from it.

Every number that appears in `CONFLICTS.md` traces to a file here. If a claim in the
matrix cannot be traced to a log in this directory, it should not be in the matrix.

---

## Files

```
README.md          this file — provenance and known instrumentation issues
DERIVED.md         pooled figures used in CONFLICTS.md, with trial counts

c10-android.txt    C10 harness, Android 10 / Chrome 143
c10-ipad.txt       C10 harness, iPadOS 26.6 / Safari 26.6
c10-iphone.txt     C10 harness, iOS 18.7 / Safari

c3c6-android-1.txt C3/C6 harness, Android — session 1
c3c6-android-2.txt C3/C6 harness, Android — session 2
c3c6-android-3.txt C3/C6 harness, Android — session 3
c3c6-ipad-1.txt    C3/C6 harness, iPadOS — session 1
c3c6-ipad-2.txt    C3/C6 harness, iPadOS — session 2
c3c6-iphone.txt    C3/C6 harness, iOS
c3c6-macos-1.txt   C3/C6 harness, macOS Chrome 142, mouse input
c3c6-macos-2.txt   C3/C6 harness, macOS — steps 4 and 6 only, horizontal drags
```

## Devices

| label   | OS / browser                         | viewport     | touch points |
| ------- | ------------------------------------ | ------------ | ------------ |
| android | Android 10 / Chrome 143              | 412×892 @3.5 | 5            |
| ipad    | iPadOS 26.6 / Safari 26.6 (iPad Pro) | 1024×1366 @2 | 5            |
| iphone  | iOS 18.7 / Safari                    | 375×667 @2   | 5            |
| macos   | macOS 26.6.2 / Chrome 142            | 2140×1391 @2 | 0 (mouse)    |

All measurements taken 2026-08-29.

iPadOS reports a Macintosh user agent. It is identified here by `maxTouchPoints > 1`
and confirmed by hand. Do not trust the `ua-detect` line on that device.

---

## Known instrumentation issues

These affect how the logs should be read. None of them invalidate the figures in
`DERIVED.md`, which were selected to avoid the affected fields.

**1. `dur` is negative in early C3/C6 sessions.**
Affects `c3c6-android-1.txt`, `c3c6-android-2.txt`, `c3c6-iphone.txt`.
The gesture length subtracted the 700 ms settle window even when the gesture was
force-closed early by the next `pointerdown`. Fixed by recording `endAt` at
`pointerup`. **`dist`, `clickAt`, `ctxAt` and the fired-event set are unaffected** —
all derived figures use those fields, not `dur`.

**2. iOS callout swallows alternate trials.**
Affects `c3c6-iphone.txt` and `c3c6-ipad-1.txt`, step 7.
Once the native selection callout opens, subsequent touches go to the overlay and
never reach the page. Trials alternate between a genuine long press
(`dur` ≈ 900 ms, `selChars` > 0) and a tap that only dismissed the menu
(`childClick`, `dur` < 100 ms). Discard the dismissal trials.
This is itself a finding — see C6, Precedence, item 4.

**3. Scroll position not controlled in C10 step 1.**
Every trial began with the list at the top, so the container could not scroll
upward. Only the cancellation result from that step is comparable across platforms;
the `scrollAfter` value is not.

**4. Gap zone was not instrumented in the first iPhone session.**
`c3c6` is unaffected, but C10 step 4 trial 1 on iPhone registered as a drag because
the harness had not yet excluded the gap zone from drag activation. 2 of 3 trials
remain valid.

**5. C3/C6 step 10 targeted the child button.**
The card contains a centred button and it was tapped instead of the card body in
every session. `dblclick` figures from step 10 are valid — the event fires on the
same path either way — but the card body was only exercised in steps 11–12.

**6. Desktop drags leaving the element.**
In `c3c6-macos-1.txt`, large drags moved the card outside the clipped stage area.
Re-run as `c3c6-macos-2.txt` with horizontal-only drags. Both files are retained:
the second is authoritative for steps 4 and 6, the first for steps 1–3 and 7–10.

**7. Double-tap zoom could not be measured.**
Steps 11–12 vary `touch-action` and record `dblclick` reliably, but zoom itself was
never triggered. The harness page is `width=device-width` with no horizontally
overflowing content, so Android Chrome found no block to zoom to and no zoom
occurred anywhere on the page. On iOS, zoom occurred outside the card but not on it,
including under `touch-action: auto` — so the card's failure to zoom is not
attributable to `touch-action`. Isolating zoom behaviour requires a page built for
that purpose. See C1, marked 🚧.

---

## How to reproduce

Serve the repository over LAN and open the harness on a real device.

```bash
python3 -m http.server 8000
ipconfig getifaddr en0
# phone → http://<ip>:8000/tools/c10-drag-vs-scroll.html
```

Append `?v=N` and increment it between edits. `http.server` sends no cache headers
and mobile browsers will silently serve a stale copy otherwise — this produced one
discarded session.

Simulators are not acceptable. Trackpad input in the iOS Simulator does not map to
real touch and `touch-action` behaves differently.

Start each trial with the scroll container near the middle of its range.
