// Deterministic stand-in for a network round trip. Each call to schedule()
// represents an in-flight save request; resolve(id, payload) delivers
// that request's server response whenever the test chooses to, with
// whatever payload the server actually sent (real networks don't
// guarantee response order matches send order, and a server can also
// reject/adjust a request rather than just echoing it back).
class Scheduler {
  constructor() {
    this.queue = new Map();
    this.nextId = 1;
  }

  schedule(fn) {
    const id = this.nextId++;
    this.queue.set(id, fn);
    return id;
  }

  cancel(id) {
    this.queue.delete(id);
  }

  resolve(id, payload) {
    const fn = this.queue.get(id);
    this.queue.delete(id);
    if (fn) fn(payload);
  }
}

module.exports = { Scheduler };
