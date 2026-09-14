// Row list with a per-row delete-confirm dialog. `state.focusedElementId`
// stands in for document.activeElement (tracked by element id, since
// there's no real DOM in this fixture). Opening the dialog moves focus to
// a control inside it; cancelling returns focus to the row's trigger.
function createApp() {
  const state = {
    rows: [
      { id: 'row-1', label: 'Item 1' },
      { id: 'row-2', label: 'Item 2' },
      { id: 'row-3', label: 'Item 3' },
    ],
    modalOpenForRowId: null,
    focusedElementId: 'row-1-trigger',
  };

  function focusTrigger(rowId) {
    state.focusedElementId = `${rowId}-trigger`;
  }

  function openDeleteModal(rowId) {
    state.modalOpenForRowId = rowId;
    state.focusedElementId = 'delete-modal-confirm-button';
  }

  function cancelDeleteModal() {
    const rowId = state.modalOpenForRowId;
    state.modalOpenForRowId = null;
    state.focusedElementId = `${rowId}-trigger`;
  }

  function confirmDelete() {
    const rowId = state.modalOpenForRowId;
    state.rows = state.rows.filter((r) => r.id !== rowId);
    state.modalOpenForRowId = null;
    state.focusedElementId = null;
  }

  return { state, focusTrigger, openDeleteModal, cancelDeleteModal, confirmDelete };
}

module.exports = { createApp };
