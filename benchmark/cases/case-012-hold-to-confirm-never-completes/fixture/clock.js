// Deterministic fake clock, standing in for the real browser/Node timer
// so hold-duration behavior can be tested without wall-clock time.
function createFakeClock() {
  let now = 0;
  return {
    now: () => now,
    advance(ms) {
      now += ms;
    },
  };
}

module.exports = { createFakeClock };
