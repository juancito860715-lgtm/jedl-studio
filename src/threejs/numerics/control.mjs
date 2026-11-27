/**
 * D35 production control kernels: PID, proportional tracking, critical spring.
 *
 * Independently implemented from the documented algorithms in this repository.
 * Source projects inspected for practical behavior and validation:
 * - https://github.com/m-lundberg/simple-pid (MIT; PID state, measurement
 *   derivative, output limits and anti-windup; tests/test_pid.py)
 * - https://github.com/mrdoob/three.js (MIT; MathUtils.damp and its unit tests)
 * - https://github.com/pmndrs/react-spring (MIT; mass/tension/friction spring
 *   integration, damping ratio and SpringValue/AnimationConfig tests)
 *
 * Units: dt in seconds. Gains/omega must use the units declared by the caller.
 * These are renderer-independent CPU kernels; Three.js objects can consume the
 * returned values without coupling the numerical methods to the render loop.
 */

function finiteNumber(value, name) {
  if (!Number.isFinite(value)) throw new TypeError(name + " must be finite");
}

function clamp(value, lower, upper) {
  return Math.min(upper, Math.max(lower, value));
}

function vectorOf(value, name) {
  if (typeof value === "number") {
    finiteNumber(value, name);
    return null;
  }
  if (!Array.isArray(value) && !ArrayBuffer.isView(value)) {
    throw new TypeError(name + " must be a finite number or numeric array");
  }
  const result = Array.from(value);
  if (result.length === 0) throw new RangeError(name + " must not be empty");
  result.forEach((entry, index) => finiteNumber(entry, name + "[" + index + "]"));
  return result;
}

function mapPair(a, b, fn, label) {
  const av = vectorOf(a, label + " first input");
  const bv = vectorOf(b, label + " second input");
  if (av === null && bv === null) return fn(a, b);
  if (av === null || bv === null || av.length !== bv.length) {
    throw new RangeError(label + " inputs must have matching shapes");
  }
  return av.map((value, index) => fn(value, bv[index]));
}

function magnitude(value) {
  if (typeof value === "number") return Math.abs(value);
  return Math.hypot(...value);
}

function scale(value, factor) {
  return typeof value === "number" ? value * factor : value.map(x => x * factor);
}

function add(a, b) {
  return mapPair(a, b, (x, y) => x + y, "addition");
}

function subtract(a, b) {
  return mapPair(a, b, (x, y) => x - y, "subtraction");
}

function zerosLike(value) {
  return typeof value === "number" ? 0 : value.map(() => 0);
}

function sameShape(a, b, c) {
  const av = vectorOf(a, "position");
  const bv = vectorOf(b, "velocity");
  const cv = vectorOf(c, "target");
  if (av === null && bv === null && cv === null) return;
  if (av === null || bv === null || cv === null ||
      av.length !== bv.length || av.length !== cv.length) {
    throw new RangeError("position, velocity and target must have matching shapes");
  }
}

/**
 * Practical discrete PID controller with conditional-integration anti-windup.
 * update(measurement, dt) expects dt in seconds and returns the bounded output.
 */
export class PIDController {
  constructor({
    kp = 0,
    ki = 0,
    kd = 0,
    setpoint = 0,
    outputLimits = [null, null],
    startingOutput = 0,
    derivativeOnMeasurement = true
  } = {}) {
    for (const [name, value] of Object.entries({ kp, ki, kd, setpoint, startingOutput })) {
      finiteNumber(value, name);
    }
    if (!Array.isArray(outputLimits) || outputLimits.length !== 2) {
      throw new TypeError("outputLimits must be [lower, upper]");
    }
    const lower = outputLimits[0] == null ? -Infinity : outputLimits[0];
    const upper = outputLimits[1] == null ? Infinity : outputLimits[1];
    if (Number.isNaN(lower) || Number.isNaN(upper) || lower >= upper) {
      throw new RangeError("outputLimits lower bound must be less than upper bound");
    }
    this.kp = kp;
    this.ki = ki;
    this.kd = kd;
    this.setpoint = setpoint;
    this.lower = lower;
    this.upper = upper;
    this.derivativeOnMeasurement = Boolean(derivativeOnMeasurement);
    this.startingOutput = clamp(startingOutput, lower, upper);
    this.reset();
  }

