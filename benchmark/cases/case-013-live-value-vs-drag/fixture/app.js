// Slider bound to a shared value. Local drag writes directly to
// sliderValue while dragging is true. applyExternalUpdate() can be called
// at any time, including while a drag is in progress.
function createApp() {
  const state = { sliderValue: 0, dragging: false };

  function startDrag() {
    state.dragging = true;
  }

  function dragTo(value) {
    if (state.dragging) state.sliderValue = value;
  }

  function endDrag() {
    state.dragging = false;
  }

  function applyExternalUpdate(value) {
    state.sliderValue = value;
  }

  return { state, startDrag, dragTo, endDrag, applyExternalUpdate };
}

module.exports = { createApp };
