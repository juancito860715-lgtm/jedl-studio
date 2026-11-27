/**
 * D35:7 bisection root finder and D35:8 cubic Hermite interpolation.
 * Independent JavaScript adaptations informed by inspected MIT projects:
 * - djeada/Numerical-Methods: bisection implementation and pytest cases.
 * - mrdoob/three.js: CubicInterpolant implementation and unit tests.
 * These kernels are CPU-side and renderer-independent; Three.js consumes
 * their scalar/vector outputs in animation curves and procedural controls.
 */

function finite(value, name) {
  if (!Number.isFinite(value)) throw new TypeError(name + " must be finite");
}

function evaluateFinite(fn, x) {
  const value = fn(x);
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new TypeError("function must return a finite scalar");
  }
  return value;
}

/**
 * Bisection for a continuous scalar function on a sign-changing bracket.
 * xTolerance is a positional tolerance; fTolerance is a residual tolerance.
 * The two stopping criteria are deliberately reported separately.
 */
export function bisectRoot(fn, lower, upper, {
  xTolerance = 1e-10,
  fTolerance = 0,
  maxIterations = 128
} = {}) {
  if (typeof fn !== "function") throw new TypeError("fn must be a function");
  finite(lower, "lower");
  finite(upper, "upper");
  finite(xTolerance, "xTolerance");
  finite(fTolerance, "fTolerance");
  if (!(lower < upper)) throw new RangeError("lower must be less than upper");
  if (!(xTolerance > 0) || fTolerance < 0) throw new RangeError("invalid tolerances");
  if (!Number.isInteger(maxIterations) || maxIterations < 1) {
    throw new RangeError("maxIterations must be a positive integer");
  }

  let a = lower;
  let b = upper;
  let fa = evaluateFinite(fn, a);
  let fb = evaluateFinite(fn, b);
  const result = (root, residual, iterations, converged, reason) => ({
    root, lower: a, upper: b, residual, iterations,
    errorBound: (b - a) / 2, converged, reason
  });

  if (fa === 0) return result(a, fa, 0, true, "endpoint_root");
  if (fb === 0) return result(b, fb, 0, true, "endpoint_root");
  if ((fa < 0) === (fb < 0)) {
    throw new RangeError("function values at endpoints must have opposite signs");
  }

  for (let iteration = 1; iteration <= maxIterations; iteration += 1) {
    const midpoint = a + (b - a) / 2;
    if (midpoint === a || midpoint === b) {
      const root = midpoint;
      return result(root, evaluateFinite(fn, root), iteration - 1, false, "precision_limit");
    }
    const fm = evaluateFinite(fn, midpoint);
    if (fm === 0) {
      a = midpoint;
      b = midpoint;
      return result(midpoint, fm, iteration, true, "exact_root");
    }
    if ((fa < 0) !== (fm < 0)) {
      b = midpoint;
      fb = fm;
    } else {
      a = midpoint;
      fa = fm;
    }
    const center = a + (b - a) / 2;
    const residual = evaluateFinite(fn, center);
    if ((b - a) / 2 <= xTolerance) {
      return result(center, residual, iteration, true, "position_tolerance");
    }
    if (fTolerance > 0 && Math.abs(residual) <= fTolerance) {
      return result(center, residual, iteration, true, "residual_tolerance");
    }
  }
  const root = a + (b - a) / 2;
  return result(root, evaluateFinite(fn, root), maxIterations, false, "max_iterations");
}

function asVector(value, name) {
  if (typeof value === "number") {
    finite(value, name);
    return null;
  }
  if (!Array.isArray(value) && !ArrayBuffer.isView(value)) {
    throw new TypeError(name + " must be a finite number or numeric array");
  }
  const values = Array.from(value);
  if (values.length === 0) throw new RangeError(name + " must not be empty");
  values.forEach((entry, index) => finite(entry, name + "[" + index + "]"));
  return values;
}

function combineHermite(p0, p1, m0, m1, h00, h10, h01, h11) {
  const a = asVector(p0, "p0");
  const b = asVector(p1, "p1");
  const c = asVector(m0, "tangent0");
  const d = asVector(m1, "tangent1");
  if (a === null && b === null && c === null && d === null) {
    return h00 * p0 + h10 * m0 + h01 * p1 + h11 * m1;
  }
  const arrays = [a, b, c, d];
  if (arrays.some(item => item === null) ||
      arrays.some(item => item.length !== a.length)) {
    throw new RangeError("Hermite inputs must have matching shapes");
  }
  return a.map((_, i) => h00 * a[i] + h10 * m0[i] + h01 * b[i] + h11 * m1[i]);
}

/**
 * Cubic Hermite interpolation between p0 and p1.
 * Tangents are derivatives with respect to the original parameter t.
 * Returns value and derivative d(value)/dt; supports scalars and vectors.
 */
export function cubicHermite(p0, p1, tangent0, tangent1, t, t0, t1, {
  clamp: clampParameter = true
} = {}) {
  finite(t, "t");
  finite(t0, "t0");
  finite(t1, "t1");
  if (!(t1 > t0)) throw new RangeError("t1 must be greater than t0");
  const duration = t1 - t0;
  let s = (t - t0) / duration;
  if (clampParameter) s = Math.min(1, Math.max(0, s));
  const s2 = s * s;
  const s3 = s2 * s;

  const value = combineHermite(
    p0, p1, tangent0, tangent1,
    2 * s3 - 3 * s2 + 1,
    (s3 - 2 * s2 + s) * duration,
    -2 * s3 + 3 * s2,
    (s3 - s2) * duration
  );
  const derivative = combineHermite(
    p0, p1, tangent0, tangent1,
    (6 * s2 - 6 * s) / duration,
    3 * s2 - 4 * s + 1,
    (-6 * s2 + 6 * s) / duration,
    3 * s2 - 2 * s
  );
  if (clampParameter && (t < t0 || t > t1)) {
    return { value: t < t0 ? p0 : p1, derivative: typeof p0 === "number" ? 0 : Array.from(p0, () => 0) };
  }
  return { value, derivative };
}
