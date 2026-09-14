// CAD-style modal command state machine. Each command (EXTRUDE, ROTATE,
// SCALE) supports a nested numeric-entry sub-state for typing an exact
// value; typing updates a live preview.
function createViewport() {
  const state = {
    mode: 'IDLE',
    preview: null,
    numericValue: null,
  };

  function startExtrude() {
    state.mode = 'EXTRUDE';
    state.preview = { command: 'EXTRUDE', value: null };
  }

  function startRotate() {
    state.mode = 'ROTATE';
    state.preview = { command: 'ROTATE', value: null };
  }

  function startScale() {
    state.mode = 'SCALE';
    state.preview = { command: 'SCALE', value: null };
  }

  function beginNumericEntry() {
    if (state.mode === 'EXTRUDE') state.mode = 'EXTRUDE_NUMERIC';
    else if (state.mode === 'ROTATE') state.mode = 'ROTATE_NUMERIC';
    else if (state.mode === 'SCALE') state.mode = 'SCALE_NUMERIC';
  }

  function typeNumericValue(value) {
    state.numericValue = value;
    if (state.preview) state.preview.value = value;
  }

  function confirm() {
    state.mode = 'IDLE';
    state.preview = null;
    state.numericValue = null;
  }

  function pressEscape() {
    if (state.mode === 'ROTATE' || state.mode === 'ROTATE_NUMERIC') {
      state.mode = 'IDLE';
      state.preview = null;
      state.numericValue = null;
      return;
    }
    if (state.mode === 'SCALE' || state.mode === 'SCALE_NUMERIC') {
      state.mode = 'IDLE';
      state.preview = null;
      state.numericValue = null;
      return;
    }
    if (state.mode === 'EXTRUDE') {
      state.mode = 'IDLE';
      state.preview = null;
      state.numericValue = null;
      return;
    }
    if (state.mode === 'EXTRUDE_NUMERIC') {
      state.mode = 'EXTRUDE';
      return;
    }
  }

  function getMode() {
    return state.mode;
  }

  function hasPreview() {
    return state.preview !== null;
  }

  function getPreviewValue() {
    return state.preview ? state.preview.value : null;
  }

  return {
    state,
    startExtrude,
    startRotate,
    startScale,
    beginNumericEntry,
    typeNumericValue,
    confirm,
    pressEscape,
    getMode,
    hasPreview,
    getPreviewValue,
  };
}

module.exports = { createViewport };
