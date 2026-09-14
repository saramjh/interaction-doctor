// Small model of the Android hardware Back dispatch contract:
// BackHandler.addEventListener('hardwareBackPress', fn) registers a
// handler; handlers are consulted most-recently-added first; a handler
// returning true marks the event handled and stops further propagation.
function createBackHandler() {
  let listeners = [];
  return {
    addListener(fn) {
      listeners = [fn, ...listeners];
      return {
        remove() {
          listeners = listeners.filter((l) => l !== fn);
        },
      };
    },
    dispatchBackPress() {
      for (const fn of listeners) {
        if (fn() === true) return true;
      }
      return false;
    },
  };
}

module.exports = { createBackHandler };
