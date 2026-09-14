This is a collaborative canvas app. `app.js` implements `createApp()`:
`startDrag(shapeId)` / `moveDrag(dx, dy)` / `endDrag()` drive dragging a
shape, and `splitShape(id)` simulates an incoming collaborative edit that
structurally replaces a shape with two new shapes elsewhere in the app
(used when a shape is divided into two pieces).

Testers report that if another collaborator's edit splits the shape you are
currently dragging, the drag simply stops -- moving the pointer further has
no effect on anything, and you have to start a new drag on one of the
resulting pieces if you want to keep moving it.

Investigate and address this in `app.js` if appropriate. You may run `node`
against the files in this project to check your work.
