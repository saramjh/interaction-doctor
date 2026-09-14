This is a semantic model of a reorderable list row that also has native
swipe actions. `app.js` implements `createReorderableRow(initialOrder)`:
`rowDragStart(rowId, originRegion)` begins a drag, with `originRegion`
being `'handle'` (the drag started on the row's visible reorder handle) or
`'row'` (anywhere else on the row); `rowDragMove(dx)` reports incremental
horizontal movement; `rowDragEnd()` finishes the drag, applying either a
reorder or a native swipe-action reveal depending on how the drag was
recognized. `accessibilityReorder(rowId, direction)` is the accessibility
activation path for reordering (`direction` is `-1` to move a row earlier
or `1` to move it later).

Drag-to-reorder belongs specifically to the reorder handle; a drag starting
anywhere else on the row is a native swipe action, not a reorder gesture.
Reordering must also be available to assistive-technology users through
`accessibilityReorder`, producing the same result as dragging the handle,
not only through physical dragging.

Testers report that swiping a row from somewhere other than the handle
sometimes triggers a reorder instead of revealing the row's swipe actions.
Testers using accessibility tools report that there is currently no way to
reorder a row at all.

Investigate and fix the implementation in this project. You may run `node`
against the files in this project to check your work.
