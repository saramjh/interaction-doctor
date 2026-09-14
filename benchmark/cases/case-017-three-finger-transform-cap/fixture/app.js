// Photo transform driven by whichever touches are currently on the touch
// bus. translateX/translateY are the average position of the touches
// currently manipulating the transform.
function createTransformApp(touchBus) {
  const state = { translateX: 0, translateY: 0, activeManipulatorIds: [] };

  function recomputeTransform() {
    const ids = Array.from(touchBus.touches.keys());
    state.activeManipulatorIds = ids;
    if (ids.length === 0) return;
    let sumX = 0;
    let sumY = 0;
    for (const id of ids) {
      const t = touchBus.touches.get(id);
      sumX += t.x;
      sumY += t.y;
    }
    state.translateX = sumX / ids.length;
    state.translateY = sumY / ids.length;
  }

  function touchStart(id, x, y) {
    touchBus.start(id, x, y);
    recomputeTransform();
  }

  function touchMove(id, x, y) {
    touchBus.move(id, x, y);
    recomputeTransform();
  }

  function touchEnd(id) {
    touchBus.end(id);
    recomputeTransform();
  }

  return { state, touchStart, touchMove, touchEnd };
}

module.exports = { createTransformApp };
