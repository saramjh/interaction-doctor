// Canvas editor with three gesture recognizers sharing one pointer
// stream: pen drawing, canvas panning, and lasso selection.
const { createArena } = require('./arena-shim');

function createCanvasEditor() {
  const arena = createArena();
  const state = {
    tool: 'pen',
    panModifierHeld: false,
    penDrawActive: false,
    panCanvasActive: false,
    lassoSelectActive: false,
    strokePoints: [],
    panOffset: { x: 0, y: 0 },
    selectionBox: null,
  };

  function setTool(tool) {
    state.tool = tool;
  }

  function setPanModifier(held) {
    state.panModifierHeld = held;
  }

  function pointerDown(x, y) {
    if (state.panModifierHeld) {
      if (arena.tryStart('pan')) {
        state.panCanvasActive = true;
      }
      return;
    }
    if (state.tool === 'pen') {
      if (arena.tryStart('pen')) {
        state.penDrawActive = true;
        state.strokePoints = [[x, y]];
      }
      return;
    }
    if (state.tool === 'lasso') {
      if (arena.tryStart('lasso')) {
        state.lassoSelectActive = true;
        state.selectionBox = { startX: x, startY: y, endX: x, endY: y };
      }
      return;
    }
  }

  function pointerMove(x, y) {
    if (state.panCanvasActive) {
      state.panOffset.x += x;
      state.panOffset.y += y;
    } else if (state.penDrawActive) {
      state.strokePoints.push([x, y]);
    } else if (state.lassoSelectActive) {
      state.selectionBox.endX = x;
      state.selectionBox.endY = y;
    }
  }

  function pointerUp() {
    if (state.panCanvasActive) {
      arena.end('pan');
      state.panCanvasActive = false;
    }
    if (state.penDrawActive) {
      arena.end('pen');
      state.penDrawActive = false;
    }
    if (state.lassoSelectActive) {
      arena.end('lasso');
      state.lassoSelectActive = false;
    }
  }

  function quickLassoActivate(x, y) {
    state.lassoSelectActive = true;
    state.selectionBox = { startX: x, startY: y, endX: x, endY: y };
  }

  function cancelGesture() {
    if (state.panCanvasActive) {
      arena.end('pan');
      state.panCanvasActive = false;
    }
    if (state.penDrawActive) {
      arena.end('pen');
      state.penDrawActive = false;
    }
    if (state.lassoSelectActive) {
      arena.end('lasso');
      state.lassoSelectActive = false;
    }
  }

  function getActiveGestures() {
    const active = [];
    if (state.penDrawActive) active.push('pen');
    if (state.panCanvasActive) active.push('pan');
    if (state.lassoSelectActive) active.push('lasso');
    return active;
  }

  return {
    state,
    setTool,
    setPanModifier,
    pointerDown,
    pointerMove,
    pointerUp,
    quickLassoActivate,
    cancelGesture,
    getActiveGestures,
  };
}

module.exports = { createCanvasEditor };
