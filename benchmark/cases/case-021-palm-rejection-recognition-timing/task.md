This is a semantic model of a stylus drawing surface with a palm-rejection
classifier. `app.js` implements `createDrawingSurface()`: `pointerDown(
classification)` begins tracking a touch with the classifier's reading at
that instant (`'PEN'` or `'PALM'`), `classifierUpdate(classification)`
reports a revised reading from the classifier before the surface has
committed to a decision, `pointerMove(x, y)` reports movement (the surface
commits to drawing or rejecting the touch the first time movement is
reported), and `pointerUp()` ends the touch.

The surface is defined to draw with a touch's stylus stroke only when the
classifier's most current reading, at the moment the surface commits to a
decision, is `'PEN'` -- not necessarily whatever the classifier's very
first reading was.

Testers report that an initial brief misread which the classifier corrects
a moment later -- before any movement is reported -- can still cause the
stroke to be silently rejected (or, in the other direction, an accidental
palm touch to draw), because the surface already committed to its
decision using the classifier's very first reading.

Investigate and fix the implementation in this project. You may run `node`
against the files in this project to check your work.
