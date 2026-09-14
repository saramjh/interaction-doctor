This is a semantic model of an on-screen fader that can be controlled
either locally or by a connected physical MIDI device. `app.js`
implements `createFaderApp(midiBus)`: `midiControl(deviceId, value)`
reports the named device actively driving the fader, `midiControlEnd(
deviceId)` reports that device's control ending normally, and `localSet(
value)` represents local UI input. `midi-shim.js` provides
`createMidiBus()`: `connect(deviceId)` / `disconnect(deviceId)` report a
device's connection state, and `onDisconnect(fn)` registers a listener
for disconnection events.

While a connected device is actively driving the fader, local UI input is
suppressed so it doesn't fight the hardware. If that device physically
disconnects while it is still actively driving the fader, its control
over the fader ends immediately; local UI input becomes usable again
right away, and the device may start a fresh interaction later if it
reconnects. A device disconnecting while it is NOT the one currently
driving the fader has no effect on whichever device is.

Testers report that if the MIDI device driving the fader is unplugged
mid-interaction, the fader stays locked to that device's control
indefinitely -- local UI input has no effect even though nothing is
connected anymore.

Investigate and fix the implementation in this project. You may run
`node` against the files in this project to check your work.
