// Media library: a track card has a scrub bar (drag left/right to seek) and
// the whole card sits inside a horizontally-swipeable carousel of tracks
// (drag left/right to move between tracks).
const { FakeElement } = require('./dom-shim');

function createPlayer() {
  const carousel = new FakeElement('carousel');
  const scrubber = new FakeElement('scrubber', carousel);

  const state = { scrubberValue: 0, carouselOffset: 0, scrubbing: false, carouselDragging: false };

  scrubber.addEventListener('pointerdown', () => {
    state.scrubbing = true;
  });
  scrubber.addEventListener('pointermove', (e) => {
    if (state.scrubbing) state.scrubberValue += e.dx;
  });
  scrubber.addEventListener('pointerup', () => {
    state.scrubbing = false;
  });

  carousel.addEventListener('pointerdown', () => {
    state.carouselDragging = true;
  });
  carousel.addEventListener('pointermove', (e) => {
    if (state.carouselDragging) state.carouselOffset += e.dx;
  });
  carousel.addEventListener('pointerup', () => {
    state.carouselDragging = false;
  });

  return { carousel, scrubber, state };
}

module.exports = { createPlayer };
