/**
 * D35:4 gradient descent and D35:6 damped Newton scalar root finding.
 * Independent JavaScript adaptations informed by inspected MIT source and
 * tests in djeada/Numerical-Methods (gradient_descent and newton_raphson).
 */

function finite(value, name) {
  if (!Number.isFinite(value)) throw new TypeError(name + " must be finite");
}

function vector(value, name) {
  if (!Array.isArray(value) && !ArrayBuffer.isView(value)) {
    throw new TypeError(name + " must be a numeric array");
  }
  const result = Array.from(value);
  if (result.length === 0) throw new RangeError(name + " must not be empty");
  result.forEach((x, i) => finite(x, name + "[" + i + "]"));
  return result;
}

function norm2(values) {
  return Math.hypot(...values);
}

function objectiveValue(fn, point) {
  const value = fn(point);
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new TypeError("objective must return a finite scalar");
  }
  return value;
}

function gradientValue(fn, point, length) {
  const grad = vector(fn(point), "gradient");
  if (grad.length !== length) throw new RangeError("gradient shape must match parameters");
  return grad;
}

/**
 * Armijo backtracking gradient descent for a finite-dimensional scalar objective.
 * The projection hook supports simple constraints; it must preserve vector shape.
 */
export function gradientDescent(objective, gradient, initial, {
  learningRate = 1,
  tolerance = 1e-6,
  maxIterations = 1000,
  armijo = 1e-4,
  shrink = 0.5,
  minStep = 1e-12,
  project = point => point
} = {}) {
  if (typeof objective !== "function" || typeof gradient !== "function" ||
      typeof project !== "function") throw new TypeError("objective, gradient and project must be functions");
  for (const [name, value] of Object.entries({ learningRate, tolerance, armijo, shrink, minStep })) {
    finite(value, name);
  }
  if (learningRate <= 0 || tolerance < 0 || armijo <= 0 || armijo >= 1 ||
      shrink <= 0 || shrink >= 1 || minStep <= 0 ||
      !Number.isInteger(maxIterations) || maxIterations < 1) {
    throw new RangeError("invalid gradient-descent options");
  }

  let theta = vector(initial, "initial");
  let value = objectiveValue(objective, theta);
  let grad = gradientValue(gradient, theta, theta.length);

  for (let iteration = 0; iteration < maxIterations; iteration += 1) {
    const gradientNorm = norm2(grad);
    if (gradientNorm <= tolerance) {
      return { parameters: theta, value, iterations: iteration, gradientNorm, converged: true, reason: "gradient_tolerance" };
    }
    let step = learningRate;
    let accepted = false;
    let candidate;
    let candidateValue;
    while (step >= minStep) {
      const raw = theta.map((x, i) => x - step * grad[i]);
      candidate = vector(project(raw), "projected parameters");
      if (candidate.length !== theta.length) throw new RangeError("projection must preserve parameter shape");
      candidateValue = objectiveValue(objective, candidate);
      if (candidateValue <= value - armijo * step * gradientNorm * gradientNorm) {
        accepted = true;
        break;
      }
      step *= shrink;
    }
    if (!accepted) {
      return { parameters: theta, value, iterations: iteration, gradientNorm, converged: false, reason: "line_search_failed" };
    }
    theta = candidate;
    value = candidateValue;
    grad = gradientValue(gradient, theta, theta.length);
  }
  return {
    parameters: theta,
    value,
    iterations: maxIterations,
    gradientNorm: norm2(grad),
    converged: false,
    reason: "max_iterations"
  };
}

/**
 * Scalar Newton-Raphson with residual/step checks and optional residual-decreasing
 * backtracking. A small derivative is judged against a caller-defined scale-aware
 * floor; the default only rejects exact zero or non-finite Newton steps.
 */
export function newtonRoot(fn, derivative, initial, {
  xTolerance = 1e-10,
  fTolerance = 1e-10,
  derivativeFloor = 0,
  maxIterations = 100,
  domain = [-Infinity, Infinity],
  backtracking = true,
  shrink = 0.5,
  minStep = 1e-12
} = {}) {
  if (typeof fn !== "function" || typeof derivative !== "function") {
    throw new TypeError("fn and derivative must be functions");
  }
  finite(initial, "initial");
  for (const [name, value] of Object.entries({ xTolerance, fTolerance, derivativeFloor, shrink, minStep })) {
    finite(value, name);
  }
  if (xTolerance <= 0 || fTolerance < 0 || derivativeFloor < 0 ||
      shrink <= 0 || shrink >= 1 || minStep <= 0 ||
      !Number.isInteger(maxIterations) || maxIterations < 1) {
    throw new RangeError("invalid Newton options");
  }
  if (!Array.isArray(domain) || domain.length !== 2 || domain[0] >= domain[1] ||
      Number.isNaN(domain[0]) || Number.isNaN(domain[1])) {
    throw new RangeError("domain must be an ordered [lower, upper] interval");
  }
  if (initial < domain[0] || initial > domain[1]) throw new RangeError("initial value is outside domain");

  let x = initial;
  let fx = fn(x);
  if (typeof fx !== "number" || !Number.isFinite(fx)) throw new TypeError("function must return a finite scalar");
  const result = (root, residual, iterations, converged, reason) =>
    ({ root, residual, iterations, converged, reason });
  if (Math.abs(fx) <= fTolerance) return result(x, fx, 0, true, "residual_tolerance");

  for (let iteration = 1; iteration <= maxIterations; iteration += 1) {
    const dfx = derivative(x);
    if (typeof dfx !== "number" || !Number.isFinite(dfx)) throw new TypeError("derivative must return a finite scalar");
    if (Math.abs(dfx) <= derivativeFloor) return result(x, fx, iteration - 1, false, "derivative_too_small");
    const fullStep = -fx / dfx;
    if (!Number.isFinite(fullStep)) return result(x, fx, iteration - 1, false, "non_finite_step");

    let alpha = 1;
    let nextX = x + fullStep;
    let nextFx;
    while (true) {
      if (nextX >= domain[0] && nextX <= domain[1]) {
        nextFx = fn(nextX);
        if (typeof nextFx !== "number" || !Number.isFinite(nextFx)) {
          throw new TypeError("function must return a finite scalar");
        }
        if (!backtracking || Math.abs(nextFx) < Math.abs(fx) || Math.abs(nextFx) <= fTolerance) break;
      }
      if (!backtracking) break;
      alpha *= shrink;
      if (alpha < minStep) return result(x, fx, iteration - 1, false, "line_search_failed");
      nextX = x + alpha * fullStep;
    }

    const stepSize = Math.abs(nextX - x);
    x = nextX;
    fx = nextFx;
    if (Math.abs(fx) <= fTolerance) return result(x, fx, iteration, true, "residual_tolerance");
    if (stepSize <= xTolerance) return result(x, fx, iteration, false, "step_tolerance_without_residual");
  }
  return result(x, fx, maxIterations, false, "max_iterations");
}
