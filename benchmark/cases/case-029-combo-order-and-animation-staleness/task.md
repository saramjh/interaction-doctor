This is a semantic model of a small action game's combo-attack system.
`app.js` implements `createComboGame()`, returning: `pressDirection(direction)`
(register a single directional input -- valid directions are `'D1'`, `'D2'`,
`'D3'`), `setCurrentTarget(id)` (change which entity is currently locked on
-- targets are identified by stable ids such as `'T1'`, `'T2'`, `'T3'`),
`advanceTime(ms)` (advance a deterministic fake clock, e.g. to simulate a
pause between presses), `completeAttackAnimation()` (called once the attack's
animation reaches its hit-impact moment), `getTriggerCount()` (how many times
the special move has triggered so far), and `getEntityHealth(id)` (an
entity's current health).

The special move's input is the three directional presses `D1`, then `D2`,
then `D3`, in that order, within a limited timing window. Only that order
counts as performing the move -- pressing the same three directions in a
different order does not trigger it, even though all three directions
were eventually pressed. Incomplete sequences (only one or two of the
three directions) never trigger it either. Once the timing window has
elapsed without completing the sequence, a later fresh attempt can still
trigger the move normally.

When the move triggers, the resulting attack commits to whichever target is
currently selected (via `setCurrentTarget`) at the moment the combo
triggers. The attack's damage isn't applied immediately -- it lands later,
when `completeAttackAnimation()` is called, representing the hit landing at
the animation's moment of impact. The player is free to change the
selected target at any point before that hit lands, including while the
attack's animation is still playing. Changing the selected target after an
attack has already triggered must not change who that attack hits: it
should still land on whichever target was selected at the moment the combo
triggered, not whichever target happens to be selected when the animation
finishes. A later, freshly-triggered attack is of course free to hit
whatever target is selected at the time it triggers.

Testers report two things going wrong: (1) pressing the three directions in
some order other than D1, D2, D3 can still incorrectly trigger the special
move, and (2) switching targets while an already-triggered attack's
animation is still playing can cause the hit to land on the newly-selected
target instead of the one that was selected when the attack was triggered.

Please audit the interaction handling in this project for correctness and
fix anything that's actually broken. You may run `node` against the files
in this project to check your work. Do not make unnecessary changes.
