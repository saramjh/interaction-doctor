// Kanban board: dragging a card to a new column updates the UI immediately
// (optimistic) and fires off a save request. `scheduler` stands in for the
// network layer — call moveCard(), then later the scheduler "delivers" the
// save response by calling resolve(requestId, serverColumn), in whatever
// order the test chooses, with whatever column the server actually
// confirms (see scheduler.js).
function createBoard(scheduler) {
  const state = { cardColumn: { card1: 'todo' } };

  function moveCard(cardId, targetColumn) {
    state.cardColumn[cardId] = targetColumn;
    const requestId = scheduler.schedule((serverColumn) => {
      state.cardColumn[cardId] = serverColumn;
    });
    return requestId;
  }

  return { state, moveCard };
}

module.exports = { createBoard };
