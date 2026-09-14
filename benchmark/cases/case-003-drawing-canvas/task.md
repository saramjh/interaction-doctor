This is a drawing canvas. `canvas.js` implements `createCanvas()`: holding
the spacebar and dragging pans the canvas; dragging without the spacebar
held draws a freehand stroke. `keydownSpace`/`keyupSpace` track the
spacebar; `pointerdown`/`pointermove`/`pointerup` drive drawing/panning.

Please audit the interaction handling in this project for correctness and
fix anything that's actually broken. You may run `node` against the files
in this project to check your work. Do not make unnecessary changes.
