import { configure } from "@testing-library/dom";

/**
 * `waitFor` waits long enough for a lazily imported tab to arrive.
 *
 * `vitest.config.mts` already raised `testTimeout` to 15s because "the
 * render-heavy tab tests can blow past the 5s default when the machine / CI
 * runner is under load". That never reached `waitFor`, which keeps its own
 * deadline — `asyncUtilTimeout`, 1s by default — and that is the deadline the
 * tab tests actually wait on: since the tabs became dynamic imports, the first
 * `waitFor` for one also waits for Vite to transform it.
 *
 * So `TabPanels.test.tsx` failed in a full `make check` run (right after the
 * production build, machine busy) with `Unable to find role="button" and name
 * "防具"`, and passed on its own and in three suite runs straight after.
 * Shrinking `asyncUtilTimeout` reproduces that exact failure, which is what
 * pins the cause to this deadline rather than to a missing element.
 *
 * 5s is the same intent as the `testTimeout` bump, and stays well inside it so
 * a genuinely missing element still fails the test rather than the run.
 */
configure({ asyncUtilTimeout: 5000 });

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
