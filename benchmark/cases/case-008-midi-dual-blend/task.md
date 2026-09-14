This is a small synth control surface. `synth.js` implements
`createSynth(mixRatio)`: a filter-cutoff parameter is continuously driven
by two simultaneous analog MIDI controllers -- a mod wheel and a breath
controller. Both controllers are always "live" at once (a performer can
move either, or both, at any time, in any order); the current cutoff
value is a deterministic weighted blend of both controllers' latest
readings.

Please audit the interaction handling in this project for correctness and
fix anything that's actually broken. You may run `node` against the files
in this project to check your work. Do not make unnecessary changes.
