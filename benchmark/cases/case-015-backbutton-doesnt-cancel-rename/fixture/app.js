// Inline rename flow. longPressStart begins editing an item's name;
// commitRename/cancelRename explicitly end it; unrelatedTapElsewhere
// represents ordinary interaction with something else in the list while a
// rename may or may not still be in progress.
function createRenameFlow(backHandler) {
  const state = {
    items: { 'item-1': 'Old Name', 'item-2': 'Another Item' },
    renaming: false,
    itemId: null,
    draftValue: null,
    keyboardVisible: false,
  };

  function longPressStart(itemId, currentValue) {
    state.renaming = true;
    state.itemId = itemId;
    state.draftValue = currentValue;
    state.keyboardVisible = true;
  }

  function typeText(text) {
    if (state.renaming) state.draftValue = text;
  }

  function commitRename() {
    if (!state.renaming) return;
    state.items[state.itemId] = state.draftValue;
    state.renaming = false;
    state.keyboardVisible = false;
  }

  function cancelRename() {
    if (!state.renaming) return;
    state.renaming = false;
    state.keyboardVisible = false;
  }

  function unrelatedTapElsewhere() {
    if (state.renaming) {
      state.items[state.itemId] = state.draftValue;
      state.renaming = false;
    }
  }

  backHandler.addListener(() => {
    if (state.keyboardVisible) {
      state.keyboardVisible = false;
      return true;
    }
    return false;
  });

  return { state, longPressStart, typeText, commitRename, cancelRename, unrelatedTapElsewhere };
}

module.exports = { createRenameFlow };
