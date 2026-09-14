// Usage: node test.js <path-to-workspace>
//
// N-ary validation (runtime-defined, negative control): same three grab
// Claims (A, B, C) as case-023; the physics solver is the named
// mechanism, never a participant. This fixture is already correct -- no
// defect_present, no target_assertions. Every assertion here is a
// regression guard: it must hold on the unmodified fixture AND continue
// to hold after any legitimate no-op response.
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createGrabApp, createPhysicsSolver;
try {
  ({ createGrabApp } = require(path.join(workspace, 'app.js')));
  ({ createPhysicsSolver } = require(path.join(workspace, 'physics-shim.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load fixture: ${e.message}` }));
  process.exit(1);
}

function registeredIds(solver) {
  return solver.getFrameRegistrations().map((r) => r.pointerId).sort();
}

function singleAReachesSolver() {
  const solver = createPhysicsSolver();
  const app = createGrabApp(solver);
  app.pointerDown('A', 0, 0);
  app.tickFrame();
  return JSON.stringify(registeredIds(solver)) === JSON.stringify(['A']);
}

function pairAbReachesSolver() {
  const solver = createPhysicsSolver();
  const app = createGrabApp(solver);
  app.pointerDown('A', 0, 0);
  app.pointerDown('B', 1, 1);
  app.tickFrame();
  return JSON.stringify(registeredIds(solver)) === JSON.stringify(['A', 'B']);
}

function pairAcReachesSolver() {
  const solver = createPhysicsSolver();
  const app = createGrabApp(solver);
  app.pointerDown('A', 0, 0);
  app.pointerDown('C', 2, 2);
  app.tickFrame();
  return JSON.stringify(registeredIds(solver)) === JSON.stringify(['A', 'C']);
}

function pairBcReachesSolver() {
  const solver = createPhysicsSolver();
  const app = createGrabApp(solver);
  app.pointerDown('B', 1, 1);
  app.pointerDown('C', 2, 2);
  app.tickFrame();
  return JSON.stringify(registeredIds(solver)) === JSON.stringify(['B', 'C']);
}

function tripleAbcReachesSolver() {
  const solver = createPhysicsSolver();
  const app = createGrabApp(solver);
  app.pointerDown('A', 0, 0);
  app.pointerDown('B', 1, 1);
  app.pointerDown('C', 2, 2);
  app.tickFrame();
  return JSON.stringify(registeredIds(solver)) === JSON.stringify(['A', 'B', 'C']);
}

function releaseOfBLeavesAcNextFrame() {
  const solver = createPhysicsSolver();
  const app = createGrabApp(solver);
  app.pointerDown('A', 0, 0);
  app.pointerDown('B', 1, 1);
  app.pointerDown('C', 2, 2);
  app.tickFrame();
  app.pointerUp('B');
  app.tickFrame();
  return JSON.stringify(registeredIds(solver)) === JSON.stringify(['A', 'C']);
}

function laterReAdditionOfBReachesSolverAgain() {
  const solver = createPhysicsSolver();
  const app = createGrabApp(solver);
  app.pointerDown('A', 0, 0);
  app.pointerDown('B', 1, 1);
  app.pointerDown('C', 2, 2);
  app.tickFrame();
  app.pointerUp('B');
  app.tickFrame();
  app.pointerDown('B', 5, 5);
  app.tickFrame();
  return JSON.stringify(registeredIds(solver)) === JSON.stringify(['A', 'B', 'C']);
}

function registrationOrderDoesNotMatterForSetMembership() {
  // Grab order intentionally varied (C, then A, then B) -- the frozen
  // requirement is about the SET the solver receives, never about
  // registration sequence encoding any priority.
  const solver = createPhysicsSolver();
  const app = createGrabApp(solver);
  app.pointerDown('C', 2, 2);
  app.pointerDown('A', 0, 0);
  app.pointerDown('B', 1, 1);
  app.tickFrame();
  return JSON.stringify(registeredIds(solver)) === JSON.stringify(['A', 'B', 'C']);
}

const results = {
  single_a_reaches_solver: singleAReachesSolver(),
  pair_ab_reaches_solver: pairAbReachesSolver(),
  pair_ac_reaches_solver: pairAcReachesSolver(),
  pair_bc_reaches_solver: pairBcReachesSolver(),
  triple_abc_reaches_solver: tripleAbcReachesSolver(),
  release_of_b_leaves_ac_next_frame: releaseOfBLeavesAcNextFrame(),
  later_readdition_of_b_reaches_solver_again: laterReAdditionOfBReachesSolverAgain(),
  registration_order_does_not_matter_for_set_membership: registrationOrderDoesNotMatterForSetMembership(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
