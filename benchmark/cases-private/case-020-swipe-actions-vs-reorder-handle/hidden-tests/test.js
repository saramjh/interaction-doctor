// Usage: node test.js <path-to-workspace>
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createReorderableRow;
try {
  ({ createReorderableRow } = require(path.join(workspace, 'app.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load app.js: ${e.message}` }));
  process.exit(1);
}

function freshRow() {
  return createReorderableRow(['row-1', 'row-2', 'row-3']);
}

// --- Part A: routing / scope -------------------------------------------

function offHandleSwipeRevealsNativeAction() {
  const app = freshRow();
  app.rowDragStart('row-2', 'row');
  app.rowDragMove(-70);
  app.rowDragEnd();
  return app.state.swipeRevealedRowId === 'row-2';
}

function offHandleDragDoesNotReorder() {
  const app = freshRow();
  app.rowDragStart('row-2', 'row');
  app.rowDragMove(-70);
  app.rowDragEnd();
  return app.state.order.join(',') === 'row-1,row-2,row-3';
}

function onHandleDragReorders() {
  const app = freshRow();
  app.rowDragStart('row-2', 'handle');
  app.rowDragMove(-70);
  app.rowDragEnd();
  return app.state.order.join(',') === 'row-2,row-1,row-3' && app.state.swipeRevealedRowId === null;
}

// --- Part B: accessibility activation -----------------------------------

function accessibilityReorderMatchesPhysicalReorder() {
  const app = freshRow();
  if (typeof app.accessibilityReorder !== 'function') return false;
  app.accessibilityReorder('row-2', -1);
  return app.state.order.join(',') === 'row-2,row-1,row-3';
}

function nativeSwipeRemainsAvailableAfterAccessibilityAddition() {
  const app = freshRow();
  if (typeof app.accessibilityReorder === 'function') {
    app.accessibilityReorder('row-2', -1);
  }
  app.rowDragStart('row-3', 'row');
  app.rowDragMove(60);
  app.rowDragEnd();
  return app.state.swipeRevealedRowId === 'row-3';
}

// --- regression guards ---------------------------------------------------

function ordinaryRowStateIntactOnCreation() {
  const app = freshRow();
  return app.state.order.join(',') === 'row-1,row-2,row-3' && app.state.swipeRevealedRowId === null;
}

function repeatedReorderOperationsRemainValid() {
  const app = freshRow();
  app.rowDragStart('row-2', 'handle');
  app.rowDragMove(-70);
  app.rowDragEnd();
  if (typeof app.accessibilityReorder === 'function') {
    app.accessibilityReorder('row-3', -1);
  }
  return app.state.order.length === 3 && new Set(app.state.order).size === 3;
}

const results = {
  off_handle_swipe_reveals_native_action: offHandleSwipeRevealsNativeAction(),
  off_handle_drag_does_not_reorder: offHandleDragDoesNotReorder(),
  accessibility_reorder_matches_physical_reorder: accessibilityReorderMatchesPhysicalReorder(),
  native_swipe_remains_available_after_accessibility_addition: nativeSwipeRemainsAvailableAfterAccessibilityAddition(),
  on_handle_drag_reorders: onHandleDragReorders(),
  ordinary_row_state_intact_on_creation: ordinaryRowStateIntactOnCreation(),
  repeated_reorder_operations_remain_valid: repeatedReorderOperationsRemainValid(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
