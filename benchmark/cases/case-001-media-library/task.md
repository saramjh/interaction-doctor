You are working in a small media library UI. `app.js` builds a track card:
a `scrubber` element (drag to seek within the track) nested inside a
`carousel` element (drag to swipe between tracks). `dom-shim.js` is a tiny
fake DOM (fake elements with `addEventListener`/`dispatch`, bubbling
pointer events) that stands in for the real browser DOM in this exercise —
treat it as equivalent to real pointer events on real nested elements.

Users report that dragging the scrub bar to seek within the current track
also shifts the carousel to a different track at the same time.

Investigate and fix the implementation in this project so that:
- dragging the scrub bar seeks within the track and does not move the
  carousel
- dragging the carousel elsewhere (not starting on the scrub bar) still
  swipes between tracks as before

Make the smallest appropriate change. You may run `node` against the files
in this project to check your work.
