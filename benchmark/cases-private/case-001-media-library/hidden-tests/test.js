// Usage: node test.js <path-to-workspace>
// Exits 0 and prints {"pass": true, ...} on success; exits 1 with
// {"pass": false, "reason": ...} on failure. Never shown to the evaluated agent.
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createPlayer;
try {
  ({ createPlayer } = require(path.join(workspace, 'app.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load app.js: ${e.message}` }));
  process.exit(1);
}

function scrubGestureDoesNotMoveCarousel() {
  const { scrubber, state } = createPlayer();
  scrubber.dispatch('pointerdown');
  scrubber.dispatch('pointermove', { dx: 10 });
  scrubber.dispatch('pointermove', { dx: 5 });
  scrubber.dispatch('pointerup');
  return state.scrubberValue === 15 && state.carouselOffset === 0;
}

function carouselDragStillWorks() {
  const { carousel, state } = createPlayer();
  carousel.dispatch('pointerdown');
  carousel.dispatch('pointermove', { dx: 20 });
  carousel.dispatch('pointerup');
  return state.carouselOffset === 20;
}

const results = {
  scrub_does_not_move_carousel: scrubGestureDoesNotMoveCarousel(),
  carousel_drag_still_works: carouselDragStillWorks(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
