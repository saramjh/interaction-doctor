This is an inline rename interaction for a list of items. `app.js`
implements `createRenameFlow(backHandler)`: `longPressStart(itemId,
currentValue)` begins renaming an item (as if triggered by a long-press),
`typeText(text)` edits the draft, `commitRename()` explicitly saves the
draft, `cancelRename()` explicitly discards it, and `unrelatedTapElsewhere()`
represents the user tapping somewhere else in the list, unrelated to the
rename. `rn-shim.js` provides `createBackHandler()`, a small model of
Android's hardware Back button dispatch (`BackHandler.addEventListener` /
a handler returning `true` marks the press handled).

In this screen, hardware Back while renaming is defined to leave the item
unchanged and exit the rename flow -- the same outcome as pressing an
explicit cancel control.

Testers report that occasionally, after pressing the Android Back button
while renaming an item and then tapping elsewhere in the list, that item's
name changes to whatever had been typed -- even though the rename was
never explicitly confirmed.

Investigate and fix the implementation in this project. You may run `node`
against the files in this project to check your work.
