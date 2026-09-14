// Usage: node test.js <path-to-workspace>
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createComposer;
try {
  ({ createComposer } = require(path.join(workspace, 'composer.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load composer.js: ${e.message}` }));
  process.exit(1);
}

function enterDuringCompositionConfirmsNotSends() {
  const c = createComposer();
  c.compositionstart();
  c.compositionupdate('の');
  c.keydownEnter(); // Enter arrives mid-composition -- IME's Enter, not app's.
  c.compositionend('の'); // IME confirms the composed text afterward.
  return c.state.sentMessages.length === 0 && c.state.draft === 'の';
}

function idleEnterSendsNormally() {
  const c = createComposer();
  c.type('h');
  c.type('i');
  c.keydownEnter();
  return (
    c.state.sentMessages.length === 1 &&
    c.state.sentMessages[0] === 'hi' &&
    c.state.draft === ''
  );
}

const results = {
  enter_during_composition_confirms_not_sends: enterDuringCompositionConfirmsNotSends(),
  idle_enter_sends_normally: idleEnterSendsNormally(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
