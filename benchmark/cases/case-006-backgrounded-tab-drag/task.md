This is a draggable side panel. `app.js` builds a `panel` element that
accumulates a `panelOffset` from pointer drag deltas while the pointer is
held down, and a `document` element that dispatches a `visibilitychange`
event whenever the browser tab is backgrounded or foregrounded (`hidden:
true` / `hidden: false`), matching the real
`document.addEventListener('visibilitychange', ...)` / `document.hidden`
API. `dom-shim.js` is a tiny fake DOM (fake elements with
`addEventListener`/`dispatch`, bubbling events) that stands in for the
real browser DOM in this exercise -- treat it as equivalent to real
pointer and visibility events.

Users report that if they start dragging the panel and then switch to a
different browser tab mid-drag, the panel sometimes keeps moving on its
own once they switch back, as if the drag never ended.

Investigate and fix the implementation in this project. You may run
`node` against the files in this project to check your work.
