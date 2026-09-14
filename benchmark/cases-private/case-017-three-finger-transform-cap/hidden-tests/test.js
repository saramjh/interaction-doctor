// Usage: node test.js <path-to-workspace>
//
// N-ary validation (capacity(2)): participants are three actual touch
// Claims (A, B, C), never the touch bus / recognizer mechanism itself.
// Every pairwise combination (A+B, A+C, B+C) is independently valid; only
// the full three-participant state exposes the capacity violation, which
// requires all three to be simultaneously reachable -- pair_ab/ac/bc_works
// alone cannot see it.
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createTransformApp, createTouchBus;
try {
  ({ createTransformApp } = require(path.join(workspace, 'app.js')));
  ({ createTouchBus } = require(path.join(workspace, 'rn-shim.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load fixture: ${e.message}` }));
  process.exit(1);
}

function pairAbWorks() {
  const bus = createTouchBus();
  const app = createTransformApp(bus);
  app.touchStart('A', 0, 0);
  app.touchStart('B', 10, 0);
  return app.state.translateX === 5 && app.state.translateY === 0;
}

function pairAcWorks() {
  const bus = createTouchBus();
  const app = createTransformApp(bus);
  app.touchStart('A', 0, 0);
  app.touchStart('C', 1000, 1000);
  return app.state.translateX === 500 && app.state.translateY === 500;
}

function pairBcWorks() {
  const bus = createTouchBus();
  const app = createTransformApp(bus);
  app.touchStart('B', 10, 0);
  app.touchStart('C', 1000, 1000);
  return app.state.translateX === 505 && app.state.translateY === 500;
}

function capacityHeldWhenThirdJoins() {
  const bus = createTouchBus();
  const app = createTransformApp(bus);
  app.touchStart('A', 0, 0);
  app.touchStart('B', 10, 0);
  const beforeX = app.state.translateX;
  const beforeY = app.state.translateY;

  app.touchStart('C', 1000, 1000); // third contact, far outlier
  app.touchMove('C', 2000, 2000); // moving it must not change the transform

  return app.state.translateX === beforeX && app.state.translateY === beforeY;
}

function abContinueCorrectlyWhileCapacityFull() {
  const bus = createTouchBus();
  const app = createTransformApp(bus);
  app.touchStart('A', 0, 0);
  app.touchStart('B', 10, 0);
  app.touchStart('C', 1000, 1000);
  app.touchMove('A', 20, 0); // A+B centroid should now be (15, 0)
  return app.state.translateX === 15 && app.state.translateY === 0;
}

function releasingOneParticipantDoesNotCorruptRemaining() {
  const bus = createTouchBus();
  const app = createTransformApp(bus);
  app.touchStart('A', 0, 0);
  app.touchStart('B', 10, 0);
  app.touchEnd('A');
  return app.state.translateX === 10 && app.state.translateY === 0;
}

function futureOrdinaryTwoFingerTransformStillWorks() {
  const bus = createTouchBus();
  const app = createTransformApp(bus);
  app.touchStart('A', 0, 0);
  app.touchStart('B', 10, 0);
  app.touchEnd('A');
  app.touchEnd('B');
  app.touchStart('D', 4, 0);
  app.touchStart('E', 8, 0);
  return app.state.translateX === 6 && app.state.translateY === 0;
}

const results = {
  pair_ab_works: pairAbWorks(),
  pair_ac_works: pairAcWorks(),
  pair_bc_works: pairBcWorks(),
  capacity_held_when_third_joins: capacityHeldWhenThirdJoins(),
  ab_continue_correctly_while_capacity_full: abContinueCorrectlyWhileCapacityFull(),
  releasing_one_participant_does_not_corrupt_remaining: releasingOneParticipantDoesNotCorruptRemaining(),
  future_ordinary_two_finger_transform_still_works: futureOrdinaryTwoFingerTransformStillWorks(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
