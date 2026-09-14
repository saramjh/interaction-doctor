This is a semantic model of a timeline/editor viewport. `app.js` implements
`createTimelineEditor()`, returning: `pointerDownScrubber(x)` / `pointerMoveScrubber(x)`
/ `pointerUp()` (a scrub-drag near the timeline edge), `advanceFrame()`
(advances one runtime frame, including any native-settle and periodic
drag-autoscroll work that are still scheduled for that frame),
`clickTimeline(viewportX)` (click the timeline at a viewport-relative x,
placing a keyframe), `getActualScrollOffset()`, `getPlacedKeyframes()`,
and `isDragging()`.

While a scrub-drag near the timeline edge is active, the viewport
auto-scrolls periodically to keep following it. Releasing the pointer ends
that drag-driven auto-scroll immediately -- no further auto-scroll work
attributable to the drag should move the viewport after release.

Separately, the viewport also has its own native scroll-settle behavior
that can continue briefly on its own after the pointer is released --
this is independent of the drag and is expected to keep running even
after drag-driven auto-scroll has correctly stopped. Clicking the
timeline while that settle is still in progress is supported and should
work normally.

Clicking the timeline places a keyframe at the timeline content position
that is visually under the pointer at the moment of the click -- i.e. the
clicked viewport coordinate plus whatever the viewport's current scroll
offset actually is at that moment.

Testers report that auto-scroll driven by an edge scrub-drag sometimes
keeps moving the viewport even after the pointer has already been
released.

Please audit the interaction handling in this project for correctness and
fix anything that's actually broken, then verify the surrounding timeline
behavior still works correctly. You may run `node` against the files in
this project to check your work. Do not make unnecessary changes.
