// Usage: node test.js <path-to-workspace>
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createDrawingSurface;
try {
  ({ createDrawingSurface } = require(path.join(workspace, 'app.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load app.js: ${e.message}` }));
  process.exit(1);
}

function misreadPalmThenCorrectedToPenBeforePromotionDrawsNormally() {
  const s = createDrawingSurface();
  s.pointerDown('PALM');
  s.classifierUpdate('PEN');
  s.pointerMove(5, 5);
  return s.state.promoted === 'draw' && s.state.strokePoints.length === 1;
}

function misreadPenThenCorrectedToPalmBeforePromotionRejectsNormally() {
  const s = createDrawingSurface();
  s.pointerDown('PEN');
  s.classifierUpdate('PALM');
  s.pointerMove(5, 5);
  return s.state.promoted === 'palm-reject' && s.state.strokePoints.length === 0;
}

function correctPenClassificationStillDrawsNormally() {
  const s = createDrawingSurface();
  s.pointerDown('PEN');
  s.pointerMove(1, 1);
  s.pointerMove(2, 2);
  return s.state.promoted === 'draw' && s.state.strokePoints.length === 2;
}

function correctPalmClassificationStillRejectedNormally() {
  const s = createDrawingSurface();
  s.pointerDown('PALM');
  s.pointerMove(1, 1);
  return s.state.promoted === 'palm-reject' && s.state.strokePoints.length === 0;
}

function oncePromotedLaterClassifierUpdatesDoNotFlipDecision() {
  // Guards against an over-broad "fix" that keeps re-evaluating the
  // classification forever instead of only fixing the pre-promotion
  // window.
  const s = createDrawingSurface();
  s.pointerDown('PEN');
  s.pointerMove(1, 1);
  s.classifierUpdate('PALM'); // arrives AFTER promotion
  s.pointerMove(2, 2);
  return s.state.promoted === 'draw' && s.state.strokePoints.length === 2;
}

const results = {
  misread_palm_then_corrected_to_pen_before_promotion_draws_normally: misreadPalmThenCorrectedToPenBeforePromotionDrawsNormally(),
  misread_pen_then_corrected_to_palm_before_promotion_rejects_normally: misreadPenThenCorrectedToPalmBeforePromotionRejectsNormally(),
  correct_pen_classification_still_draws_normally: correctPenClassificationStillDrawsNormally(),
  correct_palm_classification_still_rejected_normally: correctPalmClassificationStillRejectedNormally(),
  once_promoted_later_classifier_updates_do_not_flip_decision: oncePromotedLaterClassifierUpdatesDoNotFlipDecision(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
