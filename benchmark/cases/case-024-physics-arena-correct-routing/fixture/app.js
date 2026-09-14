// Rigid-body grab app: each active pointer represents a grab attempt on
// the shared body. tickFrame() forwards the currently active grabs to the
// physics solver.
function createGrabApp(solver) {
  const state = { activePointers: {} };

  function pointerDown(pointerId, x, y) {
    state.activePointers[pointerId] = { x, y };
  }

  function pointerMove(pointerId, x, y) {
    if (state.activePointers[pointerId]) {
      state.activePointers[pointerId] = { x, y };
    }
  }

  function pointerUp(pointerId) {
    delete state.activePointers[pointerId];
  }

  function tickFrame() {
    solver.clearFrameRegistrations();
    const ids = Object.keys(state.activePointers);
    for (const id of ids) {
      solver.registerGrab(id, state.activePointers[id]);
    }
  }

  return { state, pointerDown, pointerMove, pointerUp, tickFrame };
}

module.exports = { createGrabApp };
