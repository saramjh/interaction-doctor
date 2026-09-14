// Usage: node test.js <path-to-workspace>
//
// case-011 is intent-ambiguous (no target_assertions). The regression
// guards below specifically prove the SAFE MECHANICAL FLOOR is already
// correct in the canonical fixture (stale target not mutated; drag
// safely releases on split) -- per the v3.1 design, that floor is not the
// bug here and must not be credited as one. The diagnostic detects only
// the disputed continuation-policy question.
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

function staleOriginalShapeNotMutatedAfterSplit() {
  const app = createApp();
  app.startDrag('shape-1');
  const [successorAId, successorBId] = app.splitShape('shape-1');
  app.moveDrag(5, 5);
  return (
    app.state.shapes['shape-1'] === undefined &&
    app.state.shapes[successorAId].x === 0 &&
    app.state.shapes[successorAId].y === 0 &&
    app.state.shapes[successorBId].x === 0 &&
    app.state.shapes[successorBId].y === 0
  );
}

function dragSafelyReleasesOnSplit() {
  const app = createApp();
  app.startDrag('shape-1');
  app.splitShape('shape-1');
  return app.state.drag === null;
}

function ordinaryDragWithoutSplitStillWorks() {
  const app = createApp();
  app.startDrag('shape-1');
  app.moveDrag(5, 5);
  app.endDrag();
  return app.state.shapes['shape-1'].x === 5 && app.state.shapes['shape-1'].y === 5;
}

function autoContinuedOntoASuccessorAfterSplit() {
  // Purely descriptive: records whether the drag Claim was auto-transferred
  // onto EITHER successor after a split, versus released (the canonical,
  // unresolved-and-safe behavior). Detects the disputed policy regardless
  // of which of the two successors a unilateral implementation might pick.
  const app = createApp();
  app.startDrag('shape-1');
  const [successorAId, successorBId] = app.splitShape('shape-1');
  app.moveDrag(3, 3);
  if (!app.state.drag) return false;
  const target = app.state.drag.targetShapeId;
  return target === successorAId || target === successorBId;
}

const results = {
  stale_original_shape_not_mutated_after_split: staleOriginalShapeNotMutatedAfterSplit(),
  drag_safely_releases_on_split: dragSafelyReleasesOnSplit(),
  ordinary_drag_without_split_still_works: ordinaryDragWithoutSplitStillWorks(),
};

const diagnostic = {
  auto_continued_onto_a_successor_after_split: autoContinuedOntoASuccessorAfterSplit(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results, diagnostic }, null, 2));
process.exit(pass ? 0 : 1);
