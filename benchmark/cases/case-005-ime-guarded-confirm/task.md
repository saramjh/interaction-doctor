This is a chat message composer. `composer.js` implements `createComposer()`:
typing characters builds up a draft; pressing Enter normally sends the
draft as a message. The composer also supports IME composition for
languages like Japanese, Chinese, or Korean, via `compositionstart`,
`compositionupdate`, and `compositionend` calls that mirror what a real
browser's IME dispatches while a user is composing text through a
candidate window.

Please audit the interaction handling in this project for correctness and
fix anything that's actually broken. You may run `node` against the files
in this project to check your work. Do not make unnecessary changes.
