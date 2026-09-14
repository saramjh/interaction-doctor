// Usage: node test.js <path-to-workspace>
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createViewport;
try {
  ({ createViewport } = require(path.join(workspace, 'app.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load app.js: ${e.message}` }));
  process.exit(1);
}

// --- targets: the nested numeric path specifically ------------------------

function extrudeNumericEscapeReturnsToIdle() {
  const v = createViewport();
  v.startExtrude();
  v.beginNumericEntry();
  v.typeNumericValue(5);
  v.pressEscape();
  return v.getMode() === 'IDLE';
}

function extrudeNumericEscapeClearsPreview() {
  const v = createViewport();
  v.startExtrude();
  v.beginNumericEntry();
  v.typeNumericValue(5);
  v.pressEscape();
  return v.hasPreview() === false;
}

// --- sibling/plain-command regression guards -------------------------------

function extrudePlainEscapeReturnsToIdleAndClearsPreview() {
  const v = createViewport();
  v.startExtrude();
  v.pressEscape();
  return v.getMode() === 'IDLE' && v.hasPreview() === false;
}

function rotateNumericEscapeFollowsConvention() {
  const v = createViewport();
  v.startRotate();
  v.beginNumericEntry();
  v.typeNumericValue(30);
  v.pressEscape();
  return v.getMode() === 'IDLE' && v.hasPreview() === false;
}

function scaleNumericEscapeFollowsConvention() {
  const v = createViewport();
  v.startScale();
  v.beginNumericEntry();
  v.typeNumericValue(2);
  v.pressEscape();
  return v.getMode() === 'IDLE' && v.hasPreview() === false;
}

function extrudeConfirmStillWorks() {
  const v = createViewport();
  v.startExtrude();
  v.beginNumericEntry();
  v.typeNumericValue(5);
  v.confirm();
  return v.getMode() === 'IDLE' && v.hasPreview() === false;
}

function freshExtrudeAfterCancellationWorks() {
  const v = createViewport();
  v.startExtrude();
  v.beginNumericEntry();
  v.typeNumericValue(5);
  v.pressEscape();
  v.startExtrude();
  return v.getMode() === 'EXTRUDE' && v.getPreviewValue() === null;
}

function numericEntryUpdatesPreviewNormallyBeforeCancellation() {
  const v = createViewport();
  v.startExtrude();
  v.beginNumericEntry();
  v.typeNumericValue(9);
  return v.getPreviewValue() === 9;
}

function numericEntryActuallyChangesMode() {
  const v = createViewport();
  v.startExtrude();
  v.beginNumericEntry();
  return v.getMode() === 'EXTRUDE_NUMERIC';
}

function escapeWhileIdleIsHarmless() {
  const v = createViewport();
  v.pressEscape();
  return v.getMode() === 'IDLE' && v.hasPreview() === false;
}

const results = {
  extrude_numeric_escape_returns_to_idle: extrudeNumericEscapeReturnsToIdle(),
  extrude_numeric_escape_clears_preview: extrudeNumericEscapeClearsPreview(),
  extrude_plain_escape_returns_to_idle_and_clears_preview: extrudePlainEscapeReturnsToIdleAndClearsPreview(),
  rotate_numeric_escape_follows_convention: rotateNumericEscapeFollowsConvention(),
  scale_numeric_escape_follows_convention: scaleNumericEscapeFollowsConvention(),
  extrude_confirm_still_works: extrudeConfirmStillWorks(),
  fresh_extrude_after_cancellation_works: freshExtrudeAfterCancellationWorks(),
  numeric_entry_updates_preview_normally_before_cancellation: numericEntryUpdatesPreviewNormallyBeforeCancellation(),
  numeric_entry_actually_changes_mode: numericEntryActuallyChangesMode(),
  escape_while_idle_is_harmless: escapeWhileIdleIsHarmless(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
