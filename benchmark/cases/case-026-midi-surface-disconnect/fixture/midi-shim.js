// Small model of MIDI hardware connection state. connect/disconnect
// report a device's connection; onDisconnect(fn) registers a listener
// notified with the disconnected device's id.
function createMidiBus() {
  const connectedDevices = new Set();
  let listeners = [];
  return {
    connect(deviceId) {
      connectedDevices.add(deviceId);
    },
    disconnect(deviceId) {
      connectedDevices.delete(deviceId);
      for (const fn of listeners) fn(deviceId);
    },
    onDisconnect(fn) {
      listeners.push(fn);
    },
    isConnected(deviceId) {
      return connectedDevices.has(deviceId);
    },
  };
}

module.exports = { createMidiBus };
