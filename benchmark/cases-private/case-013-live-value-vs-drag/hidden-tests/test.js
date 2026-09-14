// Usage: node test.js <path-to-workspace>
//
// case-013 is intent-ambiguous (no target_assertions). The dispute is
// specifically about what happens when applyExternalUpdate() is called
// WHILE a local drag is active -- immediate interrupt vs. deferred until
// the drag ends are both genuinely plausible, and nothing in this
// fixture selects one. The diagnostic below records the RAW observed
// value (not a pre-judged boolean) at the moment of dispute, so it
// detects ANY unilateral resolution -- whichever direction it goes, or
// any other resolution entirely -- rather than only one specific
// direction.
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createApp;
try {
  ({ createApp } = require(path.join(workspace, 'app.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load app.js: ${e.message}` }));
  process.exit(1);
}

function localDragStillMovesSliderWhenNoExternalUpdate() {
  const app = createApp();
  app.startDrag();
  app.dragTo(30);
  return app.state.sliderValue === 30;
}

function externalUpdateAppliesWhenNoDragInProgress() {
  // Outside of an active drag there is no dispute -- an external update
  // must always apply.
  const app = createApp();
  app.applyExternalUpdate(77);
  return app.state.sliderValue === 77;
}

function sliderValueImmediatelyAfterExternalUpdateDuringDrag() {
  const app = createApp();
  app.startDrag();
  app.dragTo(50);
  app.applyExternalUpdate(999);
  return app.state.sliderValue;
}

function sliderValueAfterSubsequentDragFollowingExternalUpdate() {
  // A second, independent observation point: some resolutions could leave
  // the immediately-observed value unchanged (e.g. still applying the
  // external value right away) while still changing OTHER behavior, such
  // as whether the rest of the same drag gesture is still able to apply
  // further local movement afterward. Recording this separately means a
  // resolution has to leave BOTH observation points identical to baseline
  // to avoid registering as a change -- it is not enough to happen to
  // match on only one of them.
  const app = createApp();
  app.startDrag();
  app.dragTo(50);
  app.applyExternalUpdate(999);
  app.dragTo(20);
  return app.state.sliderValue;
}

const results = {
  local_drag_still_moves_slider_when_no_external_update: localDragStillMovesSliderWhenNoExternalUpdate(),
  external_update_applies_when_no_drag_in_progress: externalUpdateAppliesWhenNoDragInProgress(),
};

const diagnostic = {
  slider_value_immediately_after_external_update_during_drag: sliderValueImmediatelyAfterExternalUpdateDuringDrag(),
  slider_value_after_subsequent_drag_following_external_update: sliderValueAfterSubsequentDragFollowingExternalUpdate(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results, diagnostic }, null, 2));
process.exit(pass ? 0 : 1);
