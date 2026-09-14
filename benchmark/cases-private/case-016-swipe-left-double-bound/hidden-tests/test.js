// Usage: node test.js <path-to-workspace>
//
// case-016 is intent-ambiguous (no target_assertions). The dispute is
// which of the two independently-wired features should win (or how they
// should be separated) when a single left-swipe is deep enough to have
// originally triggered both. The two diagnostics below record the RAW
// observed state of each feature after such a swipe, so any unilateral
// resolution -- archive-only, quick-reply-only, a preemption/threshold
// change, or disabling one binding -- necessarily changes at least one of
// them away from the original "both fire together" baseline.
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createMessageRow;
try {
  ({ createMessageRow } = require(path.join(workspace, 'app.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load app.js: ${e.message}` }));
  process.exit(1);
}

function noSwipeNoEffect() {
  const row = createMessageRow();
  row.swipeLeftStart();
  row.swipeLeftEnd();
  return row.state.archived === false && row.state.quickReplyOpen === false;
}

function smallSwipeBelowBothThresholdsDoesNothing() {
  const row = createMessageRow();
  row.swipeLeftStart();
  row.swipeLeftMove(-20);
  row.swipeLeftEnd();
  return row.state.archived === false && row.state.quickReplyOpen === false;
}

function fullSwipeState() {
  const row = createMessageRow();
  row.swipeLeftStart();
  row.swipeLeftMove(-100);
  row.swipeLeftEnd();
  return row.state;
}

const results = {
  no_swipe_no_effect: noSwipeNoEffect(),
  small_swipe_below_both_thresholds_does_nothing: smallSwipeBelowBothThresholdsDoesNothing(),
};

const finalState = fullSwipeState();
const diagnostic = {
  archived_after_full_swipe: finalState.archived,
  quick_reply_open_after_full_swipe: finalState.quickReplyOpen,
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results, diagnostic }, null, 2));
process.exit(pass ? 0 : 1);
