This is a search box component built against a small React-style component
harness. `app.js` implements `createSearchBox(harness, clock)`:
`harness.registerCleanup(fn)` mirrors React's `useEffect(() => { ...; return
cleanup })` contract -- whatever cleanup functions are registered must run
when `harness.unmount()` is called. `clock` is a deterministic fake timer
(`clock.setTimeout(fn, delay)` / `clock.advance(ms)`) used in place of the
real browser timer so this can be tested without waiting on wall-clock time.
Typing into the search box schedules a debounced request for suggestions;
after the delay, `state.suggestions` and `state.requestCount` update with
the result.

Testers report that if a user types into the search box and then navigates
away (the component unmounts) before the debounce delay elapses, something
still updates a short while later even though the search box is gone, and a
freshly opened search box on the next screen can end up in a confusing
state.

Investigate and fix the implementation in this project. You may run `node`
against the files in this project to check your work.
