This is a small app with a document-level "?" keyboard shortcut that opens
a help overlay, and a search input where users can type freely (including
a literal "?" character, e.g. searching for "how do I export csv?").
`dom-shim.js` is a tiny fake DOM (fake elements with `addEventListener`/
`dispatch`, bubbling keyboard events) that stands in for the real browser
DOM in this exercise -- treat it as equivalent to real keydown events on
real nested elements, where an event dispatched on a focused child bubbles
up to any listener registered on the document unless something stops it.

Users report that typing "?" into the search box sometimes also opens the
help overlay at the same time.

Investigate and address this in `app.js`. You may run `node` against the
files in this project to check your work.
