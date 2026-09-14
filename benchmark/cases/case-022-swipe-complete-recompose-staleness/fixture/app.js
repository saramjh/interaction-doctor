// To-do list with swipe-to-complete rows. swipeStart(itemId) begins a
// swipe on the row currently showing that item; resort() can change which
// item is at which position while a swipe is still in progress.
function createTodoList(initialItemIds) {
  const state = {
    items: initialItemIds.map((id) => ({ id, completed: false })),
    swipeInProgress: null,
  };

  function swipeStart(itemId) {
    const position = state.items.findIndex((i) => i.id === itemId);
    state.swipeInProgress = { position };
  }

  function swipeComplete() {
    if (!state.swipeInProgress) return;
    const item = state.items[state.swipeInProgress.position];
    if (item) item.completed = true;
    state.swipeInProgress = null;
  }

  function resort(newOrderIds) {
    state.items = newOrderIds.map((id) => state.items.find((i) => i.id === id));
  }

  return { state, swipeStart, swipeComplete, resort };
}

module.exports = { createTodoList };
