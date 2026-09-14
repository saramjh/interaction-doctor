This is a small offline-first notes app. `app.js` implements `createApp()`:
`createNote(id, text)` creates a note, `deleteNote(id)` removes one,
`queueEdit(id, text)` queues an edit command (used while offline, or while
a save is batched rather than applied immediately), and `flushQueue()`
applies every queued command in order once connectivity/batching allows.

Users report that occasionally, after a note is deleted, content
reappears in that note's slot later -- and in one report, a brand-new
note (created with a since-reused id) ended up showing old content from a
completely different, already-deleted note instead of what was just
typed into it.

Investigate and fix the implementation in this project so that a queued
edit only ever applies to the note it was actually meant for, and never
resurrects or corrupts an unrelated note. Do not change the public shape
of `createApp()` unless necessary. You may run `node` against the files
in this project to check your work.
