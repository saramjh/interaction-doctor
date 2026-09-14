// On-screen fader controllable by local UI or by a connected MIDI device.
function createFaderApp(midiBus) {
  const state = { value: 50, externalDeviceId: null };

  function midiControl(deviceId, value) {
    state.externalDeviceId = deviceId;
    state.value = value;
  }

  function midiControlEnd(deviceId) {
    if (state.externalDeviceId === deviceId) {
      state.externalDeviceId = null;
    }
  }

  function localSet(value) {
    if (state.externalDeviceId) return;
    state.value = value;
  }

  midiBus.onDisconnect((deviceId) => {});

  return { state, midiControl, midiControlEnd, localSet };
}

module.exports = { createFaderApp };
