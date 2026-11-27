import test from "node:test";
import assert from "node:assert/strict";
import { createDemandRenderScheduler } from "../../src/threejs/demand-render-scheduler.mjs";

function fakeFrames() {
  let next = 1;
  const callbacks = new Map();
  return {
    callbacks,
    request(callback) { const id = next++; callbacks.set(id, callback); return id; },
    cancel(id) { callbacks.delete(id); },
    step(timestamp = 0) {
      const [id, callback] = callbacks.entries().next().value || [];
      if (id === undefined) return false;
      callbacks.delete(id);
      callback(timestamp);
      return true;
    }
  };
}
test("initial frame renders once and idle scene stops requesting frames", () => {
  const frames = fakeFrames(); let renders = 0, updates = 0;
  createDemandRenderScheduler({ render: () => renders++, update: () => updates++, requestFrame: cb => frames.request(cb), cancelFrame: id => frames.cancel(id) });
  assert.equal(frames.callbacks.size, 1);
  frames.step(10);
  assert.equal(renders, 1); assert.equal(updates, 1);
  assert.equal(frames.callbacks.size, 0);
});
test("multiple invalidations coalesce into one pending frame", () => {
  const frames = fakeFrames(); let renders = 0;
  const scheduler = createDemandRenderScheduler({ render: () => renders++, requestFrame: cb => frames.request(cb), cancelFrame: id => frames.cancel(id) });
  frames.step();
  scheduler.invalidate(); scheduler.invalidate(); scheduler.invalidate();
  assert.equal(frames.callbacks.size, 1);
  frames.step();
  assert.equal(renders, 2);
  assert.equal(frames.callbacks.size, 0);
});
test("active animation continues scheduling and can return to demand mode", () => {
  const frames = fakeFrames(); let active = true, renders = 0;
  const scheduler = createDemandRenderScheduler({ render: () => renders++, requestFrame: cb => frames.request(cb), cancelFrame: id => frames.cancel(id), isAnimationActive: () => active });
  frames.step(1); frames.step(2);
  assert.equal(renders, 2); assert.equal(frames.callbacks.size, 1);
  active = false; frames.step(3);
  assert.equal(frames.callbacks.size, 0);
});
test("dispose cancels a pending frame and makes future invalidations inert", () => {
  const frames = fakeFrames(); let renders = 0;
  const scheduler = createDemandRenderScheduler({ render: () => renders++, requestFrame: cb => frames.request(cb), cancelFrame: id => frames.cancel(id) });
  scheduler.dispose(); scheduler.invalidate();
  assert.equal(frames.callbacks.size, 0);
  assert.equal(renders, 0);
});
