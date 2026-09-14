This is a kanban board. `board.js` implements `createBoard(scheduler)`:
dragging a card to a new column updates `state.cardColumn[cardId]`
immediately (optimistic UI), then fires a save request via
`scheduler.schedule(fn)`, which represents a network round trip — the
caller later delivers the server's response by calling
`scheduler.resolve(requestId, serverColumn)` whenever it actually arrives,
passing whatever column the server confirms. `scheduler.js` is a
deterministic stand-in for the network layer, used so this can be tested
without real timers.

Users report that if they drag a card twice in quick succession (e.g. from
"To Do" to "In Progress", then immediately to "Done"), the card sometimes
snaps back to "In Progress" a moment later, even though they left it in
"Done". This appears to depend on which save request's network response
happens to arrive first, which the user has no control over.

Investigate and fix `board.js` (and `scheduler.js` if needed) so that a
card's column always ends up reflecting the user's most recent drag,
regardless of what order in-flight save responses arrive in — while still
correctly applying a server response (e.g. a rejection that reverts the
column) when that response is for the card's current, still-relevant
request. Do not change the public shape of `createBoard`/`moveCard`
unless necessary. You may run `node` against the files in this project to
check your work.
