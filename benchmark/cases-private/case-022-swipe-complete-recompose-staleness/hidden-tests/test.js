// Usage: node test.js <path-to-workspace>
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createTodoList;
try {
  ({ createTodoList } = require(path.join(workspace, 'app.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load app.js: ${e.message}` }));
  process.exit(1);
}

function completedById(list, id) {
  return list.state.items.find((i) => i.id === id).completed;
}

function originallySwipedItemCompletesNotWhateverIsNowAtThatPosition() {
  const list = createTodoList(['A', 'B', 'C']);
  list.swipeStart('B'); // B is at position 1
  list.resort(['C', 'A', 'B']); // position 1 is now A
  list.swipeComplete();
  return completedById(list, 'B') === true && completedById(list, 'A') === false;
}

function reorderTwiceDuringOneSwipeStillCompletesOriginalItem() {
  const list = createTodoList(['A', 'B', 'C']);
  list.swipeStart('C'); // C is at position 2
  list.resort(['C', 'A', 'B']); // C now at position 0
  list.resort(['B', 'C', 'A']); // C now at position 1
  list.swipeComplete();
  return completedById(list, 'C') === true && completedById(list, 'A') === false && completedById(list, 'B') === false;
}

function targetMovingToFrontStillCompletesCorrectly() {
  const list = createTodoList(['A', 'B', 'C']);
  list.swipeStart('C'); // C starts at the back (position 2)
  list.resort(['C', 'A', 'B']); // C moves to the front (position 0)
  list.swipeComplete();
  return completedById(list, 'C') === true && completedById(list, 'A') === false && completedById(list, 'B') === false;
}

function targetMovingToBackStillCompletesCorrectly() {
  const list = createTodoList(['A', 'B', 'C']);
  list.swipeStart('A'); // A starts at the front (position 0)
  list.resort(['B', 'C', 'A']); // A moves to the back (position 2)
  list.swipeComplete();
  return completedById(list, 'A') === true && completedById(list, 'B') === false && completedById(list, 'C') === false;
}

function reorderStillAppliesWhileSwipePending() {
  // A repair must not sidestep the bug by freezing/rejecting list changes
  // while a completion is pending -- the list must still actually
  // reorder; only which item ends up completed is what needs fixing.
  const list = createTodoList(['A', 'B', 'C']);
  list.swipeStart('B');
  list.resort(['C', 'A', 'B']);
  return list.state.items.map((i) => i.id).join(',') === 'C,A,B';
}

function swipeCompleteWithoutResortStillWorks() {
  const list = createTodoList(['A', 'B', 'C']);
  list.swipeStart('B');
  list.swipeComplete();
  return completedById(list, 'B') === true && completedById(list, 'A') === false && completedById(list, 'C') === false;
}

function resortWithoutActiveSwipeDoesNotCompleteAnything() {
  const list = createTodoList(['A', 'B', 'C']);
  list.resort(['C', 'A', 'B']);
  return list.state.items.every((i) => i.completed === false);
}

function swipingADifferentItemAfterACompletedOneStillWorks() {
  const list = createTodoList(['A', 'B', 'C']);
  list.swipeStart('B');
  list.swipeComplete();
  list.swipeStart('C');
  list.swipeComplete();
  return completedById(list, 'B') === true && completedById(list, 'C') === true && completedById(list, 'A') === false;
}

const results = {
  originally_swiped_item_completes_not_whatever_is_now_at_that_position: originallySwipedItemCompletesNotWhateverIsNowAtThatPosition(),
  reorder_twice_during_one_swipe_still_completes_original_item: reorderTwiceDuringOneSwipeStillCompletesOriginalItem(),
  target_moving_to_front_still_completes_correctly: targetMovingToFrontStillCompletesCorrectly(),
  target_moving_to_back_still_completes_correctly: targetMovingToBackStillCompletesCorrectly(),
  reorder_still_applies_while_swipe_pending: reorderStillAppliesWhileSwipePending(),
  swipe_complete_without_resort_still_works: swipeCompleteWithoutResortStillWorks(),
  resort_without_active_swipe_does_not_complete_anything: resortWithoutActiveSwipeDoesNotCompleteAnything(),
  swiping_a_different_item_after_a_completed_one_still_works: swipingADifferentItemAfterACompletedOneStillWorks(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
