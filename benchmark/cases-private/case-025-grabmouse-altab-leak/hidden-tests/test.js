// Usage: node test.js <path-to-workspace>
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createResizableWindow, createFocusTracker;
try {
  ({ createResizableWindow } = require(path.join(workspace, 'app.js')));
  ({ createFocusTracker } = require(path.join(workspace, 'focus-shim.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load fixture: ${e.message}` }));
  process.exit(1);
}

function ordinaryResizeWorks() {
  const focus = createFocusTracker();
  const win = createResizableWindow(focus);
  win.mousePress();
  win.mouseMove(10, 10);
  win.mouseRelease();
  return win.state.width === 210 && win.state.height === 210;
}

function focusLossDuringActiveResizeEndsIt() {
  // Checks BOTH that the interaction is released AND that releasing it
  // does not itself apply any extra delta to the window size.
  const focus = createFocusTracker();
  const win = createResizableWindow(focus);
  win.mousePress();
  win.mouseMove(10, 10);
  focus.setActive(false);
  return win.state.resizing === false && win.state.width === 210 && win.state.height === 210;
}

function staleDeltaAfterFocusLossDoesNotMutateSize() {
  const focus = createFocusTracker();
  const win = createResizableWindow(focus);
  win.mousePress();
  win.mouseMove(10, 10);
  focus.setActive(false);
  win.mouseMove(50, 50); // stale delta, no new press
  return win.state.width === 210 && win.state.height === 210;
}

function refocusAloneDoesNotResumeResize() {
  const focus = createFocusTracker();
  const win = createResizableWindow(focus);
  win.mousePress();
  win.mouseMove(10, 10);
  focus.setActive(false);
  focus.setActive(true); // refocus, no new press
  win.mouseMove(5, 5);
  return win.state.width === 210 && win.state.height === 210;
}

function freshResizeAfterRefocusWorks() {
  const focus = createFocusTracker();
  const win = createResizableWindow(focus);
  win.mousePress();
  win.mouseMove(10, 10);
  focus.setActive(false);
  focus.setActive(true);
  win.mousePress(); // new press after refocus
  win.mouseMove(7, 7);
  return win.state.width === 217 && win.state.height === 217;
}

function focusLossWithNoActiveResizeIsHarmless() {
  const focus = createFocusTracker();
  const win = createResizableWindow(focus);
  focus.setActive(false);
  focus.setActive(true);
  return win.state.width === 200 && win.state.height === 200;
}

function normalReleaseThenStaleMoveHasNoEffect() {
  const focus = createFocusTracker();
  const win = createResizableWindow(focus);
  win.mousePress();
  win.mouseMove(10, 10);
  win.mouseRelease();
  win.mouseMove(99, 99); // stale, no press
  return win.state.width === 210 && win.state.height === 210;
}

const results = {
  focus_loss_during_active_resize_ends_it: focusLossDuringActiveResizeEndsIt(),
  stale_delta_after_focus_loss_does_not_mutate_size: staleDeltaAfterFocusLossDoesNotMutateSize(),
  refocus_alone_does_not_resume_resize: refocusAloneDoesNotResumeResize(),
  ordinary_resize_works: ordinaryResizeWorks(),
  fresh_resize_after_refocus_works: freshResizeAfterRefocusWorks(),
  focus_loss_with_no_active_resize_is_harmless: focusLossWithNoActiveResizeIsHarmless(),
  normal_release_then_stale_move_has_no_effect: normalReleaseThenStaleMoveHasNoEffect(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
