// Usage: node test.js <path-to-workspace>
//
// N-ary validation (simultaneous): participants are three actual
// highlight Claims (A, B, C), never any shared storage structure itself.
// A+B alone passes even on the buggy fixture (a real two-slot cap never
// gets exercised by only two participants); the A+B+C case is where the
// buggy artificial capacity(2) becomes observable, and the hidden oracle
// requires all three to coexist to detect it.
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createAnnotationSurface;
try {
  ({ createAnnotationSurface } = require(path.join(workspace, 'app.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load app.js: ${e.message}` }));
  process.exit(1);
}

function aStartsThenPresent() {
  const s = createAnnotationSurface();
  s.startHighlight('A');
  return s.isActive('A') === true;
}

function aAndBBothPresent() {
  const s = createAnnotationSurface();
  s.startHighlight('A');
  s.startHighlight('B');
  return s.isActive('A') === true && s.isActive('B') === true;
}

function allThreePresentAfterCStarts() {
  const s = createAnnotationSurface();
  s.startHighlight('A');
  s.startHighlight('B');
  s.startHighlight('C');
  return s.isActive('A') === true && s.isActive('B') === true && s.isActive('C') === true;
}

function updatingCDoesNotMutateOthers() {
  const s = createAnnotationSurface();
  s.startHighlight('A');
  s.startHighlight('B');
  s.startHighlight('C');
  s.moveHighlight('C', 10);
  return s.getOffset('A') === 0 && s.getOffset('B') === 0 && s.getOffset('C') === 10;
}

function endingOneDoesNotRemoveOthers() {
  const s = createAnnotationSurface();
  s.startHighlight('A');
  s.startHighlight('B');
  s.endHighlight('A');
  return s.isActive('A') === false && s.isActive('B') === true;
}

function laterHighlightStillWorks() {
  const s = createAnnotationSurface();
  s.startHighlight('A');
  s.endHighlight('A');
  s.startHighlight('D');
  return s.isActive('D') === true;
}

const results = {
  a_starts_then_present: aStartsThenPresent(),
  a_and_b_both_present: aAndBBothPresent(),
  all_three_present_after_c_starts: allThreePresentAfterCStarts(),
  updating_c_does_not_mutate_others: updatingCDoesNotMutateOthers(),
  ending_one_does_not_remove_others: endingOneDoesNotRemoveOthers(),
  later_highlight_still_works: laterHighlightStillWorks(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
