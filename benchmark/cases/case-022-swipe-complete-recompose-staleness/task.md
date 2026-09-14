This is a semantic model of a to-do list with swipe-to-complete rows.
`app.js` implements `createTodoList(initialItemIds)`: `swipeStart(itemId)`
begins a swipe gesture on a specific item, `swipeComplete()` finishes the
gesture and marks an item done, and `resort(newOrderIds)` represents the
list being reordered (e.g. by a sort change or a real-time update) while a
swipe may still be in progress.

If a completion was started on a given item, that same item must still be
the one that completes, even if the list changes order one or more times
before the completion actually finishes.

Testers report that reordering the list while a swipe-to-complete gesture
is still in progress can cause the wrong item to end up marked done when
the gesture finishes.

Investigate and fix the implementation in this project. You may run
`node` against the files in this project to check your work.
