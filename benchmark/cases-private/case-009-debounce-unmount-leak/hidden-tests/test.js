// Usage: node test.js <path-to-workspace>
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createSearchBox, createFakeClock, createComponentHarness;
try {
  ({ createSearchBox } = require(path.join(workspace, 'app.js')));
  ({ createFakeClock } = require(path.join(workspace, 'clock.js')));
  ({ createComponentHarness } = require(path.join(workspace, 'harness.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load fixture: ${e.message}` }));
  process.exit(1);
}

function normalDebounceStillWorksWhileMounted() {
  const clock = createFakeClock();
  const harness = createComponentHarness();
  const box = createSearchBox(harness, clock);

  box.type('cats');
  clock.advance(200); // less than the debounce delay
  const notYet = box.state.requestCount === 0 && box.state.suggestions === null;

  clock.advance(200); // now past the delay (400ms total)
  const fired = box.state.requestCount === 1 && box.state.suggestions === 'results for cats';

  return notYet && fired;
}

function unmountBeforeExpiryPreventsStaleMutation() {
  const clock = createFakeClock();
  const harness = createComponentHarness();
  const box = createSearchBox(harness, clock);

  box.type('dogs');
  harness.unmount();
  clock.advance(1000); // well past the delay

  return box.state.requestCount === 0 && box.state.suggestions === null;
}

function cancelOnUnmountDoesNotDisableFutureInstance() {
  const clock = createFakeClock();

  const harnessA = createComponentHarness();
  const boxA = createSearchBox(harnessA, clock);
  boxA.type('first');
  harnessA.unmount(); // unmounted before its debounce fires

  const harnessB = createComponentHarness();
  const boxB = createSearchBox(harnessB, clock);
  boxB.type('second');
  clock.advance(400);

  return boxB.state.requestCount === 1 && boxB.state.suggestions === 'results for second';
}

const results = {
  normal_debounce_still_works_while_mounted: normalDebounceStillWorksWhileMounted(),
  unmount_before_expiry_prevents_stale_mutation: unmountBeforeExpiryPreventsStaleMutation(),
  cancel_on_unmount_does_not_disable_future_instance: cancelOnUnmountDoesNotDisableFutureInstance(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
