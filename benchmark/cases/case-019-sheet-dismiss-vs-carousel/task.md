This is a semantic model of a bottom sheet that supports native interactive
drag-to-dismiss, containing a horizontally-scrolling photo carousel.
`app.js` implements `createSheetWithCarousel()`: `dragStart(region)` begins
a drag, with `region` being `'carousel'` (the drag started over the photo
carousel) or `'sheet'` (anywhere else on the sheet); `dragMove(dx, dy)`
reports incremental horizontal/vertical movement; `dragEnd()` finishes the
drag. The sheet's vertical drag-to-dismiss and the carousel's horizontal
paging both track movement from drags that start in the carousel region.

Testers report that a drag starting on the photo carousel, when it also
has enough vertical movement, can both change which photo is showing and
dismiss the sheet at the same time.

Investigate and address this in `app.js` if appropriate. You may run
`node` against the files in this project to check your work.
