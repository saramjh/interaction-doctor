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

function singleToastDismissesAlone() {
  const app = createApp();
  const a = app.createToast('A');
  app.swipeStart(a);
  app.swipeMove(a, 60);
  app.swipeEnd(a);
  return app.state.toasts.get(a).dismissed === true;
}

function bothToastsCanBeActivelySwipingSimultaneously() {
  // The crux of this negative control: nothing shared/global should
  // prevent two DIFFERENT toasts from being mid-swipe at the same time.
  const app = createApp();
  const a = app.createToast('A');
  const b = app.createToast('B');
  app.swipeStart(a);
  app.swipeStart(b);
  return app.state.toasts.get(a).swiping === true && app.state.toasts.get(b).swiping === true;
}

function twoToastsInterleavedSwipeBothDismissIndependently() {
  const app = createApp();
  const a = app.createToast('A');
  const b = app.createToast('B');
  app.swipeStart(a);
  app.swipeStart(b);
  app.swipeMove(a, 30);
  app.swipeMove(b, 10);
  app.swipeMove(a, 30); // a: total 60, past threshold
  app.swipeMove(b, 10); // b: total 20, short of threshold
  app.swipeEnd(a);
  app.swipeEnd(b);
  return app.state.toasts.get(a).dismissed === true && app.state.toasts.get(b).dismissed === false;
}

function dismissingOneDoesNotAffectOther() {
  const app = createApp();
  const a = app.createToast('A');
  const b = app.createToast('B');
  app.swipeStart(a);
  app.swipeMove(a, 60);
  app.swipeEnd(a); // a dismissed

  // b must still be independently swipeable after a's dismissal
  app.swipeStart(b);
  app.swipeMove(b, 60);
  app.swipeEnd(b);
  return (
    app.state.toasts.get(a).dismissed === true &&
    app.state.toasts.get(b).dismissed === true
  );
}

function laterCreatedToastStillWorksAfterEarlierActivity() {
  const app = createApp();
  const a = app.createToast('A');
  app.swipeStart(a);
  app.swipeMove(a, 60);
  app.swipeEnd(a);

  const c = app.createToast('C'); // created after prior swipe activity
  app.swipeStart(c);
  app.swipeMove(c, 60);
  app.swipeEnd(c);
  return app.state.toasts.get(c).dismissed === true;
}

const results = {
  single_toast_dismisses_alone: singleToastDismissesAlone(),
  both_toasts_can_be_actively_swiping_simultaneously: bothToastsCanBeActivelySwipingSimultaneously(),
  two_toasts_interleaved_swipe_both_dismiss_independently: twoToastsInterleavedSwipeBothDismissIndependently(),
  dismissing_one_does_not_affect_other: dismissingOneDoesNotAffectOther(),
  later_created_toast_still_works_after_earlier_activity: laterCreatedToastStillWorksAfterEarlierActivity(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
