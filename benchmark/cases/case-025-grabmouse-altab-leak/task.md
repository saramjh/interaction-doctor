This is a semantic model of a tool window with a custom drag-to-resize
border. `app.js` implements `createResizableWindow(focusTracker)`:
`mousePress()` begins a resize (as if the user pressed on the window's
resize border, comparable to Qt's `grabMouse()` semantics), `mouseMove(dx,
dy)` extends the resize, and `mouseRelease()` ends it normally.
`focus-shim.js` provides `createFocusTracker()`: `onFocusChange(fn)`
registers a listener, and `setActive(isActive)` reports the window
gaining (`true`) or losing (`false`) native active-window focus (e.g. the
user switches to another application via Alt-Tab).

A resize is only active while the window retains active focus. If the
window loses active focus while a resize is in progress, that resize ends
immediately; regaining focus afterward does not resume it, and the user
may begin a fresh resize once focus returns.

Testers report that if the window loses focus (e.g. via Alt-Tab) partway
through a resize and then regains focus, further pointer movement can
continue resizing the window from where the interrupted drag left off,
even though the user never pressed again.

Investigate and fix the implementation in this project. You may run
`node` against the files in this project to check your work.
