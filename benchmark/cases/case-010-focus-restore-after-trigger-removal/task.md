This is a list of items, each with a "..." trigger button that opens a
confirm-delete dialog for that row. `app.js` implements `createApp()`:
`openDeleteModal(rowId)` opens the dialog for a row and moves focus to its
confirm button, `confirmDelete()` removes that row and closes the dialog,
`cancelDeleteModal()` closes the dialog without removing anything and
returns focus to the row's trigger. `state.focusedElementId` tracks which
element currently has keyboard focus (standing in for
`document.activeElement`, by element id, since there's no real DOM here).

Testers report that after confirming a delete, keyboard focus is no longer
restored to a usable destination.

Investigate and address this in `app.js`. You may run `node` against the
files in this project to check your work.
