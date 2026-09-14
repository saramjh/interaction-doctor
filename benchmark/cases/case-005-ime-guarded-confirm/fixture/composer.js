// Chat message composer: pressing Enter sends the message, EXCEPT while
// the user is mid-composition with an IME (e.g. typing Japanese/Chinese/
// Korean via a candidate window) -- during composition, Enter's job is to
// confirm the composed text, not to submit the message. `compositionstart`
// / `compositionupdate` / `compositionend` are dispatched by the platform
// IME exactly as they are in a real browser; `isComposing` reflects the
// current composition state at the moment any given keydown is handled.
function createComposer() {
  const state = { isComposing: false, draft: '', sentMessages: [] };

  function compositionstart() {
    state.isComposing = true;
  }

  function compositionupdate(text) {
    state.draft = text;
  }

  function compositionend(text) {
    state.draft = text;
    state.isComposing = false;
  }

  function type(char) {
    state.draft += char;
  }

  function keydownEnter() {
    if (state.isComposing) {
      // IME owns this Enter -- it confirms the current composition, it
      // does not submit the message.
      return;
    }
    state.sentMessages.push(state.draft);
    state.draft = '';
  }

  return { state, compositionstart, compositionupdate, compositionend, type, keydownEnter };
}

module.exports = { createComposer };
