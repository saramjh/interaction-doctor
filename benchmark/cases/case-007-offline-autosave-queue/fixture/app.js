// Offline-first notes app: edits are queued (e.g. while offline, or
// batched for a debounced autosave) and applied later via flushQueue().
function createApp() {
  const state = { notes: {}, noteGeneration: {}, queue: [] };

  function createNote(id, text) {
    state.notes[id] = text;
    state.noteGeneration[id] = (state.noteGeneration[id] || 0) + 1;
  }

  function deleteNote(id) {
    delete state.notes[id];
  }

  function queueEdit(id, text) {
    state.queue.push({ id, text, generation: state.noteGeneration[id] });
  }

  function flushQueue() {
    for (const cmd of state.queue) {
      state.notes[cmd.id] = cmd.text;
    }
    state.queue = [];
  }

  return { state, createNote, deleteNote, queueEdit, flushQueue };
}

module.exports = { createApp };
