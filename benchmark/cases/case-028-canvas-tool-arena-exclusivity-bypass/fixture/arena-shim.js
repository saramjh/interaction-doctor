// Small recognizer arena: tryStart(id) succeeds only if nothing else is
// currently active; end(id) releases the slot if it is the current
// holder.
function createArena() {
  let activeId = null;
  return {
    tryStart(id) {
      if (activeId !== null) return false;
      activeId = id;
      return true;
    },
    end(id) {
      if (activeId === id) activeId = null;
    },
    getActive() {
      return activeId;
    },
  };
}

module.exports = { createArena };
