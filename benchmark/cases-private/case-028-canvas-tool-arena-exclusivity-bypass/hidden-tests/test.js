// Usage: node test.js <path-to-workspace>
//
// N-ary validation (exclusive): participants are three actual gesture
// Claims (PenDrawClaim, PanCanvasClaim, LassoSelectClaim). The recognizer
// arena is the named mechanism arbitration is delegated to for pen/pan --
// it is never itself a participant. Every assertion inspects
// getActiveGestures(), the actual observable set of concurrently-active
// gesture EFFECTS, never a single arena bookkeeping field -- this is
// deliberate: a fake "repair" that only sets an arena variable while two
// gesture implementations still run concurrently must still fail here.
//
// This case does NOT claim a pairwise-valid/triple-only shape (unlike
// case-017/018): the lasso bypass is universal (it never consults the
// arena at all), so it breaks exclusivity against EITHER other
// recognizer, in EITHER activation order. The genuine N-ary property
// being tested is that all three recognizers belong to one exclusive set
// and the invariant (concurrent active count <= 1) must hold across that
// whole set, not merely between any one specific pair.
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createCanvasEditor;
try {
  ({ createCanvasEditor } = require(path.join(workspace, 'app.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load app.js: ${e.message}` }));
  process.exit(1);
}

// --- standalone recognizer functionality (A, B, C) -------------------------

function penDrawWorksStandalone() {
  const app = createCanvasEditor();
  app.setTool('pen');
  app.pointerDown(0, 0);
  app.pointerMove(5, 5);
  app.pointerUp();
  return app.state.strokePoints.length === 2 && app.getActiveGestures().length === 0;
}

function panCanvasWorksStandalone() {
  const app = createCanvasEditor();
  app.setPanModifier(true);
  app.pointerDown(0, 0);
  app.pointerMove(10, 10);
  app.pointerUp();
  return app.state.panOffset.x === 10 && app.state.panOffset.y === 10 && app.getActiveGestures().length === 0;
}

function lassoSelectWorksStandalone() {
  const app = createCanvasEditor();
  app.quickLassoActivate(0, 0);
  app.pointerMove(20, 20);
  app.pointerUp();
  return app.state.selectionBox.endX === 20 && app.getActiveGestures().length === 0;
}

// --- pairwise exclusivity, both already-correct and buggy directions -------

function penActiveThenPanConditionStaysExclusive() {
  // D: Pen vs Pan -- both already go through the arena correctly.
  const app = createCanvasEditor();
  app.setTool('pen');
  app.pointerDown(0, 0);
  const afterPen = app.getActiveGestures();
  app.setPanModifier(true);
  app.pointerDown(5, 5);
  const afterPan = app.getActiveGestures();
  return afterPen.length === 1 && afterPen[0] === 'pen' && afterPan.length === 1 && afterPan[0] === 'pen';
}

function penActiveThenLassoConditionStaysExclusive() {
  // E: canonical bug -- pen active, then the lasso shortcut fires.
  const app = createCanvasEditor();
  app.setTool('pen');
  app.pointerDown(0, 0);
  const afterPen = app.getActiveGestures();
  app.quickLassoActivate(5, 5);
  const afterLasso = app.getActiveGestures();
  return afterPen.length === 1 && afterPen[0] === 'pen' && afterLasso.length <= 1;
}

function panActiveThenLassoConditionStaysExclusive() {
  // F: same defect, reachable via pan instead of pen.
  const app = createCanvasEditor();
  app.setPanModifier(true);
  app.pointerDown(0, 0);
  const afterPan = app.getActiveGestures();
  app.quickLassoActivate(5, 5);
  const afterLasso = app.getActiveGestures();
  return afterPan.length === 1 && afterPan[0] === 'pan' && afterLasso.length <= 1;
}

function lassoActiveThenPenConditionStaysExclusive() {
  // G: reverse ordering -- lasso active first, then pen's own activation
  // condition fires (pen's arena.tryStart() must not succeed, since
  // exclusivity is meant to hold regardless of which recognizer became
  // active first).
  const app = createCanvasEditor();
  app.quickLassoActivate(0, 0);
  const afterLasso = app.getActiveGestures();
  app.setTool('pen');
  app.pointerDown(5, 5);
  const afterPen = app.getActiveGestures();
  return afterLasso.length === 1 && afterLasso[0] === 'lasso' && afterPen.length <= 1;
}

function lassoActiveThenPanConditionStaysExclusive() {
  // G, symmetric variant with pan.
  const app = createCanvasEditor();
  app.quickLassoActivate(0, 0);
  const afterLasso = app.getActiveGestures();
  app.setPanModifier(true);
  app.pointerDown(5, 5);
  const afterPan = app.getActiveGestures();
  return afterLasso.length === 1 && afterLasso[0] === 'lasso' && afterPan.length <= 1;
}

// --- lifecycle / regression guards ------------------------------------------

function endingGestureReleasesSlotAndAnotherCanStartAfterward() {
  const app = createCanvasEditor();
  app.setTool('pen');
  app.pointerDown(0, 0);
  app.pointerUp();
  app.setPanModifier(true);
  app.pointerDown(1, 1);
  const active = app.getActiveGestures();
  return active.length === 1 && active[0] === 'pan';
}

function repeatedInteractionsDoNotLeaveStuckState() {
  const app = createCanvasEditor();
  app.setTool('pen');
  app.pointerDown(0, 0);
  app.pointerUp();
  app.pointerDown(1, 1);
  app.pointerUp();
  app.setPanModifier(true);
  app.pointerDown(2, 2);
  const active = app.getActiveGestures();
  return active.length === 1 && active[0] === 'pan';
}

function pointerUpDoesNotLeavePhantomActivity() {
  const app = createCanvasEditor();
  app.setTool('pen');
  app.pointerDown(0, 0);
  app.pointerUp();
  return app.getActiveGestures().length === 0;
}

function cancelGestureReleasesSlot() {
  const app = createCanvasEditor();
  app.setTool('pen');
  app.pointerDown(0, 0);
  app.cancelGesture();
  return app.getActiveGestures().length === 0;
}

function lassoStillWorksAfterAnEarlierConflictResolves() {
  // A prior conflicting attempt (blocked or not) must never permanently
  // disable a recognizer -- a fresh, later, standalone attempt with
  // nothing else active must still succeed normally.
  const app = createCanvasEditor();
  app.setTool('pen');
  app.pointerDown(0, 0);
  app.quickLassoActivate(5, 5);
  app.pointerUp();
  app.quickLassoActivate(10, 10);
  const active = app.getActiveGestures();
  return active.length === 1 && active[0] === 'lasso';
}

const results = {
  pen_active_then_lasso_condition_stays_exclusive: penActiveThenLassoConditionStaysExclusive(),
  pan_active_then_lasso_condition_stays_exclusive: panActiveThenLassoConditionStaysExclusive(),
  lasso_active_then_pen_condition_stays_exclusive: lassoActiveThenPenConditionStaysExclusive(),
  lasso_active_then_pan_condition_stays_exclusive: lassoActiveThenPanConditionStaysExclusive(),
  pen_draw_works_standalone: penDrawWorksStandalone(),
  pan_canvas_works_standalone: panCanvasWorksStandalone(),
  lasso_select_works_standalone: lassoSelectWorksStandalone(),
  pen_active_then_pan_condition_stays_exclusive: penActiveThenPanConditionStaysExclusive(),
  ending_gesture_releases_slot_and_another_can_start_afterward: endingGestureReleasesSlotAndAnotherCanStartAfterward(),
  repeated_interactions_do_not_leave_stuck_state: repeatedInteractionsDoNotLeaveStuckState(),
  pointer_up_does_not_leave_phantom_activity: pointerUpDoesNotLeavePhantomActivity(),
  cancel_gesture_releases_slot: cancelGestureReleasesSlot(),
  lasso_still_works_after_an_earlier_conflict_resolves: lassoStillWorksAfterAnEarlierConflictResolves(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
