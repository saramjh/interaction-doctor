// Shared canvas: a drag targets a shape by id. splitShape(id) simulates a
// concurrent structural edit arriving mid-drag -- the original shape is
// replaced by two new shapes with new ids, and the original id becomes
// invalid.
function createApp() {
  const state = {
    shapes: { 'shape-1': { id: 'shape-1', x: 0, y: 0 } },
    drag: null, // { targetShapeId } while a drag is active
  };

  function startDrag(shapeId) {
    state.drag = { targetShapeId: shapeId };
  }

  function moveDrag(dx, dy) {
    if (!state.drag) return;
    const shape = state.shapes[state.drag.targetShapeId];
    if (!shape) return;
    shape.x += dx;
    shape.y += dy;
  }

  function endDrag() {
    state.drag = null;
  }

  function splitShape(id) {
    const original = state.shapes[id];
    if (!original) return [];

    delete state.shapes[id];
    const successorAId = `${id}-a`;
    const successorBId = `${id}-b`;
    state.shapes[successorAId] = { id: successorAId, x: original.x, y: original.y };
    state.shapes[successorBId] = { id: successorBId, x: original.x, y: original.y };

    if (state.drag && state.drag.targetShapeId === id) {
      state.drag = null;
    }

    return [successorAId, successorBId];
  }

  return { state, startDrag, moveDrag, endDrag, splitShape };
}

module.exports = { createApp };
