// Usage: node test.js <path-to-workspace>
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createBoard, Scheduler;
try {
  ({ createBoard } = require(path.join(workspace, 'board.js')));
  ({ Scheduler } = require(path.join(workspace, 'scheduler.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load fixture: ${e.message}` }));
  process.exit(1);
}

function staleResponseDoesNotClobberNewerMove() {
  const scheduler = new Scheduler();
  const board = createBoard(scheduler);

  const idA = board.moveCard('card1', 'doing');
  const idB = board.moveCard('card1', 'done');

  // Response B (the newer move) arrives first; stale response A arrives
  // late and echoes its own (now-superseded) target.
  scheduler.resolve(idB, 'done');
  scheduler.resolve(idA, 'doing');

  return board.state.cardColumn.card1 === 'done';
}

function normalInOrderResolutionStillWorks() {
  const scheduler = new Scheduler();
  const board = createBoard(scheduler);
  const idA = board.moveCard('card1', 'doing');
  scheduler.resolve(idA, 'doing');
  return board.state.cardColumn.card1 === 'doing';
}

function serverRejectionIsHonoredWhenCurrent() {
  // Guards against a "fix" that just ignores every save response (which
  // would trivially avoid the stale-overwrite bug but silently drop
  // legitimate server state, e.g. a rejected/adjusted move).
  const scheduler = new Scheduler();
  const board = createBoard(scheduler);
  const idA = board.moveCard('card1', 'doing');
  // Server rejects the move and reports the card is still in 'todo'.
  // idA is still the current (only, unsuperseded) request for this card,
  // so this response must be applied.
  scheduler.resolve(idA, 'todo');
  return board.state.cardColumn.card1 === 'todo';
}

const results = {
  stale_response_does_not_clobber_newer_move: staleResponseDoesNotClobberNewerMove(),
  normal_in_order_resolution_still_works: normalInOrderResolutionStillWorks(),
  server_rejection_is_honored_when_current: serverRejectionIsHonoredWhenCurrent(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
