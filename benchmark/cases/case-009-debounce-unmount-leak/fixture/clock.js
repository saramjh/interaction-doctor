// Deterministic fake timer, standing in for the real browser/Node timer
// so debounce behavior can be tested without depending on wall-clock time.
function createFakeClock() {
  let now = 0;
  let timers = [];
  let nextId = 1;

  return {
    now: () => now,
    setTimeout(fn, delay) {
      const id = nextId++;
      timers.push({ id, fireAt: now + delay, fn });
      return id;
    },
    clearTimeout(id) {
      timers = timers.filter((t) => t.id !== id);
    },
    advance(ms) {
      now += ms;
      const due = timers.filter((t) => t.fireAt <= now).sort((a, b) => a.fireAt - b.fireAt);
      timers = timers.filter((t) => t.fireAt > now);
      for (const t of due) t.fn();
    },
  };
}

module.exports = { createFakeClock };
