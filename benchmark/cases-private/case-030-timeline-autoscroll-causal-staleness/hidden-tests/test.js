// Usage: node test.js <path-to-workspace>
//
// This case requires GENUINE recursive revalidation: fixing defect 1 (the
// leaked drag-autoscroll callback keeps executing after pointerUp) changes
// runtime reachability in a way that exposes defect 2 (click-to-place uses
// a cached scroll offset that is only ever refreshed by the leaked
// callback -- so on the buggy baseline the leak accidentally keeps that
// cache synchronized, masking defect 2 entirely).
//
// The public scheduler exposes exactly ONE way to advance time --
// advanceFrame() -- which internally runs native settle (if still
// scheduled) and then the periodic drag-autoscroll work (if still active)
// within that same frame. There is no supported public sequence that
// advances native settle while skipping the (still-leaked, on baseline)
// drag-autoscroll callback -- so masking is a reachability property of the
// runtime scheduler itself, not an artifact of a particular hidden-test
// call order. See causalAdversarialMaskingCheck() below, which tries every
// supported frame count between pointerUp() and clickTimeline() and proves
// none of them exposes defect 2 on the unmodified baseline.
//
// DEFECT FAMILY 1 (timer/release): drag_autoscroll_stops_at_release.
// DEFECT FAMILY 2 (stale coordinate): the click_during_native_settle_*
// targets. Family 2 intentionally PASSES on the unmodified baseline (it is
// masked by defect 1's leak) and FAILS once defect 1 alone is fixed -- that
// transition is the causal proof this case exists to test, not an ordinary
// regression. It remains a TARGET assertion (gates repair_success), not a
// regression guard, specifically because of that non-monotonic baseline
// behavior.
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createTimelineEditor;
try {
  ({ createTimelineEditor } = require(path.join(workspace, 'app.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load app.js: ${e.message}` }));
  process.exit(1);
}

// --- Defect family 1: timer / release ----------------------------------

function dragAutoscrollStopsAtRelease() {
  const game = createTimelineEditor();
  game.pointerDownScrubber(0);
  game.pointerUp();
  const before = game.getActualScrollOffset();
  // At this point settleFramesRemaining is whatever pointerUp() scheduled
  // AND (on the buggy baseline) drag-autoscroll is still active, so a
  // single supported advanceFrame() call is enough to prove -- if this
  // returns true -- that NEITHER settle nor a leaked drag-autoscroll
  // contribution moved the viewport, meaning drag-autoscroll must have
  // already been cancelled AND settle must not have been scheduled --
  // which is too strong a claim to make from one frame alone. Instead,
  // isolate the drag-autoscroll claim specifically: call advanceFrame()
  // repeatedly until settle is fully drained (a fixed, known number of
  // frames), then take one further frame with settle now exhausted -- any
  // further movement on that last frame is attributable to drag-autoscroll
  // alone, since settle can no longer contribute.
  for (let i = 0; i < 3; i++) game.advanceFrame(); // drains SETTLE_FRAME_COUNT
  const afterSettleDrained = game.getActualScrollOffset();
  game.advanceFrame(); // settle now contributes nothing; isolates drag-autoscroll
  const afterOneMore = game.getActualScrollOffset();
  return afterOneMore === afterSettleDrained;
}

// --- Defect family 2: stale coordinate, exposed only once defect 1 is
//     fixed (masked on the unmodified baseline). Two materially different
//     value combinations, to reject a hard-coded/guessed correction. -----

function runCausalSequence(clickX, framesBeforeClick) {
  const game = createTimelineEditor();
  game.pointerDownScrubber(0);
  game.pointerUp();
  for (let i = 0; i < framesBeforeClick; i++) game.advanceFrame();
  const actualAtClick = game.getActualScrollOffset();
  const kf = game.clickTimeline(clickX);
  return kf.contentX === clickX + actualAtClick;
}

function clickDuringNativeSettleUsesCurrentVisualContentPosition() {
  return runCausalSequence(10, 1);
}

function clickDuringNativeSettleUsesCurrentVisualContentPositionVariant() {
  return runCausalSequence(25, 2);
}

// --- Causal adversarial check: no supported public schedule between
//     pointerUp() and clickTimeline() exposes defect 2 on baseline. -------

function causalAdversarialMaskingCheck() {
  // Try every supported frame count from 0 up through full settle
  // completion (and one frame beyond, to also cover the fully-settled
  // state) -- the only way to advance time at all is advanceFrame(),
  // so this exhausts every reachable schedule between release and click.
  for (let frames = 0; frames <= 4; frames++) {
    const game = createTimelineEditor();
    game.pointerDownScrubber(0);
    game.pointerUp();
    for (let i = 0; i < frames; i++) game.advanceFrame();
    const actualAtClick = game.getActualScrollOffset();
    const kf = game.clickTimeline(7);
    if (kf.contentX !== 7 + actualAtClick) return false;
  }
  return true;
}

// --- Regression guards ---------------------------------------------------

function edgeAutoscrollWorksDuringActiveDrag() {
  const game = createTimelineEditor();
  game.pointerDownScrubber(0);
  const before = game.getActualScrollOffset();
  game.advanceFrame(); // no settle scheduled yet -- isolates the autoscroll tick
  const after = game.getActualScrollOffset();
  return after === before + 5;
}

function pointerMovementDuringScrubStillWorks() {
  const game = createTimelineEditor();
  game.pointerDownScrubber(0);
  game.pointerMoveScrubber(12);
  return game.state.lastScrubX === 12 && game.isDragging() === true;
}

function pointerUpEndsDraggingState() {
  const game = createTimelineEditor();
  game.pointerDownScrubber(0);
  game.pointerUp();
  return game.isDragging() === false;
}

function nativeSettleStillOccursAfterRelease() {
  const game = createTimelineEditor();
  game.pointerDownScrubber(0);
  game.pointerUp();
  const settleScheduled = game.state.settleFramesRemaining === 3;
  const before = game.getActualScrollOffset();
  game.advanceFrame();
  const after = game.getActualScrollOffset();
  const settleDecremented = game.state.settleFramesRemaining === 2;
  // Movement must be AT LEAST the settle contribution -- on the buggy
  // baseline it will be more (settle + the still-leaked drag-autoscroll
  // contribution), which is fine; this guard only proves settle itself
  // is still scheduled and still contributing, not that it's the only
  // thing contributing (drag_autoscroll_stops_at_release covers that).
  return settleScheduled && settleDecremented && after >= before + 3;
}

function ordinaryClickWithNoPendingSettleCorrect() {
  const game = createTimelineEditor();
  const kf = game.clickTimeline(7);
  const placed = game.getPlacedKeyframes();
  return placed.length === 1 && placed[0].contentX === 7 && kf.contentX === 7;
}

function clickPlacementAfterSettleFullyCompletesCorrect() {
  const game = createTimelineEditor();
  game.pointerDownScrubber(0);
  game.pointerUp();
  for (let i = 0; i < 3; i++) game.advanceFrame(); // fully drains settle
  const actual = game.getActualScrollOffset();
  const kf = game.clickTimeline(4);
  return kf.contentX === 4 + actual;
}

function freshScrubAfterReleaseWorks() {
  const game = createTimelineEditor();
  game.pointerDownScrubber(0);
  game.pointerUp();
  game.pointerDownScrubber(1);
  return game.isDragging() === true;
}

function laterOrdinaryClickStillWorks() {
  const game = createTimelineEditor();
  game.pointerDownScrubber(0);
  game.pointerUp();
  game.advanceFrame();
  game.clickTimeline(10); // first click, not asserted here
  const actualBeforeSecond = game.getActualScrollOffset();
  const kf = game.clickTimeline(50); // a later click, no further frames elapsed
  return kf.contentX === 50 + actualBeforeSecond;
}

function noDuplicateKeyframeFromOneClick() {
  const game = createTimelineEditor();
  game.clickTimeline(3);
  return game.getPlacedKeyframes().length === 1;
}

function autoscrollNotPermanentlyDisabledAfterCleanup() {
  const game = createTimelineEditor();
  game.pointerDownScrubber(0);
  game.pointerUp();
  for (let i = 0; i < 3; i++) game.advanceFrame(); // fully drain this cycle's pending settle
  game.pointerDownScrubber(1); // fresh drag, no settle pending now
  const before = game.getActualScrollOffset();
  game.advanceFrame(); // fresh drag's own autoscroll tick, isolated
  const after = game.getActualScrollOffset();
  return after === before + 5;
}

const results = {
  drag_autoscroll_stops_at_release: dragAutoscrollStopsAtRelease(),
  click_during_native_settle_uses_current_visual_content_position: clickDuringNativeSettleUsesCurrentVisualContentPosition(),
  click_during_native_settle_uses_current_visual_content_position_variant: clickDuringNativeSettleUsesCurrentVisualContentPositionVariant(),

  causal_adversarial_masking_check: causalAdversarialMaskingCheck(),
  edge_autoscroll_works_during_active_drag: edgeAutoscrollWorksDuringActiveDrag(),
  pointer_movement_during_scrub_still_works: pointerMovementDuringScrubStillWorks(),
  pointerup_ends_dragging_state: pointerUpEndsDraggingState(),
  native_settle_still_occurs_after_release: nativeSettleStillOccursAfterRelease(),
  ordinary_click_with_no_pending_settle_correct: ordinaryClickWithNoPendingSettleCorrect(),
  click_placement_after_settle_fully_completes_correct: clickPlacementAfterSettleFullyCompletesCorrect(),
  fresh_scrub_after_release_works: freshScrubAfterReleaseWorks(),
  later_ordinary_click_still_works: laterOrdinaryClickStillWorks(),
  no_duplicate_keyframe_from_one_click: noDuplicateKeyframeFromOneClick(),
  autoscroll_not_permanently_disabled_after_cleanup: autoscrollNotPermanentlyDisabledAfterCleanup(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