  reset() {
    this.integral = this.startingOutput;
    this.previousMeasurement = null;
    this.previousError = null;
    this.components = { proportional: 0, integral: this.integral, derivative: 0, raw: this.integral, output: this.integral };
    return this;
  }

  update(measurement, dt) {
    finiteNumber(measurement, "measurement");
    finiteNumber(dt, "dt");
    if (dt <= 0) throw new RangeError("dt must be greater than zero");

    const error = this.setpoint - measurement;
    const deltaMeasurement = this.previousMeasurement == null ? 0 : measurement - this.previousMeasurement;
    const deltaError = this.previousError == null ? 0 : error - this.previousError;
    const proportional = this.kp * error;
    const derivative = this.kd === 0 ? 0 :
      (this.derivativeOnMeasurement ? -this.kd * deltaMeasurement / dt : this.kd * deltaError / dt);
    const candidateIntegral = clamp(this.integral + this.ki * error * dt, this.lower, this.upper);
    const rawCandidate = proportional + candidateIntegral + derivative;
    const output = clamp(rawCandidate, this.lower, this.upper);

    // Conditional integration: do not accumulate error that pushes farther into saturation.
    const acceptsIntegral = output === rawCandidate ||
      (output === this.upper && error < 0) ||
      (output === this.lower && error > 0);
    if (acceptsIntegral) this.integral = candidateIntegral;

    const raw = proportional + this.integral + derivative;
    const bounded = clamp(raw, this.lower, this.upper);
    this.components = {
      proportional,
      integral: this.integral,
      derivative,
      raw,
      output: bounded
    };
    this.previousMeasurement = measurement;
    this.previousError = error;
    return bounded;
  }
}

/**
 * First-order proportional tracker: x_dot = kp * (target - x).
 * Uses an explicit Euler step, matching the D35:1 discrete algorithm.
 * Rejects unstable steps (kp*dt >= 2); values above 1 may overshoot.
 * Scalar or same-length numeric arrays are supported.
 */
export function proportionalTrack(position, target, kp, dt, { maxSpeed = Infinity, tolerance = 0 } = {}) {
  finiteNumber(kp, "kp");
  finiteNumber(dt, "dt");
  finiteNumber(maxSpeed, "maxSpeed");
  finiteNumber(tolerance, "tolerance");
  if (kp <= 0 || dt <= 0 || tolerance < 0 || maxSpeed <= 0) {
    throw new RangeError("kp and dt must be positive; maxSpeed positive; tolerance non-negative");
  }
  if (kp * dt >= 2) throw new RangeError("kp*dt must be below 2 for explicit-Euler stability");

  const error = subtract(target, position);
  const errorMagnitude = magnitude(error);
  if (errorMagnitude <= tolerance) {
    return { position: typeof position === "number" ? target : Array.from(target), velocity: zerosLike(position), error: 0 };
  }
  let velocity = scale(error, kp);
  const speed = magnitude(velocity);
  if (Number.isFinite(maxSpeed) && speed > maxSpeed) velocity = scale(velocity, maxSpeed / speed);
  const nextPosition = add(position, scale(velocity, dt));
  return { position: nextPosition, velocity, error: magnitude(subtract(target, nextPosition)) };
}

/**
 * Exact time-step of x'' + 2*omega*x' + omega^2*(x-target) = 0 (critical damping).
 * Valid for constant target during the step; scalar or vector states are supported.
 * dt is seconds and omega is radians/second (numerically s^-1).
 */
export function criticalDampedSpringStep(position, velocity, target, omega, dt) {
  finiteNumber(omega, "omega");
  finiteNumber(dt, "dt");
  if (omega < 0 || dt < 0) throw new RangeError("omega and dt must be non-negative");
  sameShape(position, velocity, target);
  if (dt === 0) {
    return {
      position: typeof position === "number" ? position : Array.from(position),
      velocity: typeof velocity === "number" ? velocity : Array.from(velocity)
    };
  }
  if (omega === 0) {
    return { position: add(position, scale(velocity, dt)), velocity: typeof velocity === "number" ? velocity : Array.from(velocity) };
  }

  const y0 = subtract(position, target);
  const c = add(velocity, scale(y0, omega));
  const decay = Math.exp(-omega * dt);
  const nextY = scale(add(y0, scale(c, dt)), decay);
  const nextVelocity = scale(subtract(velocity, scale(c, omega * dt)), decay);
  return { position: add(target, nextY), velocity: nextVelocity };
}
