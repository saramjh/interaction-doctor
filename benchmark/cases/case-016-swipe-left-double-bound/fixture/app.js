// Message row: a left-swipe gesture is tracked via swipeLeftStart/Move/End.
// Two features each react to the completed gesture based on how far left
// it travelled.
const ARCHIVE_THRESHOLD = 80;
const QUICK_REPLY_THRESHOLD = 40;

function createMessageRow() {
  const state = {
    dx: 0,
    swiping: false,
    archived: false,
    quickReplyOpen: false,
  };

  function swipeLeftStart() {
    state.swiping = true;
    state.dx = 0;
  }

  function swipeLeftMove(delta) {
    if (state.swiping) state.dx += delta;
  }

  function swipeLeftEnd() {
    if (!state.swiping) return;
    state.swiping = false;
    const magnitude = Math.abs(state.dx);
    if (state.dx < 0 && magnitude >= ARCHIVE_THRESHOLD) {
      state.archived = true;
    }
    if (state.dx < 0 && magnitude >= QUICK_REPLY_THRESHOLD) {
      state.quickReplyOpen = true;
    }
  }

  return { state, swipeLeftStart, swipeLeftMove, swipeLeftEnd };
}

module.exports = { createMessageRow };
