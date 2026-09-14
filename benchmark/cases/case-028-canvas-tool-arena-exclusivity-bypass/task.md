This is a small canvas editor with three gesture recognizers that share
one pointer input stream: pen drawing, canvas panning, and lasso
selection. `app.js` implements `createCanvasEditor()`: `setTool(tool)`
selects `'pen'` or `'lasso'` as the active tool, `setPanModifier(held)`
reports whether the pan modifier is currently held, `pointerDown(x, y)` /
`pointerMove(x, y)` / `pointerUp()` drive an ordinary pointer gesture
through whichever recognizer its activation condition selects,
`quickLassoActivate(x, y)` represents a dedicated shortcut that starts a
lasso selection directly, and `cancelGesture()` cancels whatever is
currently active. `getActiveGestures()` reports which of `'pen'` /
`'pan'` / `'lasso'` are currently active.

A single pointer stream must never drive more than one of these three
canvas editing gestures at once -- when their activation conditions
overlap, only one may be active at a time.

Testers report that starting a pen stroke and then triggering the lasso
shortcut while that stroke is still in progress leaves both the stroke
and the lasso selection active at the same time.

Investigate and fix the implementation in this project. You may run
`node` against the files in this project to check your work.
