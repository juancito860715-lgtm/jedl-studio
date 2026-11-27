# D35 production control kernels — implementation notes

Status: implementation committed; GitHub validation pending. Do not treat this note as a certification.

## D35:0 — PID controller

**Implemented:** `src/threejs/numerics/control.mjs`, class `PIDController`.

The controller uses seconds for `dt`, independent proportional/integral/derivative terms, bounded output, and conditional integration anti-windup. The default derivative is taken on the measurement to avoid a derivative kick when the setpoint changes. The caller can choose derivative-on-error explicitly.

```text
e = setpoint - measurement
P = Kp * e
D = -Kd * (measurement - previousMeasurement) / dt
I_candidate = clamp(I + Ki * e * dt, outputMin, outputMax)
u_candidate = P + I_candidate + D
u = clamp(u_candidate, outputMin, outputMax)
accept I_candidate only when saturation is not driven farther
```

Reference project: [m-lundberg/simple-pid](https://github.com/m-lundberg/simple-pid), MIT, commit `6e6f4b000cdf7830635674cb89a6e823f5025784`. Inspected `simple_pid/pid.py`, `tests/test_pid.py`, and its CI workflow. The upstream latest run is action-required; it is not represented as a green run. The local JavaScript implementation is independently tested.

## D35:1 — proportional tracking

**Implemented:** `proportionalTrack(position, target, kp, dt, options)`.

```text
error = target - position
velocity = kp * error
if speed(velocity) > maxSpeed: scale velocity to maxSpeed
positionNext = position + dt * velocity
require kp > 0, dt > 0 and kp*dt < 2
```

For the scalar constant-target model, the Euler error multiplier is `1-kp*dt`; the step is stable for `0 < kp*dt < 2`, and monotonic without overshoot for `0 < kp*dt <= 1`. Vector arrays are supported and the speed cap applies to vector magnitude.

Reference project: [three.js](https://github.com/mrdoob/three.js), MIT, commit `0de0346de82a0d01923ffeb27f33240ad8b4863f`. Inspected `src/math/MathUtils.js` (`damp`) and `test/unit/src/math/MathUtils.tests.js`; upstream CI run [46015390100](https://github.com/mrdoob/three.js/actions/runs/46015390100) succeeded. Three.js uses the exact exponential solution of the continuous first-order model; this local implementation deliberately retains the manifest's explicit-Euler step and tests its stability bound.

## D35:2 — critically damped spring

**Implemented:** `criticalDampedSpringStep(position, velocity, target, omega, dt)`.

For a constant target, let `y=x-target` and `c=v+omega*y`. The exact step is:

```text
decay = exp(-omega*dt)
xNext = target + (y + c*dt) * decay
vNext = (v - omega*c*dt) * decay
```

This is the closed-form solution of `x'' + 2*omega*x' + omega^2*(x-target) = 0`. It supports scalar or vector states, zero-time identity, and the `omega=0` constant-velocity limit. It assumes the target and frequency remain constant during the step.

Reference project: [pmndrs/react-spring](https://github.com/pmndrs/react-spring), MIT, commit `f005007bef2c67e95abc6b2f03e3d5a9e2b3bdcd`. Inspected `SpringValue.ts`, `AnimationConfig.ts`, and their tests. The source documents damping ratio 1 as non-bouncing and tests the spring runtime; upstream CI run [46000682696](https://github.com/pmndrs/react-spring/actions/runs/46000682696) succeeded. The local implementation uses the exact constant-target propagator rather than copying the source's small-step integrator.

## Local tests

`tests/threejs/d35-control-implementations.test.mjs` exercises PID proportional/integral/derivative and anti-windup behavior, scalar/vector proportional tracking, speed limits and Euler stability, the exact spring solution, step-composition property, zero-time and zero-frequency cases.

The global Three.js workflow includes this test file and is configured to run when `src/threejs/**` changes. Promotion to production-implementation-passed requires the workflow to finish successfully on the exact commit.
