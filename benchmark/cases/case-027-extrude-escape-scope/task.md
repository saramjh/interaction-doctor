This is a small CAD-style viewport with modal commands. `app.js`
implements `createViewport()`: `startExtrude()` / `startRotate()` /
`startScale()` begin their respective modal commands; `beginNumericEntry()`
enters a nested numeric-entry sub-state for typing an exact value while a
command is active; `typeNumericValue(value)` updates the live preview;
`confirm()` commits the current command; `pressEscape()` cancels.
`getMode()`, `hasPreview()`, and `getPreviewValue()` report the current
state.

Testers report that after starting EXTRUDE, entering the numeric sub-state,
typing an exact distance, and pressing Escape, the application remains in
EXTRUDE mode and a preview can remain visible.

Investigate and fix the implementation in this project. You may run
`node` against the files in this project to check your work.
