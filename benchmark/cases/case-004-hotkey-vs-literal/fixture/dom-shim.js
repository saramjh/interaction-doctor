// Minimal fake element tree with bubbling dispatch, used so this fixture's
// interaction logic can be exercised deterministically under plain Node
// (no browser/DOM dependency needed for the pilot benchmark).
class FakeElement {
  constructor(name, parent = null) {
    this.name = name;
    this.parent = parent;
    this.listeners = {};
    if (parent) parent.children = (parent.children || []).concat(this);
  }

  addEventListener(type, fn) {
    this.listeners[type] = this.listeners[type] || [];
    this.listeners[type].push(fn);
  }

  dispatch(type, payload = {}) {
    const evt = Object.assign({ type, target: this, propagationStopped: false }, payload);
    evt.stopPropagation = () => {
      evt.propagationStopped = true;
    };
    let node = this;
    while (node) {
      for (const fn of node.listeners[type] || []) fn(evt);
      if (evt.propagationStopped) break;
      node = node.parent;
    }
    return evt;
  }
}

module.exports = { FakeElement };
