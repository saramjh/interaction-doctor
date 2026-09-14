// Timeline/editor viewport. Edge scrub-drag drives periodic auto-scroll
// while active; a separate native scroll-settle can continue briefly
// after release. Clicking the timeline places a keyframe at the content
// position under the pointer.
const AUTOSCROLL_TICK_DELTA = 5;
const SETTLE_TICK_DELTA = 3;
const SETTLE_FRAME_COUNT = 3;

function createTimelineEditor() {
  const state = {
    dragging: false,
    autoscrollActive: false,
    lastScrubX: null,
    scrollActual: 0,
    scrollCached: 0,
    settleFramesRemaining: 0,
    keyframes: [],
  };

  function pointerDownScrubber(x) {
    state.dragging = true;
    state.autoscrollActive = true;
    state.lastScrubX = x;
  }

  function pointerMoveScrubber(x) {
    state.lastScrubX = x;
  }

  function pointerUp() {
    state.dragging = false;
    state.settleFramesRemaining = SETTLE_FRAME_COUNT;
  }

  // Advances one runtime frame. Within a single frame, any native-settle
  // work still scheduled runs first, followed by the periodic
  // drag-autoscroll work if it is still active for that frame. There is
  // no way to advance one without the other -- both are driven by the
  // same underlying per-frame scheduler.
  function advanceFrame() {
    if (state.settleFramesRemaining > 0) {
      state.scrollActual += SETTLE_TICK_DELTA;
      state.settleFramesRemaining -= 1;
    }
    if (state.autoscrollActive) {
      state.scrollActual += AUTOSCROLL_TICK_DELTA;
      state.scrollCached = state.scrollActual;
    }
  }

  function clickTimeline(viewportX) {
    const contentX = viewportX + state.scrollCached;
    const keyframe = { viewportX, contentX };
    state.keyframes.push(keyframe);
    return keyframe;
  }

  function getActualScrollOffset() {
    return state.scrollActual;
  }

  function getPlacedKeyframes() {
    return state.keyframes;
  }

  function isDragging() {
    return state.dragging;
  }

  return {
    state,
    pointerDownScrubber,
    pointerMoveScrubber,
    pointerUp,
    advanceFrame,
    clickTimeline,
    getActualScrollOffset,
    getPlacedKeyframes,
    isDragging,
  };
}

module.exports = { createTimelineEditor };
