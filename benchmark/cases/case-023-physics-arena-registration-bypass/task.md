This is a semantic model of a shared rigid-body manipulation surface,
backed by a physics solver. `physics-shim.js` provides
`createPhysicsSolver()`: `registerGrab(pointerId, data)` records a grab
registration for the current frame, `clearFrameRegistrations()` clears the
frame's registrations, and `getFrameRegistrations()` returns whatever was
registered. `app.js` implements `createGrabApp(solver)`: `pointerDown(
pointerId, x, y)` / `pointerMove(pointerId, x, y)` / `pointerUp(pointerId)`
track active pointer grabs on the body, and `tickFrame()` is called once
per frame to forward the currently active grabs to the solver.

Every currently active pointer grab must be forwarded to the solver every
frame; the solver, not the application, is responsible for deciding how
simultaneous grabs on the same body are resolved. The application must
not pre-select which active grabs the solver is allowed to see.

Testers report that when three fingers are simultaneously grabbing the
body, the solver ends up only seeing two of them -- the third finger's
movement has no effect at all, even though it's still actively held down.

Investigate and fix the implementation in this project. You may run
`node` against the files in this project to check your work.
