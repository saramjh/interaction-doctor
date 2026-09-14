// Usage: node test.js <path-to-workspace>
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createCanvas;
try {
  ({ createCanvas } = require(path.join(workspace, 'canvas.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load canvas.js: ${e.message}` }));
  process.exit(1);
}

function panWhileSpaceHeldDoesNotDraw() {
  const c = createCanvas();
  c.keydownSpace();
  c.pointerdown(0);
  c.pointermove(10, 10);
  c.pointerup();
  c.keyupSpace();
  return c.state.panOffset === 10 && c.state.strokes.length === 0;
}

function drawWithoutSpaceDoesNotPan() {
  const c = createCanvas();
  c.pointerdown(0);
  c.pointermove(10, 10);
  c.pointerup();
  return c.state.panOffset === 0 && c.state.strokes.length === 1 && c.state.strokes[0].length === 2;
}

function switchingModeMidwayIsUnaffectedByLaterSpaceChange() {
  // Space is pressed AFTER a draw gesture has already started; the
  // in-progress gesture must keep drawing (mode was decided at
  // pointerdown), matching a real "hold to temporarily switch tool" UX.
  const c = createCanvas();
  c.pointerdown(0);
  c.keydownSpace();
  c.pointermove(5, 5);
  c.pointerup();
  return c.state.strokes.length === 1 && c.state.panOffset === 0;
}

const results = {
  pan_while_space_held_does_not_draw: panWhileSpaceHeldDoesNotDraw(),
  draw_without_space_does_not_pan: drawWithoutSpaceDoesNotPan(),
  mode_decided_at_pointerdown_not_reevaluated_midgesture: switchingModeMidwayIsUnaffectedByLaterSpaceChange(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
