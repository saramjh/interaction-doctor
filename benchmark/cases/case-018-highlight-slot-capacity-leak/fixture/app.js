// Annotation surface: each highlight stroke is identified by its own id.
function createAnnotationSurface() {
  const state = { slotA: null, slotB: null };

  function startHighlight(id) {
    if (!state.slotA) {
      state.slotA = { id, offset: 0 };
      return;
    }
    if (!state.slotB) {
      state.slotB = { id, offset: 0 };
      return;
    }
    state.slotA = state.slotB;
    state.slotB = { id, offset: 0 };
  }

  function moveHighlight(id, dx) {
    if (state.slotA && state.slotA.id === id) state.slotA.offset += dx;
    if (state.slotB && state.slotB.id === id) state.slotB.offset += dx;
  }

  function endHighlight(id) {
    if (state.slotA && state.slotA.id === id) state.slotA = null;
    if (state.slotB && state.slotB.id === id) state.slotB = null;
  }

  function isActive(id) {
    return Boolean((state.slotA && state.slotA.id === id) || (state.slotB && state.slotB.id === id));
  }

  function getOffset(id) {
    if (state.slotA && state.slotA.id === id) return state.slotA.offset;
    if (state.slotB && state.slotB.id === id) return state.slotB.offset;
    return undefined;
  }

  return { state, startHighlight, moveHighlight, endHighlight, isActive, getOffset };
}

module.exports = { createAnnotationSurface };
