// Small model of native active-window focus. setActive(isActive) reports
// the window gaining or losing active focus; onFocusChange(fn) registers
// a listener notified of that transition.
function createFocusTracker() {
  let listeners = [];
  return {
    onFocusChange(fn) {
      listeners.push(fn);
    },
    setActive(isActive) {
      for (const fn of listeners) fn(isActive);
    },
  };
}

module.exports = { createFocusTracker };
