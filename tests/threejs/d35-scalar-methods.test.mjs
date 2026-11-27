import test from "node:test";
import assert from "node:assert/strict";
import { bisectRoot, cubicHermite } from "../../src/threejs/numerics/scalar-methods.mjs";

test("D35:7 bisection solves linear, quadratic and trigonometric roots", () => {
  const linear = bisectRoot(x => 2 * x - 4, 0, 5);
  const quadratic = bisectRoot(x => x * x - 4, 0, 3);
  const trig = bisectRoot(Math.sin, 3, 4);
  assert.ok(Math.abs(linear.root - 2) <= 1e-10);
  assert.ok(Math.abs(quadratic.root - 2) <= 1e-10);
  assert.ok(Math.abs(trig.root - Math.PI) <= 1e-10);
  assert.equal(linear.converged, true);
});

test("D35:7 endpoint and exact midpoint roots are handled without sign multiplication", () => {
  assert.equal(bisectRoot(x => x, 0, 2).root, 0);
  const exact = bisectRoot(x => x - 1, 0, 2);
  assert.equal(exact.root, 1);
  assert.equal(exact.reason, "exact_root");
});

test("D35:7 rejects invalid brackets and non-finite function values", () => {
  assert.throws(() => bisectRoot(x => x * x + 1, 0, 1), /opposite signs/);
  assert.throws(() => bisectRoot(() => NaN, 0, 1), /finite scalar/);
  assert.throws(() => bisectRoot(x => x, 1, 1), /less than/);
});

test("D35:7 reports positional error bound and iteration exhaustion", () => {
  const result = bisectRoot(x => x * x - 2, 1, 2, { xTolerance: 1e-5 });
  assert.ok(result.errorBound <= 1e-5);
  const limited = bisectRoot(x => x * x - 2, 1, 2, { maxIterations: 1 });
  assert.equal(limited.converged, false);
  assert.equal(limited.reason, "max_iterations");
});

test("D35:8 Hermite interpolation preserves endpoint values and derivatives", () => {
  const start = cubicHermite(2, 8, 3, -1, 0, 0, 2);
  const end = cubicHermite(2, 8, 3, -1, 2, 0, 2);
  assert.equal(start.value, 2);
  assert.equal(end.value, 8);
  assert.equal(start.derivative, 3);
  assert.equal(end.derivative, -1);
});

test("D35:8 Hermite reproduces a linear function over a non-unit interval", () => {
  const result = cubicHermite(4, 10, 3, 3, 1.5, 1, 3);
  assert.ok(Math.abs(result.value - 5.5) < 1e-12);
  assert.ok(Math.abs(result.derivative - 3) < 1e-12);
});

test("D35:8 Hermite supports vectors and clamps outside the interval", () => {
  const middle = cubicHermite([0, 2], [2, 4], [1, 1], [1, 1], 0.5, 0, 1);
  assert.deepEqual(middle.value, [0.5, 2.5]);
  assert.deepEqual(middle.derivative, [1, 1]);
  const outside = cubicHermite([0, 2], [2, 4], [1, 1], [1, 1], -1, 0, 1);
  assert.deepEqual(outside.value, [0, 2]);
  assert.deepEqual(outside.derivative, [0, 0]);
});

test("D35:8 Hermite rejects mismatched shapes and invalid parameter intervals", () => {
  assert.throws(() => cubicHermite([0, 1], [1], [0, 0], [0, 0], 0.5, 0, 1), /matching shapes/);
  assert.throws(() => cubicHermite(0, 1, 0, 0, 0.5, 1, 1), /greater than/);
});
