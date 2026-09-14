// A draggable panel. Dragging accumulates `panelOffset` from pointermove
// deltas while the pointer is down. `visibilitychange` fires when the
// browser tab is backgrounded/foregrounded (e.g. the user switches tabs
// mid-drag) -- dispatched here as `documentEl.dispatch('visibilitychange',
// { hidden })`, matching the real document.visibilitychange contract.
const { FakeElement } = require('./dom-shim');

function createApp() {
  const documentEl = new FakeElement('document');
  const panel = new FakeElement('panel', documentEl);

  const state = { panelOffset: 0, dragging: false };

  panel.addEventListener('pointerdown', () => {
    state.dragging = true;
  });
  panel.addEventListener('pointermove', (e) => {
    if (state.dragging) state.panelOffset += e.dx;
  });
  panel.addEventListener('pointerup', () => {
    state.dragging = false;
  });

  documentEl.addEventListener('visibilitychange', (e) => {});

  return { state, documentEl, panel };
}

module.exports = { createApp };
