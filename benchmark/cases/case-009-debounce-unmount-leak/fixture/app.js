// Search box: typing schedules a debounced suggestions request against
// `clock`. `harness` is the component's mount/unmount lifecycle (see
// harness.js).
const DEBOUNCE_MS = 300;

function createSearchBox(harness, clock) {
  const state = { query: '', suggestions: null, requestCount: 0 };

  function type(query) {
    state.query = query;
    clock.setTimeout(() => {
      state.requestCount += 1;
      state.suggestions = `results for ${query}`;
    }, DEBOUNCE_MS);
  }

  return { state, type };
}

module.exports = { createSearchBox };
