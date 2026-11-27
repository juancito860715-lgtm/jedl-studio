import test from "node:test";
import assert from "node:assert/strict";
import { gradientDescent, newtonRoot } from "../../src/threejs/numerics/optimization-roots.mjs";

test("D35:4 gradient descent minimizes a convex quadratic with Armijo backtracking", () => {
  const result = gradientDescent(
    x => x[0] * x[0] + 2 * x[1] * x[1],
    x => [2 * x[0], 4 * x[1]],
    [10, -10],
    { learningRate: 0.2, tolerance: 1e-7, maxIterations: 500 }
  );
  assert.equal(result.converged, true);
  assert.ok(Math.hypot(...result.parameters) < 1e-6);
  assert.ok(result.value < 1e-12);
});

test("D35:4 gradient descent handles an initial optimum and projected constraints", () => {
  const atOptimum = gradientDescent(x => x[0] ** 2, x => [2 * x[0]], [0]);
  assert.equal(atOptimum.iterations, 0);
  const projected = gradientDescent(
    x => (x[0] - 2) ** 2,
    x => [2 * (x[0] - 2)],
    [0],
    { project: x => [Math.max(0, Math.min(1, x[0]))] }
  );
  assert.equal(projected.converged, false);
  assert.equal(projected.reason, "line_search_failed");
  assert.ok(projected.parameters[0] <= 1);
});

test("D35:4 gradient descent reports iteration exhaustion and validates dimensions", () => {
  const limited = gradientDescent(x => x[0] ** 2, x => [2 * x[0]], [10], { maxIterations: 1 });
  assert.equal(limited.reason, "max_iterations");
  assert.throws(() => gradientDescent(x => x[0] ** 2, () => [1, 2], [1]), /shape/);
});

test("D35:6 Newton finds linear, quadratic and trigonometric roots", () => {
  const linear = newtonRoot(x => 2 * x - 4, () => 2, 0);
  const quadratic = newtonRoot(x => x * x - 2, x => 2 * x, 1);
  const trig = newtonRoot(Math.sin, Math.cos, 3);
  assert.ok(Math.abs(linear.root - 2) < 1e-10);
  assert.ok(Math.abs(quadratic.root - Math.SQRT2) < 1e-10);
  assert.ok(Math.abs(trig.root - Math.PI) < 1e-9);
});

test("D35:6 Newton handles small-scale derivatives without a fixed absolute cutoff", () => {
  const result = newtonRoot(x => 1e-20 * (x - 2), () => 1e-20, 10);
  assert.ok(Math.abs(result.root - 2) < 1e-12);
});

test("D35:6 Newton rejects zero derivative and respects the domain", () => {
  const zero = newtonRoot(x => x * x + 1, x => 2 * x, 0);
  assert.equal(zero.reason, "derivative_too_small");
  const bounded = newtonRoot(x => x - 3, () => 1, 0, { domain: [-1, 1] });
  assert.equal(bounded.converged, false);
  assert.equal(bounded.reason, "line_search_failed");
});

test("D35:6 Newton reports non-convergence and validates options", () => {
  const result = newtonRoot(x => x ** 3 - 2 * x + 2, x => 3 * x * x - 2, 0, { maxIterations: 5 });
  assert.equal(result.converged, false);
  assert.throws(() => newtonRoot(x => x, () => 1, 0, { xTolerance: 0 }), /options/);
});
