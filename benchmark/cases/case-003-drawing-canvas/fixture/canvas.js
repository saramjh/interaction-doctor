// Drawing canvas: holding the spacebar switches the pointer to a pan tool;
// releasing it returns to freehand drawing. A single `mode` flag, set
// exclusively at pointerdown time from the current spacebar state, decides
// which behavior a given pointer gesture gets — so a drag that starts
// while space is held pans, and a drag that starts without space held
// draws, and the two can never both apply to the same gesture.
function createCanvas() {
  const state = { mode: 'idle', strokes: [], panOffset: 0, spaceHeld: false };

  function keydownSpace() {
    state.spaceHeld = true;
  }

  function keyupSpace() {
    state.spaceHeld = false;
  }

  function pointerdown(x) {
    if (state.spaceHeld) {
      state.mode = 'panning';
    } else {
      state.mode = 'drawing';
      state.strokes.push([x]);
    }
  }

  function pointermove(x, dx) {
    if (state.mode === 'panning') {
      state.panOffset += dx;
    } else if (state.mode === 'drawing') {
      state.strokes[state.strokes.length - 1].push(x);
    }
  }

  function pointerup() {
    state.mode = 'idle';
  }

  return { state, keydownSpace, keyupSpace, pointerdown, pointermove, pointerup };
}

module.exports = { createCanvas };
