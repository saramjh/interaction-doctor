// Tracks active touch contacts by platform-style identifier and position.
function createTouchBus() {
  const touches = new Map();
  return {
    touches,
    start(id, x, y) {
      touches.set(id, { id, x, y });
    },
    move(id, x, y) {
      const t = touches.get(id);
      if (t) {
        t.x = x;
        t.y = y;
      }
    },
    end(id) {
      touches.delete(id);
    },
  };
}

module.exports = { createTouchBus };
