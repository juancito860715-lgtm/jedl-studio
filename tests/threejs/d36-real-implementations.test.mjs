import test from "node:test";
import assert from "node:assert/strict";
import { integrateEuler, integrateRK4 } from "../../src/threejs/numerics/ode-integrators.js";

const endpoint = result => result.y[result.y.length - 1];
const observedOrder = (coarse, fine) => Math.log2(coarse / fine);

test("D36:1 Euler implementation converges at first order on y'=y", () => {
  const solve = n => integrateEuler((t, y) => [y[0]], [0, 1], [1], { nSteps: n });
  const coarse = Math.abs(endpoint(solve(100))[0] - Math.E);
  const fine = Math.abs(endpoint(solve(200))[0] - Math.E);
  assert.ok(observedOrder(coarse, fine) > 0.95);
  assert.ok(observedOrder(coarse, fine) < 1.05);
});

test("D36:2 RK4 implementation converges at fourth order on y'=y", () => {
  const solve = n => integrateRK4((t, y) => [y[0]], [0, 1], [1], { nSteps: n });
  const coarse = Math.abs(endpoint(solve(8))[0] - Math.E);
  const fine = Math.abs(endpoint(solve(16))[0] - Math.E);
  assert.ok(observedOrder(coarse, fine) > 3.7);
  assert.ok(observedOrder(coarse, fine) < 4.3);
});

test("D36:2 RK4 handles coupled vector state without mutating the initial state", () => {
  const initial = [1, 0];
  const result = integrateRK4((t, y) => [y[1], -y[0]], [0, 1], initial, { nSteps: 100 });
  const final = endpoint(result);
  assert.ok(Math.abs(final[0] - Math.cos(1)) < 1e-9);
  assert.ok(Math.abs(final[1] + Math.sin(1)) < 1e-9);
  assert.deepEqual(initial, [1, 0]);
});

test("D36:1 Euler supports backward integration and lands exactly on tEnd", () => {
  const result = integrateEuler((t, y) => [y[0]], [0, -1], [1], { nSteps: 1000 });
  assert.equal(result.t.at(-1), -1);
  assert.ok(Math.abs(endpoint(result)[0] - Math.exp(-1)) < 0.001);
});

test("D36:1/D36:2 reject invalid step counts and non-finite derivatives", () => {
  for (const solver of [integrateEuler, integrateRK4]) {
    assert.throws(() => solver((t, y) => y, [0, 1], [1], { nSteps: 0 }), /nSteps/);
    const result = solver(() => [Number.NaN], [0, 1], [1], { nSteps: 4 });
    assert.equal(result.success, false);
    assert.match(result.message, /non-finite/i);
  }
});
