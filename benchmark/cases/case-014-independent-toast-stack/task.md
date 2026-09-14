This is a stack of dismissible toast notifications. `app.js` implements
`createApp()`: `createToast(label)` adds a new toast and returns its id;
`swipeStart(id)` / `swipeMove(id, dx)` / `swipeEnd(id)` drive swiping a
specific toast to dismiss it (past a distance threshold, releasing
dismisses it; short of the threshold, it snaps back).

Please audit the interaction handling in this project for correctness and
fix anything that's actually broken. You may run `node` against the files
in this project to check your work. Do not make unnecessary changes.
