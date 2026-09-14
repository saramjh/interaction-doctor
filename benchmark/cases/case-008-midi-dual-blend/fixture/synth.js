// A synth filter-cutoff parameter continuously driven by TWO simultaneous
// analog MIDI controllers: the mod wheel and a breath controller. Both are
// always "live" -- there is no discrete mode switch between them, and
// neither one is ever exclusively "in control." The current value is a
// deterministic weighted blend of both controllers' latest readings,
// using a fixed, already-tuned mix ratio. Both controllers may be updated
// in any order, at any time, independently of one another.
function createSynth(mixRatio = 0.5) {
  const state = { modWheel: 0, breath: 0, filterCutoff: 0 };

  function recompute() {
    state.filterCutoff = state.modWheel * mixRatio + state.breath * (1 - mixRatio);
  }

  function setModWheel(value) {
    state.modWheel = value;
    recompute();
  }

  function setBreath(value) {
    state.breath = value;
    recompute();
  }

  return { state, setModWheel, setBreath };
}

module.exports = { createSynth };
