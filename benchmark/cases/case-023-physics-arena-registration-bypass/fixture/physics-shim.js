// Minimal physics-solver shim. registerGrab() records a grab registration
// for the current frame; clearFrameRegistrations() clears them at the
// start of a frame; getFrameRegistrations() returns whatever was
// registered. The solver only records what it is given.
function createPhysicsSolver() {
  let frameRegistrations = [];
  return {
    registerGrab(pointerId, data) {
      frameRegistrations.push({ pointerId, data });
    },
    clearFrameRegistrations() {
      frameRegistrations = [];
    },
    getFrameRegistrations() {
      return frameRegistrations.slice();
    },
  };
}

module.exports = { createPhysicsSolver };
