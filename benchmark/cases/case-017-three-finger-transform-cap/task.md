This is a photo transform surface. `app.js` implements
`createTransformApp(touchBus)`: `touchStart(id, x, y)` / `touchMove(id, x,
y)` / `touchEnd(id)` drive touch contacts, each identified by its own id,
and the transform's `translateX`/`translateY` track the current
manipulation. `rn-shim.js` provides `createTouchBus()`, a small
model of multi-touch identity tracking (each touch has its own id,
position, and lifecycle), used so this can be tested without a real
touchscreen.

The photo transform is a two-contact manipulation. Once a two-contact
transform is active, additional concurrent contacts must not alter that
active transform.

Testers report that the photo transform behaves correctly with any two
fingers on it, but if a third finger lands on the screen while two fingers
are already manipulating the photo, the transform suddenly jumps to a
different position, even though the two original fingers haven't moved.

Investigate and fix the implementation in this project. You may run `node`
against the files in this project to check your work.
