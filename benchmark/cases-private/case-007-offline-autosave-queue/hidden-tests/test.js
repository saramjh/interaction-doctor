// Usage: node test.js <path-to-workspace>
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createApp;
try {
  ({ createApp } = require(path.join(workspace, 'app.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load app.js: ${e.message}` }));
  process.exit(1);
}

function queuedEditToDeletedNoteIsDropped() {
  const app = createApp();
  app.createNote('n1', 'draft');
  app.queueEdit('n1', 'edited while offline');
  app.deleteNote('n1');
  app.flushQueue();
  return app.state.notes.n1 === undefined;
}

function queuedEditToRecreatedNoteDoesNotOverwriteNewContent() {
  const app = createApp();
  app.createNote('n1', 'draft');
  app.queueEdit('n1', 'stale edit for the old note');
  app.deleteNote('n1');
  app.createNote('n1', 'brand new unrelated note'); // id reused
  app.flushQueue();
  return app.state.notes.n1 === 'brand new unrelated note';
}

function normalQueuedEditStillApplies() {
  const app = createApp();
  app.createNote('n1', 'draft');
  app.queueEdit('n1', 'edited');
  app.flushQueue();
  return app.state.notes.n1 === 'edited';
}

function unrelatedQueuedEditsSurviveASiblingDeletion() {
  // Guards against an over-broad "fix" that drops the ENTIRE queue (or
  // all commands for other, unrelated notes too) whenever any deletion
  // happens elsewhere. Deliberately checks only n2's outcome -- n1's
  // correctness is already covered by the target assertions above, and
  // this assertion is designed to hold on the ORIGINAL (buggy) fixture
  // too (which applies queued commands unconditionally and so does not
  // drop n2's edit either), so it registers as a true regression guard
  // rather than overlapping the bug itself.
  const app = createApp();
  app.createNote('n1', 'draft1');
  app.createNote('n2', 'draft2');
  app.queueEdit('n1', 'edit for n1');
  app.queueEdit('n2', 'edit for n2');
  app.deleteNote('n1');
  app.flushQueue();
  return app.state.notes.n2 === 'edit for n2';
}

const results = {
  queued_edit_to_deleted_note_is_dropped: queuedEditToDeletedNoteIsDropped(),
  queued_edit_to_recreated_note_does_not_overwrite_new_content: queuedEditToRecreatedNoteDoesNotOverwriteNewContent(),
  normal_queued_edit_still_applies: normalQueuedEditStillApplies(),
  unrelated_queued_edits_survive_a_sibling_deletion: unrelatedQueuedEditsSurviveASiblingDeletion(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
