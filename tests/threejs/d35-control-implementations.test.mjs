import test from "node:test";
import assert from "node:assert/strict";
import { PIDController, proportionalTrack, criticalDampedSpringStep } from "../../src/threejs/numerics/control.mjs";

test("D35:0 PID proportional output and zero-error equilibrium", () => {
  const pid = new PIDController({ kp: 2, setpoint: 3 });
  assert.equal(pid.update(2, 0.1), 2);
  assert.equal(pid.update(3, 0.1), 0);
});

test("D35:0 PID integrates in seconds and prevents integral windup", () => {
  const pid = new PIDController({ ki: 2, setpoint: 10, outputLimits: [-1, 1] });
  assert.equal(pid.update(0, 1), 1);
  assert.equal(pid.components.integral, 1);
  assert.equal(pid.update(0, 1), 1);
  assert.equal(pid.components.integral, 1);
  pid.setpoint = 0;
  assert.equal(pid.update(0, 1), 1);
  assert.equal(pid.components.integral, 1);
});

test("D35:0 PID derivative-on-measurement avoids setpoint derivative kick", () => {
  const pid = new PIDController({ kd: 3, setpoint: 5 });
  assert.equal(pid.update(0, 0.1), 0);
  assert.equal(pid.update(0, 0.1), 0);
  assert.equal(pid.update(1, 0.1), -30);
});

test("D35:0 PID validates dt and output limits", () => {
  const pid = new PIDController({ kp: 1 });
  assert.throws(() => pid.update(0, 0), /dt/);
  assert.throws(() => new PIDController({ outputLimits: [2, 1] }), /lower bound/);
});

test("D35:1 proportional tracker moves toward a scalar target and converges", () => {
  let x = 0;
  for (let i = 0; i < 30; i++) x = proportionalTrack(x, 1, 2, 0.1).position;
  assert.ok(Math.abs(1 - x) < 0.002);
  assert.ok(x <= 1);
});

test("D35:1 proportional tracker supports vectors and speed limits", () => {
  const result = proportionalTrack([0, 0, 0], [3, 4, 0], 2, 0.1, { maxSpeed: 1 });
  assert.deepEqual(result.position, [0.06, 0.08, 0]);
  assert.ok(Math.abs(Math.hypot(...result.velocity) - 1) < 1e-12);
});

test("D35:1 proportional tracker rejects unstable explicit-Euler steps", () => {
  assert.throws(() => proportionalTrack(0, 1, 2, 1), /stability/);
});

test("D35:2 critically damped spring matches the closed-form solution", () => {
  const result = criticalDampedSpringStep(0, 0, 1, 2, 0.5);
  assert.ok(Math.abs(result.position - (1 - 2 / Math.E)) < 1e-12);
  assert.ok(Math.abs(result.velocity - (2 / Math.E)) < 1e-12);
});

test("D35:2 exact spring step has the semigroup property for a fixed target", () => {
  const one = criticalDampedSpringStep(0, 0.3, 1, 3, 0.4);
  const half = criticalDampedSpringStep(0, 0.3, 1, 3, 0.2);
  const two = criticalDampedSpringStep(half.position, half.velocity, 1, 3, 0.2);
  assert.ok(Math.abs(one.position - two.position) < 1e-12);
  assert.ok(Math.abs(one.velocity - two.velocity) < 1e-12);
});

test("D35:2 spring handles vector state, zero time and zero frequency", () => {
  const vector = criticalDampedSpringStep([0, 2], [0, 0], [1, 1], 2, 0.1);
  assert.equal(vector.position.length, 2);
  const unchanged = criticalDampedSpringStep(0, 2, 1, 2, 0);
  assert.deepEqual(unchanged, { position: 0, velocity: 2 });
  const free = criticalDampedSpringStep(0, 2, 1, 0, 0.5);
  assert.equal(free.position, 1);
  assert.equal(free.velocity, 2);
});
