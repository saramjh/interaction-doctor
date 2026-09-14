// Usage: node test.js <path-to-workspace>
//
// N-ary validation (runtime-defined): participants are three actual grab
// Claims (pointer ids A, B, C). The physics solver is the named
// mechanism arbitration is delegated to -- it is never itself a
// participant, and no assertion here treats it as one; every assertion
// inspects the SOLVER'S OWN getFrameRegistrations() output, i.e. what the
// app actually forwarded, never merely app-local pointer state.
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

function registrationDataPreserved() {
  const solver = createPhysicsSolver();
  const app = createGrabApp(solver);
  app.pointerDown('A', 5, 7);
  app.tickFrame();
  const reg = solver.getFrameRegistrations().find((r) => r.pointerId === 'A');
  return Boolean(reg) && reg.data.x === 5 && reg.data.y === 7;
}

function releasingOneRemovesOnlyThatOneNextFrame() {
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

function remainingClaimsContinueReachingSolverAfterRelease() {
  const solver = createPhysicsSolver();
  const app = createGrabApp(solver);
  app.pointerDown('A', 0, 0);
  app.pointerDown('B', 1, 1);
  app.pointerDown('C', 2, 2);
  app.tickFrame();
  app.pointerUp('B');
  app.pointerMove('A', 9, 9);
  app.tickFrame();
  const regs = solver.getFrameRegistrations();
  const a = regs.find((r) => r.pointerId === 'A');
  return (
    JSON.stringify(registeredIds(solver)) === JSON.stringify(['A', 'C']) &&
    Boolean(a) && a.data.x === 9 && a.data.y === 9
  );
}

function freshLaterSetOfGrabsStillWorks() {
  const solver = createPhysicsSolver();
  const app = createGrabApp(solver);
  app.pointerDown('A', 0, 0);
  app.pointerDown('B', 1, 1);
  app.pointerDown('C', 2, 2);
  app.tickFrame();
  app.pointerUp('A');
  app.pointerUp('B');
  app.pointerUp('C');
  app.pointerDown('D', 3, 3);
  app.pointerDown('E', 4, 4);
  app.tickFrame();
  return JSON.stringify(registeredIds(solver)) === JSON.stringify(['D', 'E']);
}

const results = {
  single_a_reaches_solver: singleAReachesSolver(),
  pair_ab_reaches_solver: pairAbReachesSolver(),
  pair_ac_reaches_solver: pairAcReachesSolver(),
  pair_bc_reaches_solver: pairBcReachesSolver(),
  triple_abc_reaches_solver: tripleAbcReachesSolver(),
  registration_data_preserved: registrationDataPreserved(),
  releasing_one_removes_only_that_one_next_frame: releasingOneRemovesOnlyThatOneNextFrame(),
  remaining_claims_continue_reaching_solver_after_release: remainingClaimsContinueReachingSolverAfterRelease(),
  fresh_later_set_of_grabs_still_works: freshLaterSetOfGrabsStillWorks(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
