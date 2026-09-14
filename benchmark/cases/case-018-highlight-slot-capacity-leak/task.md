This is a shared annotation surface. `app.js` implements
`createAnnotationSurface()`: `startHighlight(id)` begins a highlight stroke
identified by its own id, `moveHighlight(id, dx)` extends it,
`endHighlight(id)` ends it, `isActive(id)` reports whether a given
highlight is currently active, and `getOffset(id)` reports its current
extent.

The annotation surface supports at least three simultaneous active
highlight strokes; starting another highlight must not end an existing
active stroke.

Testers report that when a third highlight is started while two others are
already in progress, one of the existing highlights disappears.

Investigate and fix the implementation in this project. You may run `node`
against the files in this project to check your work.
