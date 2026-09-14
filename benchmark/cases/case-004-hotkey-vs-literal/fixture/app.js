// Document-level "?" shortcut opens a help overlay. A search input sits
// inside the document and accepts free text, including a literal "?"
// character. Typing while the search input is focused dispatches keydown
// on the input, which bubbles up to the document exactly as a real
// browser keydown would.
const { FakeElement } = require('./dom-shim');

function createApp() {
  const documentEl = new FakeElement('document');
  const searchInput = new FakeElement('search-input', documentEl);

  const state = { helpOpen: false, searchValue: '' };

  documentEl.addEventListener('keydown', (e) => {
    if (e.key === '?') {
      state.helpOpen = !state.helpOpen;
    }
  });

  searchInput.addEventListener('keydown', (e) => {
    state.searchValue += e.key;
  });

  return { state, documentEl, searchInput };
}

module.exports = { createApp };
