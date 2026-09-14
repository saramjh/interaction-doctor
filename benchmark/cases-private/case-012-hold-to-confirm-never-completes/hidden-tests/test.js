// Usage: node test.js <path-to-workspace>
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createHoldButton, createFakeClock;
try {
  ({ createHoldButton } = require(path.join(workspace, 'app.js')));
  ({ createFakeClock } = require(path.join(workspace, 'clock.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load fixture: ${e.message}` }));
  process.exit(1);
}

function holdingLessThanThresholdDoesNotFire() {
  const clock = createFakeClock();
  const btn = createHoldButton(clock, 600);
  btn.pointerdown();
  clock.advance(300);
  btn.tick();
  return btn.state.confirmedCount === 0;
}

function reachingThresholdFiresExactlyOnce() {
  const clock = createFakeClock();
  const btn = createHoldButton(clock, 600);
  btn.pointerdown();
  clock.advance(600);
  btn.tick();
  const firedOnce = btn.state.confirmedCount === 1;
  btn.tick();
  const stillOne = btn.state.confirmedCount === 1;
  return firedOnce && stillOne;
}

function continuingToHoldDoesNotRepeatedlyFire() {
  const clock = createFakeClock();
  const btn = createHoldButton(clock, 600);
  btn.pointerdown();
  clock.advance(600);
  btn.tick(); // fires once
  clock.advance(1000);
  btn.tick(); // still holding=false by now; must not fire again
  return btn.state.confirmedCount === 1;
}

function earlyReleaseDoesNotFire() {
  const clock = createFakeClock();
  const btn = createHoldButton(clock, 600);
  btn.pointerdown();
  clock.advance(300);
  btn.pointerup();
  clock.advance(1000);
  btn.tick();
  return btn.state.confirmedCount === 0;
}

function ordinarySubsequentHoldsStillWork() {
  const clock = createFakeClock();
  const btn = createHoldButton(clock, 600);
  btn.pointerdown();
  clock.advance(300);
  btn.pointerup(); // cancelled early
  btn.pointerdown(); // fresh hold attempt
  clock.advance(600);
  btn.tick();
  return btn.state.confirmedCount === 1;
}

const results = {
  reaching_threshold_fires_exactly_once: reachingThresholdFiresExactlyOnce(),
  continuing_to_hold_does_not_repeatedly_fire: continuingToHoldDoesNotRepeatedlyFire(),
  ordinary_subsequent_holds_still_work: ordinarySubsequentHoldsStillWork(),
  holding_less_than_threshold_does_not_fire: holdingLessThanThresholdDoesNotFire(),
  early_release_does_not_fire: earlyReleaseDoesNotFire(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
