/**
 * D36:1 explicit Euler and D36:2 classical RK4 integrators.
 *
 * Implementation basis inspected:
 *   https://github.com/tangent-to/ode
 *   src/fixed.js and tests/fixed.test.js
 * The reference project is MIT-licensed. This file is an independent,
 * dependency-free JavaScript implementation of the same published methods;
 * it does not copy the reference source verbatim.
 *
 * Scope: deterministic CPU integration of y' = f(t,y). Three.js consumes
 * resulting state values for scene updates; it is not used as a numerical
 * integrator. State arrays are copied so caller-owned input is not mutated.
 */

function validateSpan(tSpan) {
  if (!Array.isArray(tSpan) || tSpan.length !== 2 ||
      !Number.isFinite(tSpan[0]) || !Number.isFinite(tSpan[1])) {
    throw new TypeError("tSpan must contain two finite time values");
  }
}

function validateOptions(options) {
  if (!options || typeof options !== "object") {
    throw new TypeError("options must be an object");
  }
  if (options.nSteps !== undefined) {
    if (!Number.isInteger(options.nSteps) || options.nSteps < 1) {
      throw new RangeError("nSteps must be a positive integer");
    }
    return;
  }
  if (options.step !== undefined) {
    if (!Number.isFinite(options.step) || options.step <= 0) {
      throw new RangeError("step must be a positive finite number");
    }
    return;
  }
  throw new TypeError("provide either options.nSteps or options.step");
}

function normalizeState(y0) {
  const scalar = typeof y0 === "number";
  const values = scalar ? [y0] : Array.from(y0 ?? []);
  if (values.length === 0 || !values.every(Number.isFinite)) {
    throw new TypeError("initial state must contain finite values");
  }
  return { values, scalar };
}

function evaluate(f, t, y, size) {
  const raw = f(t, Array.from(y));
  const values = typeof raw === "number" ? [raw] : Array.from(raw ?? []);
  if (values.length !== size) {
    throw new RangeError("derivative dimension does not match state dimension");
  }
  if (!values.every(Number.isFinite)) {
    throw new Error("non-finite derivative returned by RHS");
  }
  return values;
}

function addScaled(y, k, scale) {
  return y.map((value, i) => value + scale * k[i]);
}

function integrate(stepper, f, tSpan, y0, options = {}) {
  validateSpan(tSpan);
  validateOptions(options);
  if (typeof f !== "function") throw new TypeError("f must be a function");

  const [t0, tEnd] = tSpan;
  const { values: initial } = normalizeState(y0);
  const direction = Math.sign(tEnd - t0) || 1;
  const nominalStep = options.nSteps !== undefined
    ? Math.abs(tEnd - t0) / options.nSteps
    : options.step;
  const nSteps = options.nSteps !== undefined
    ? options.nSteps
    : Math.ceil(Math.abs(tEnd - t0) / nominalStep);

  const t = [t0];
  const y = [initial.slice()];
  let current = initial.slice();
  let time = t0;
  let nfev = 0;

  try {
    for (let index = 0; index < nSteps && direction * (tEnd - time) > 0; index++) {
      const remaining = Math.abs(tEnd - time);
      const h = direction * Math.min(nominalStep, remaining);
      const result = stepper(f, time, current, h);
      current = result.state;
      nfev += result.evaluations;
      time = index === nSteps - 1 || Math.abs(tEnd - (time + h)) < 1e-14
        ? tEnd
        : time + h;
      if (!current.every(Number.isFinite)) throw new Error("non-finite state produced by integrator");
      t.push(time);
      y.push(current.slice());
    }
    if (time !== tEnd) {
      throw new Error("integration did not reach tEnd; increase nSteps or check step");
    }
    return { t, y, success: true, message: "integration successful", nfev, nsteps: t.length - 1 };
  } catch (error) {
    return { t, y, success: false, message: error.message, nfev, nsteps: t.length - 1 };
  }
}

/** Forward Euler: y_(n+1) = y_n + h f(t_n,y_n). */
export function integrateEuler(f, tSpan, y0, options = {}) {
  return integrate((rhs, time, state, h) => {
    const k1 = evaluate(rhs, time, state, state.length);
    return { state: addScaled(state, k1, h), evaluations: 1 };
  }, f, tSpan, y0, options);
}

/** Classical fourth-order Runge–Kutta with four RHS evaluations per step. */
export function integrateRK4(f, tSpan, y0, options = {}) {
  return integrate((rhs, time, state, h) => {
    const k1 = evaluate(rhs, time, state, state.length);
    const k2 = evaluate(rhs, time + h / 2, addScaled(state, k1, h / 2), state.length);
    const k3 = evaluate(rhs, time + h / 2, addScaled(state, k2, h / 2), state.length);
    const k4 = evaluate(rhs, time + h, addScaled(state, k3, h), state.length);
    const next = state.map((value, i) =>
      value + h * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]) / 6
    );
    return { state: next, evaluations: 4 };
  }, f, tSpan, y0, options);
}
