This is a slider control bound to a shared value. `app.js` implements
`createApp()`: `startDrag()` / `dragTo(value)` / `endDrag()` drive a local
drag of the slider, and `applyExternalUpdate(value)` simulates a live
update arriving from an external source (e.g. another collaborator, or a
server push) that can update the same underlying value at any time,
including while a local drag is in progress.

When an external update arrives while a local drag is active, the current
implementation immediately replaces the slider value with the external
value. A subsequent local drag update (before the drag ends) then changes
it again to whatever the user drags to next.

Investigate and address this in `app.js` if appropriate. You may run `node`
against the files in this project to check your work.
