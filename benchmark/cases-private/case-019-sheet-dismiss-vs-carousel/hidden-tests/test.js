// Usage: node test.js <path-to-workspace>
//
// case-019 is intent-ambiguous (no target_assertions). The dispute is
// which product policy governs a carousel-origin drag whose movement
// crosses both the carousel-page threshold and the sheet-dismiss
// threshold. Policy A (carousel fully suppresses dismissal), policy B
// (directional-threshold arbitration, at any threshold/ratio), "sheet
// always wins", or any other unilateral resolution are all genuinely
// plausible; nothing in this fixture selects one.
//
// A single sampled drag vector is not a reliable unresolved-behavior
// signature: an arbitration policy can be tuned so one specific ratio of
// dx/dy happens to fall inside its "allow both" band while other ratios
// are suppressed -- that is still an unconfirmed product-policy choice,
// just one a single-sample diagnostic would miss. The matrix below
// samples FIVE carousel-origin drag vectors spanning materially
// different dx:dy ratios (all of which cross both thresholds on the
// unmodified fixture), and records the RAW observed outcome
// (sheetDismissed, carouselIndex) for each -- never a correctness
// judgment, never which combination "should" hold. Any unilateral
// resolution that changes the outcome for ANY one of the five vectors is
// exactly what unresolved_behavior_changed is meant to catch, even if it
// happens to leave one particular vector (e.g. the original -80/150
// sample) untouched.
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createSheetWithCarousel;
try {
  ({ createSheetWithCarousel } = require(path.join(workspace, 'app.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load app.js: ${e.message}` }));
  process.exit(1);
}

function verticalDragOutsideCarouselStillDismissesSheet() {
  // Not part of the dispute: a drag that never touches the carousel at
  // all must still be able to dismiss the sheet.
  const app = createSheetWithCarousel();
  app.dragStart('sheet');
  app.dragMove(0, 150);
  app.dragEnd();
  return app.state.sheetDismissed === true;
}

function pureHorizontalCarouselDragStillNavigates() {
  // Also not part of the dispute: a carousel drag with no vertical
  // component at all can never reach the dismiss threshold under any
  // resolution, so paging must still work.
  const app = createSheetWithCarousel();
  app.dragStart('carousel');
  app.dragMove(-80, 0);
  app.dragEnd();
  return app.state.carouselIndex === 1 && app.state.sheetDismissed === false;
}

function carouselOriginOutcome(dx, dy) {
  const app = createSheetWithCarousel();
  app.dragStart('carousel');
  app.dragMove(dx, dy);
  app.dragEnd();
  return { sheetDismissed: app.state.sheetDismissed, carouselIndex: app.state.carouselIndex };
}

const results = {
  vertical_drag_outside_carousel_still_dismisses_sheet: verticalDragOutsideCarouselStillDismissesSheet(),
  pure_horizontal_carousel_drag_still_navigates: pureHorizontalCarouselDragStillNavigates(),
};

// Five carousel-origin vectors, spanning materially different dx:dy
// ratios, all crossing both thresholds (|dx| > 50, dy > 100) on the
// unmodified fixture -- see module comment above.
const diagnostic = {
  outcome_dx_neg80_dy150: carouselOriginOutcome(-80, 150), // original sample, ratio ~0.53
  outcome_dx_neg150_dy110: carouselOriginOutcome(-150, 110), // strong horizontal, ratio ~1.36
  outcome_dx_neg60_dy200: carouselOriginOutcome(-60, 200), // vertical-dominant, ratio 0.30
  outcome_dx_neg100_dy120: carouselOriginOutcome(-100, 120), // diagonal, ratio ~0.83
  outcome_dx_neg130_dy130: carouselOriginOutcome(-130, 130), // boundary-sensitive equal diagonal, ratio 1.00
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results, diagnostic }, null, 2));
process.exit(pass ? 0 : 1);
