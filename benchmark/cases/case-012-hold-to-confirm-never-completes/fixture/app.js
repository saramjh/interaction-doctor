// Hold-to-confirm button. pointerdown() starts a hold; tick() is called
// periodically (standing in for a timer/animation-frame check in a real
// app) to check whether the hold has reached holdDurationMs; pointerup()
// releases the hold early.
function createHoldButton(clock, holdDurationMs = 600) {
  const state = { holding: false, holdStartTime: null, confirmedCount: 0 };
  const referenceTime = clock.now();

  function pointerdown() {
    state.holding = true;
    state.holdStartTime = clock.now();
  }

  function tick() {
    if (!state.holding) return;
    const elapsed = referenceTime - state.holdStartTime;
    if (elapsed >= holdDurationMs) {
      state.confirmedCount += 1;
      state.holding = false;
    }
  }

  function pointerup() {
    state.holding = false;
  }

  return { state, pointerdown, tick, pointerup };
}

module.exports = { createHoldButton };
