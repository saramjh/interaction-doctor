// Toast stack with swipe-to-dismiss interactions.
const DISMISS_THRESHOLD = 50;

function createApp() {
  const state = { toasts: new Map() };
  let nextId = 1;

  function createToast(label) {
    const id = `toast-${nextId++}`;
    state.toasts.set(id, { id, label, swiping: false, dismissed: false, offset: 0 });
    return id;
  }

  function swipeStart(id) {
    const t = state.toasts.get(id);
    if (t) t.swiping = true;
  }

  function swipeMove(id, dx) {
    const t = state.toasts.get(id);
    if (t && t.swiping) t.offset += dx;
  }

  function swipeEnd(id) {
    const t = state.toasts.get(id);
    if (!t || !t.swiping) return;
    t.swiping = false;
    if (Math.abs(t.offset) > DISMISS_THRESHOLD) {
      t.dismissed = true;
    }
  }

  return { state, createToast, swipeStart, swipeMove, swipeEnd };
}

module.exports = { createApp };
