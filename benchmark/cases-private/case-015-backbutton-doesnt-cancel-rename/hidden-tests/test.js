// Usage: node test.js <path-to-workspace>
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createRenameFlow, createBackHandler;
try {
  ({ createRenameFlow } = require(path.join(workspace, 'app.js')));
  ({ createBackHandler } = require(path.join(workspace, 'rn-shim.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load fixture: ${e.message}` }));
  process.exit(1);
}

function backCancelsRenameInteraction() {
  const backHandler = createBackHandler();
  const flow = createRenameFlow(backHandler);
  flow.longPressStart('item-1', 'Old Name');
  flow.typeText('New Draft');
  backHandler.dispatchBackPress();
  return flow.state.renaming === false;
}

function backThenUnrelatedTapDoesNotCommitStaleDraft() {
  const backHandler = createBackHandler();
  const flow = createRenameFlow(backHandler);
  flow.longPressStart('item-1', 'Old Name');
  flow.typeText('New Draft');
  backHandler.dispatchBackPress();
  flow.unrelatedTapElsewhere();
  return flow.state.items['item-1'] === 'Old Name';
}

function backCancellationDoesNotCommitDraftByItself() {
  // Guards against a "fix" that makes Back commit the draft instead of
  // discarding it.
  const backHandler = createBackHandler();
  const flow = createRenameFlow(backHandler);
  flow.longPressStart('item-1', 'Old Name');
  flow.typeText('New Draft');
  backHandler.dispatchBackPress();
  return flow.state.items['item-1'] === 'Old Name';
}

function explicitCommitStillWorks() {
  const backHandler = createBackHandler();
  const flow = createRenameFlow(backHandler);
  flow.longPressStart('item-1', 'Old Name');
  flow.typeText('New Draft');
  flow.commitRename();
  return flow.state.items['item-1'] === 'New Draft' && flow.state.renaming === false;
}

function explicitCancelPreservesOriginalValue() {
  const backHandler = createBackHandler();
  const flow = createRenameFlow(backHandler);
  flow.longPressStart('item-1', 'Old Name');
  flow.typeText('New Draft');
  flow.cancelRename();
  return flow.state.items['item-1'] === 'Old Name' && flow.state.renaming === false;
}

function newRenameAfterBackCancellationWorksNormally() {
  // Guards against an over-broad "fix" that permanently disables rename
  // (or the back handler) after the first Back press.
  const backHandler = createBackHandler();
  const flow = createRenameFlow(backHandler);
  flow.longPressStart('item-1', 'Old Name');
  flow.typeText('discarded');
  backHandler.dispatchBackPress();

  flow.longPressStart('item-2', 'Another Item');
  flow.typeText('Renamed Item 2');
  flow.commitRename();
  return flow.state.items['item-2'] === 'Renamed Item 2';
}

const results = {
  back_cancels_rename_interaction: backCancelsRenameInteraction(),
  back_then_unrelated_tap_does_not_commit_stale_draft: backThenUnrelatedTapDoesNotCommitStaleDraft(),
  back_cancellation_does_not_commit_draft_by_itself: backCancellationDoesNotCommitDraftByItself(),
  explicit_commit_still_works: explicitCommitStillWorks(),
  explicit_cancel_preserves_original_value: explicitCancelPreservesOriginalValue(),
  new_rename_after_back_cancellation_works_normally: newRenameAfterBackCancellationWorksNormally(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
