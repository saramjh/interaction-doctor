// Tool window with a custom drag-to-resize border.
function createResizableWindow(focusTracker) {
  const state = { width: 200, height: 200, resizing: false };

  function mousePress() {
    state.resizing = true;
  }

  function mouseMove(dx, dy) {
    if (state.resizing) {
      state.width += dx;
      state.height += dy;
    }
  }

  function mouseRelease() {
    state.resizing = false;
  }

  focusTracker.onFocusChange((isActive) => {});

  return { state, mousePress, mouseMove, mouseRelease };
}

module.exports = { createResizableWindow };
