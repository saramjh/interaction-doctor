// Usage: node test.js <path-to-workspace>
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createSynth;
try {
  ({ createSynth } = require(path.join(workspace, 'synth.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load synth.js: ${e.message}` }));
  process.exit(1);
}

function expectedCutoff(mod, breath, mixRatio) {
  return mod * mixRatio + breath * (1 - mixRatio);
}

function concurrentUpdatesBlendDeterministicallyRegardlessOfOrder() {
  const a = createSynth(0.5);
  a.setModWheel(80);
  a.setBreath(20);

  const b = createSynth(0.5);
  b.setBreath(20);
  b.setModWheel(80);

  return a.state.filterCutoff === 50 && b.state.filterCutoff === 50 && a.state.filterCutoff === b.state.filterCutoff;
}

function bothControllersRemainIndependentlyLive() {
  // Guards against an over-broad "fix" that makes one controller lock out
  // the other (e.g. only the most-recently-touched controller counts).
  const s = createSynth(0.5);
  s.setModWheel(80);
  s.setBreath(20); // cutoff = 50
  s.setBreath(60); // mod wheel's prior value (80) must still contribute
  return s.state.filterCutoff === 80 * 0.5 + 60 * 0.5;
}

// Exhaustive-ish MIDI-range grid check: rejects any arbitration, priority,
// exclusivity, or threshold rule (whatever its cutover point might be)
// by covering the full 0..127 MIDI value space for BOTH controllers, at
// two different mix ratios, in both update orders, and comparing every
// point against the plain deterministic formula. A rule like "mod wheel
// overrides breath above some threshold" necessarily diverges from the
// formula at every grid point past that threshold, in at least one of
// the two orderings -- there is no threshold value small enough to hide
// from a full 0..127 sweep.
function blendMatchesDeterministicFormulaAcrossFullGrid() {
  const mixRatios = [0.5, 0.3];
  const step = 1; // 128 * 128 = 16384 points per ratio; trivial runtime cost

  for (const mixRatio of mixRatios) {
    for (let mod = 0; mod <= 127; mod += step) {
      for (let breath = 0; breath <= 127; breath += step) {
        const expected = expectedCutoff(mod, breath, mixRatio);

        const orderModFirst = createSynth(mixRatio);
        orderModFirst.setModWheel(mod);
        orderModFirst.setBreath(breath);
        if (orderModFirst.state.filterCutoff !== expected) return false;

        const orderBreathFirst = createSynth(mixRatio);
        orderBreathFirst.setBreath(breath);
        orderBreathFirst.setModWheel(mod);
        if (orderBreathFirst.state.filterCutoff !== expected) return false;
      }
    }
  }
  return true;
}

const results = {
  concurrent_updates_blend_deterministically_regardless_of_order: concurrentUpdatesBlendDeterministicallyRegardlessOfOrder(),
  both_controllers_remain_independently_live: bothControllersRemainIndependentlyLive(),
  blend_matches_deterministic_formula_across_full_grid: blendMatchesDeterministicFormulaAcrossFullGrid(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
