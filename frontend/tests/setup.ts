/**
 * What happy-dom leaves out that the app actually calls.
 *
 * `confirm`, `prompt` and `print` are the three places the app hands control to
 * the browser chrome — "really delete this character?", "name for the copy",
 * and the print dialog. happy-dom defines none of them, so a test that spies on
 * one got `vi.spyOn() can only spy on a function. Received undefined.`
 *
 * jsdom does define all three, as no-ops that return the "user dismissed it"
 * answer (`false` / `null`) and never block. These are the same stubs: the
 * tests that care spy on them and dictate the answer themselves, and the ones
 * that do not get the dismissal, which is the safe default for a suite that
 * must not stop for a dialog.
 */
beforeEach(() => {
  window.confirm = () => false;
  window.prompt = () => null;
  window.print = () => {};
});
