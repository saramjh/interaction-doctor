// Minimal React-style component lifecycle harness. registerCleanup(fn)
// mirrors useEffect(() => { ...; return fn }); unmount() runs every
// registered cleanup, mirroring what happens when a component leaves the
// tree.
function createComponentHarness() {
  let cleanups = [];
  return {
    registerCleanup(fn) {
      cleanups.push(fn);
    },
    unmount() {
      for (const fn of cleanups) fn();
      cleanups = [];
    },
  };
}

module.exports = { createComponentHarness };
