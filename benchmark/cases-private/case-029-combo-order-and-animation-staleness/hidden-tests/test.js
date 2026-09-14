// Usage: node test.js <path-to-workspace>
//
// This case intentionally contains TWO independently gradable defects:
//
//   PART A (ordered N-ary, policy=ordered): the special move's three
//   directional participants (InputClaimD1/D2/D3) must trigger only for
//   strict D1 -> D2 -> D3 order within the timing window -- not merely
//   because all three directions occurred somewhere in the window. The
//   named mechanism is the app-level input-sequence buffer; it is never
//   itself a participant.
//
//   PART B (effect-lifetime staleness): the combo attack must commit to
//   the target selected at TRIGGER time, not whichever target happens to
//   be selected when the delayed hit-impact/completion effect executes.
//
// Every Part A assertion below uses only pressDirection()/setCurrentTarget/
// getTriggerCount() and never calls completeAttackAnimation() -- so Part
// A's pass/fail is completely unaffected by Part B's defect. Every Part B
// assertion always drives a VALID (correctly-ordered) D1->D2->D3 sequence
// to reach a triggered attack -- a valid ordered sequence triggers under
// BOTH the buggy and the fixed Part A logic, so Part B's assertions never
// depend on Part A having been fixed. Each assertion also uses a fresh
// createComboGame() instance, so no assertion's outcome depends on another
// assertion having run first.
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createComboGame;
try {
  ({ createComboGame } = require(path.join(workspace, 'app.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load app.js: ${e.message}` }));
  process.exit(1);
}

function press(game, seq) {
  seq.forEach((d) => game.pressDirection(d));
}

// --- Part A: ordering -------------------------------------------------

function permutationTriggerCount(seq) {
  const game = createComboGame();
  game.setCurrentTarget('T1');
  press(game, seq);
  return game.getTriggerCount();
}

function validComboOrderTriggers() {
  return permutationTriggerCount(['D1', 'D2', 'D3']) === 1;
}

function permutationD1D3D2Rejected() {
  return permutationTriggerCount(['D1', 'D3', 'D2']) === 0;
}

function permutationD2D1D3Rejected() {
  return permutationTriggerCount(['D2', 'D1', 'D3']) === 0;
}

function permutationD2D3D1Rejected() {
  return permutationTriggerCount(['D2', 'D3', 'D1']) === 0;
}

function permutationD3D1D2Rejected() {
  return permutationTriggerCount(['D3', 'D1', 'D2']) === 0;
}

function permutationD3D2D1Rejected() {
  return permutationTriggerCount(['D3', 'D2', 'D1']) === 0;
}

function incompleteSingleInputDoesNotTrigger() {
  return permutationTriggerCount(['D1']) === 0;
}

function incompleteTwoInputsDoNotTrigger() {
  return permutationTriggerCount(['D1', 'D2']) === 0;
}

function timingWindowEnforcedOutsideWindowDoesNotTrigger() {
  const game = createComboGame();
  game.setCurrentTarget('T1');
  game.pressDirection('D1');
  game.advanceTime(2000); // well beyond the timing window
  game.pressDirection('D2');
  game.pressDirection('D3');
  return game.getTriggerCount() === 0;
}

function freshComboAfterResetCanTrigger() {
  const game = createComboGame();
  game.setCurrentTarget('T1');
  press(game, ['D1', 'D2', 'D3']);
  const first = game.getTriggerCount();
  press(game, ['D1', 'D2', 'D3']);
  const second = game.getTriggerCount();
  return first === 1 && second === 2;
}

// --- Part B: attack target binding across the delayed completion ------

function attackCompletionHitsTriggerTimeTarget() {
  const game = createComboGame();
  game.setCurrentTarget('T1');
  press(game, ['D1', 'D2', 'D3']);
  game.setCurrentTarget('T2'); // lock-on changes before the hit lands
  game.completeAttackAnimation();
  return game.getEntityHealth('T1') === 90 && game.getEntityHealth('T2') === 100;
}

function multiSwitchBeforeCompletionStillHitsTriggerTimeTarget() {
  const game = createComboGame();
  game.setCurrentTarget('T1');
  press(game, ['D1', 'D2', 'D3']);
  game.setCurrentTarget('T2');
  game.setCurrentTarget('T3'); // switches through more than one target
  game.completeAttackAnimation();
  return (
    game.getEntityHealth('T1') === 90 &&
    game.getEntityHealth('T2') === 100 &&
    game.getEntityHealth('T3') === 100
  );
}

function noSwitchAppliesNormalDamageToSelectedTarget() {
  const game = createComboGame();
  game.setCurrentTarget('T1');
  press(game, ['D1', 'D2', 'D3']);
  game.completeAttackAnimation();
  return game.getEntityHealth('T1') === 90 && game.getEntityHealth('T2') === 100;
}

function freshComboAfterSwitchUsesNewTarget() {
  // Prevents a repair from permanently binding all future attacks to the
  // first target ever used: a SECOND, freshly-triggered combo, triggered
  // and completed while the target is T2 throughout (no switch during
  // its own flight), must land on T2.
  const game = createComboGame();
  game.setCurrentTarget('T1');
  press(game, ['D1', 'D2', 'D3']);
  game.setCurrentTarget('T2');
  game.completeAttackAnimation(); // first attack resolves (not under test here)
  const t2AfterFirst = game.getEntityHealth('T2');
  press(game, ['D1', 'D2', 'D3']); // fresh combo, target T2 the whole time
  game.completeAttackAnimation();
  const t2AfterSecond = game.getEntityHealth('T2');
  return t2AfterSecond === t2AfterFirst - 10;
}

function damageNotAppliedBeforeCompletion() {
  // The public contract states damage lands at completion, not at
  // trigger time -- a repair that sidesteps the staleness problem by
  // applying damage immediately at trigger time must still fail here,
  // even though it can accidentally satisfy the target-binding checks.
  const game = createComboGame();
  game.setCurrentTarget('T1');
  press(game, ['D1', 'D2', 'D3']);
  const beforeCompletion = game.getEntityHealth('T1');
  game.completeAttackAnimation();
  const afterCompletion = game.getEntityHealth('T1');
  return beforeCompletion === 100 && afterCompletion === 90;
}

function attackCompletionExecutesOnce() {
  const game = createComboGame();
  game.setCurrentTarget('T1');
  press(game, ['D1', 'D2', 'D3']);
  game.completeAttackAnimation();
  const afterFirst = game.getEntityHealth('T1');
  game.completeAttackAnimation(); // no pending attack anymore: must be a no-op
  const afterSecond = game.getEntityHealth('T1');
  return afterFirst === 90 && afterSecond === 90;
}

function fullTriggerCompleteCycleIsRepeatable() {
  const game = createComboGame();
  game.setCurrentTarget('T1');
  press(game, ['D1', 'D2', 'D3']);
  game.completeAttackAnimation();
  const afterFirst = game.getEntityHealth('T1');
  press(game, ['D1', 'D2', 'D3']);
  game.completeAttackAnimation();
  const afterSecond = game.getEntityHealth('T1');
  return afterFirst === 90 && afterSecond === 80;
}

const results = {
  permutation_d1_d3_d2_rejected: permutationD1D3D2Rejected(),
  permutation_d2_d1_d3_rejected: permutationD2D1D3Rejected(),
  permutation_d2_d3_d1_rejected: permutationD2D3D1Rejected(),
  permutation_d3_d1_d2_rejected: permutationD3D1D2Rejected(),
  permutation_d3_d2_d1_rejected: permutationD3D2D1Rejected(),
  attack_completion_hits_trigger_time_target: attackCompletionHitsTriggerTimeTarget(),
  multi_switch_before_completion_still_hits_trigger_time_target: multiSwitchBeforeCompletionStillHitsTriggerTimeTarget(),

  valid_combo_order_triggers: validComboOrderTriggers(),
  incomplete_single_input_does_not_trigger: incompleteSingleInputDoesNotTrigger(),
  incomplete_two_inputs_do_not_trigger: incompleteTwoInputsDoNotTrigger(),
  timing_window_enforced_outside_window_does_not_trigger: timingWindowEnforcedOutsideWindowDoesNotTrigger(),
  fresh_combo_after_reset_can_trigger: freshComboAfterResetCanTrigger(),
  no_switch_applies_normal_damage_to_selected_target: noSwitchAppliesNormalDamageToSelectedTarget(),
  fresh_combo_after_switch_uses_new_target: freshComboAfterSwitchUsesNewTarget(),
  damage_not_applied_before_completion: damageNotAppliedBeforeCompletion(),
  attack_completion_executes_once: attackCompletionExecutesOnce(),
  full_trigger_complete_cycle_is_repeatable: fullTriggerCompleteCycleIsRepeatable(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
