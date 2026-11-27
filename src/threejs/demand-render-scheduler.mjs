// Coalesced render scheduler for mostly-static Three.js scenes.
// Browser APIs are injected so the scheduling state machine is testable in Node.
export function createDemandRenderScheduler({
  render,
  update = () => {},
  requestFrame,
  cancelFrame = () => {},
  isAnimationActive = () => false
} = {}) {
  if (typeof render !== "function" || typeof update !== "function" ||
      typeof requestFrame !== "function" || typeof cancelFrame !== "function" ||
      typeof isAnimationActive !== "function") {
    throw new TypeError("render, requestFrame, cancelFrame and isAnimationActive must be functions");
  }
  let dirty = true;
  let pending = null;
  let disposed = false;
  function schedule() {
    if (disposed || pending !== null) return;
    pending = requestFrame(frame);
  }
  function frame(timestamp) {
    pending = null;
    if (disposed) return;
    const shouldRender = dirty || isAnimationActive();
    dirty = false;
    if (shouldRender) {
      update(timestamp);
      render(timestamp);
    }
    if (dirty || isAnimationActive()) schedule();
  }
  function invalidate() {
    if (disposed) return;
    dirty = true;
    schedule();
  }
  function wake() { if (!disposed && isAnimationActive()) schedule(); }
  function dispose() {
    if (disposed) return;
    disposed = true;
    if (pending !== null) cancelFrame(pending);
    pending = null;
  }
  schedule();
  return { invalidate, wake, dispose, get dirty() { return dirty; }, get pending() { return pending !== null; } };
}
