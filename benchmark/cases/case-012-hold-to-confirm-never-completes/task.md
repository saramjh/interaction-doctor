This is a hold-to-confirm delete button. `app.js` implements
`createHoldButton(clock, holdDurationMs)`: `pointerdown()` starts tracking a
hold, `tick()` checks progress (standing in for a periodic timer/animation
check in a real app), and `pointerup()` releases the hold. Holding for the
full `holdDurationMs` without releasing should confirm the action exactly
once. `clock.js` is a small deterministic fake timer used so this can be
tested without waiting on wall-clock time.

Testers report that holding the button down, even well past the expected
duration, never actually confirms anything -- the action just never fires,
no matter how long they hold it.

Investigate and fix the implementation in this project. You may run `node`
against the files in this project to check your work.
