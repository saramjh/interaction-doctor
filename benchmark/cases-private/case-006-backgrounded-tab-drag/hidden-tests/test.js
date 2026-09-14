// Usage: node test.js <path-to-workspace>
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

function dragReleasesOnBackgrounding() {
  const { state, documentEl, panel } = createApp();
  panel.dispatch('pointerdown');
  panel.dispatch('pointermove', { dx: 5 });
  documentEl.dispatch('visibilitychange', { hidden: true });
  // A delta delivered after backgrounding (queued before, or delivered
  // once the tab regains focus) must not still apply.
  panel.dispatch('pointermove', { dx: 7 });
  return state.panelOffset === 5;
}

function normalDragStillWorks() {
  const { state, panel } = createApp();
  panel.dispatch('pointerdown');
  panel.dispatch('pointermove', { dx: 10 });
  panel.dispatch('pointerup');
  return state.panelOffset === 10;
}

function foregroundingEventDoesNotSpuriouslyCancelDrag() {
  const { state, documentEl, panel } = createApp();
  panel.dispatch('pointerdown');
  panel.dispatch('pointermove', { dx: 3 });
  documentEl.dispatch('visibilitychange', { hidden: false }); // foregrounding, not backgrounding
  panel.dispatch('pointermove', { dx: 4 });
  return state.panelOffset === 7;
}

const results = {
  drag_releases_on_backgrounding: dragReleasesOnBackgrounding(),
  normal_drag_still_works: normalDragStillWorks(),
  foregrounding_event_does_not_spuriously_cancel_drag: foregroundingEventDoesNotSpuriouslyCancelDrag(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
