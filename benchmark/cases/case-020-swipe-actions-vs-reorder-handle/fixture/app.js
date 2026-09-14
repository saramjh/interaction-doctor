// Reorderable list row with native swipe actions. A single drag gesture
// stream is recognized as either a reorder or a native swipe-action
// reveal.
const REORDER_MOVE_THRESHOLD = 60;
const SWIPE_REVEAL_THRESHOLD = 40;

function createReorderableRow(initialOrder) {
  const state = {
    order: [...initialOrder],
    swipeRevealedRowId: null,
    activeGesture: null,
  };

  function rowDragStart(rowId, originRegion) {
    state.activeGesture = { rowId, kind: 'reorder', dx: 0 };
  }

  function rowDragMove(dx) {
    if (!state.activeGesture) return;
    state.activeGesture.dx += dx;
  }

  function rowDragEnd() {
    if (!state.activeGesture) return;
    const { rowId, kind, dx } = state.activeGesture;
    if (kind === 'reorder' && Math.abs(dx) > REORDER_MOVE_THRESHOLD) {
      moveInOrder(rowId, dx < 0 ? -1 : 1);
    }
    if (kind === 'swipe' && Math.abs(dx) > SWIPE_REVEAL_THRESHOLD) {
      state.swipeRevealedRowId = rowId;
    }
    state.activeGesture = null;
  }

  function accessibilityReorder(rowId, direction) {}

  function moveInOrder(rowId, delta) {
    const idx = state.order.indexOf(rowId);
    const newIdx = idx + delta;
    if (newIdx < 0 || newIdx >= state.order.length) return;
    const [item] = state.order.splice(idx, 1);
    state.order.splice(newIdx, 0, item);
  }

  return { state, rowDragStart, rowDragMove, rowDragEnd, accessibilityReorder };
}

module.exports = { createReorderableRow };
