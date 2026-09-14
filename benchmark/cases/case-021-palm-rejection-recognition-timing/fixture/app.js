// Stylus drawing surface with a palm-rejection classifier. The surface
// commits to drawing or rejecting a touch ('promotes') the first time
// movement is reported.
function createDrawingSurface() {
  const state = {
    strokePoints: [],
    promoted: null,
    lastClassification: null,
  };

  let recognitionStarted = false;
  let classifiedAsAtStart = null;

  function pointerDown(classification) {
    recognitionStarted = true;
    classifiedAsAtStart = classification;
    state.lastClassification = classification;
  }

  function classifierUpdate(classification) {
    state.lastClassification = classification;
  }

  function pointerMove(x, y) {
    if (!recognitionStarted) return;
    if (state.promoted === null) {
      state.promoted = classifiedAsAtStart === 'PEN' ? 'draw' : 'palm-reject';
    }
    if (state.promoted === 'draw') {
      state.strokePoints.push([x, y]);
    }
  }

  function pointerUp() {
    recognitionStarted = false;
    classifiedAsAtStart = null;
  }

  return { state, pointerDown, classifierUpdate, pointerMove, pointerUp };
}

module.exports = { createDrawingSurface };
