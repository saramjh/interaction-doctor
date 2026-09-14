// Bottom sheet with native interactive drag-to-dismiss, containing a
// horizontal photo carousel. dragStart(region) records where the drag
// began ('carousel' or 'sheet'); dragMove accumulates the drag's
// horizontal/vertical components; dragEnd applies whichever effects
// crossed their threshold.
const DISMISS_THRESHOLD = 100;
const CAROUSEL_PAGE_THRESHOLD = 50;

function createSheetWithCarousel() {
  const state = {
    sheetOffset: 0,
    sheetDismissed: false,
    carouselIndex: 0,
    carouselOffset: 0,
    dragging: false,
    dragOriginRegion: null,
  };

  function dragStart(region) {
    state.dragging = true;
    state.dragOriginRegion = region;
    state.sheetOffset = 0;
    state.carouselOffset = 0;
  }

  function dragMove(dx, dy) {
    if (!state.dragging) return;
    state.sheetOffset += dy;
    if (state.dragOriginRegion === 'carousel') {
      state.carouselOffset += dx;
    }
  }

  function dragEnd() {
    if (!state.dragging) return;
    if (state.sheetOffset > DISMISS_THRESHOLD) {
      state.sheetDismissed = true;
    }
    if (state.dragOriginRegion === 'carousel' && Math.abs(state.carouselOffset) > CAROUSEL_PAGE_THRESHOLD) {
      state.carouselIndex += state.carouselOffset < 0 ? 1 : -1;
    }
    state.dragging = false;
    state.dragOriginRegion = null;
  }

  return { state, dragStart, dragMove, dragEnd };
}

module.exports = { createSheetWithCarousel };
