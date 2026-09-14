// Usage: node test.js <path-to-workspace>
const path = require('path');

const workspace = process.argv[2];
if (!workspace) {
  console.error(JSON.stringify({ pass: false, reason: 'missing workspace arg' }));
  process.exit(2);
}

let createFaderApp, createMidiBus;
try {
  ({ createFaderApp } = require(path.join(workspace, 'app.js')));
  ({ createMidiBus } = require(path.join(workspace, 'midi-shim.js')));
} catch (e) {
  console.log(JSON.stringify({ pass: false, reason: `could not load fixture: ${e.message}` }));
  process.exit(1);
}

function connectedDeviceControlsFaderNormally() {
  const bus = createMidiBus();
  const fader = createFaderApp(bus);
  bus.connect('A');
  fader.midiControl('A', 77);
  return fader.state.value === 77 && fader.state.externalDeviceId === 'A';
}

function localUiWorksWhenNoExternalControlActive() {
  const bus = createMidiBus();
  const fader = createFaderApp(bus);
  fader.localSet(30);
  return fader.state.value === 30;
}

function deviceADisconnectMidInteractionReleasesControl() {
  // Checks BOTH that control is released AND that the release itself does
  // not reset the fader's value -- only the ownership, not the value, is
  // required to change at disconnect.
  const bus = createMidiBus();
  const fader = createFaderApp(bus);
  bus.connect('A');
  fader.midiControl('A', 80);
  bus.disconnect('A');
  return fader.state.externalDeviceId === null && fader.state.value === 80;
}

function localUiWorksImmediatelyAfterDisconnect() {
  const bus = createMidiBus();
  const fader = createFaderApp(bus);
  bus.connect('A');
  fader.midiControl('A', 80);
  bus.disconnect('A');
  fader.localSet(15);
  return fader.state.value === 15;
}

function reconnectAndFreshInteractionWorks() {
  const bus = createMidiBus();
  const fader = createFaderApp(bus);
  bus.connect('A');
  fader.midiControl('A', 80);
  bus.disconnect('A');
  bus.connect('A');
  fader.midiControl('A', 60);
  return fader.state.value === 60 && fader.state.externalDeviceId === 'A';
}

function cleanMidiEndWithoutDisconnectStillWorks() {
  const bus = createMidiBus();
  const fader = createFaderApp(bus);
  bus.connect('A');
  fader.midiControl('A', 80);
  fader.midiControlEnd('A');
  fader.localSet(25);
  return fader.state.externalDeviceId === null && fader.state.value === 25;
}

function disconnectWithNoActiveInteractionIsHarmless() {
  const bus = createMidiBus();
  const fader = createFaderApp(bus);
  bus.connect('A');
  bus.disconnect('A');
  return fader.state.externalDeviceId === null && fader.state.value === 50;
}

function unrelatedDeviceDisconnectDoesNotCancelActiveInteraction() {
  const bus = createMidiBus();
  const fader = createFaderApp(bus);
  bus.connect('A');
  bus.connect('B');
  fader.midiControl('A', 80);
  bus.disconnect('B'); // unrelated device, never controlled the fader
  return fader.state.externalDeviceId === 'A' && fader.state.value === 80;
}

const results = {
  device_a_disconnect_mid_interaction_releases_control: deviceADisconnectMidInteractionReleasesControl(),
  local_ui_works_immediately_after_disconnect: localUiWorksImmediatelyAfterDisconnect(),
  connected_device_controls_fader_normally: connectedDeviceControlsFaderNormally(),
  local_ui_works_when_no_external_control_active: localUiWorksWhenNoExternalControlActive(),
  reconnect_and_fresh_interaction_works: reconnectAndFreshInteractionWorks(),
  clean_midi_end_without_disconnect_still_works: cleanMidiEndWithoutDisconnectStillWorks(),
  disconnect_with_no_active_interaction_is_harmless: disconnectWithNoActiveInteractionIsHarmless(),
  unrelated_device_disconnect_does_not_cancel_active_interaction: unrelatedDeviceDisconnectDoesNotCancelActiveInteraction(),
};

const pass = Object.values(results).every(Boolean);
console.log(JSON.stringify({ pass, results }, null, 2));
process.exit(pass ? 0 : 1);
