import test from "node:test";
import assert from "node:assert/strict";
import { kalmanStep } from "../../src/threejs/numerics/kalman.mjs";

const close = (a, b, tolerance = 1e-10) => assert.ok(Math.abs(a - b) <= tolerance, `${a} != ${b}`);

test("D35:3 scalar Kalman update matches the closed-form Bayesian result", () => {
  const result = kalmanStep({
    state: [0], covariance: [[1]], transition: [[1]], processNoise: [[0]],
    measurementMatrix: [[1]], measurementNoise: [[1]], measurement: [2]
  });
  close(result.state[0], 1);
  close(result.covariance[0][0], 0.5);
  close(result.innovation[0], 2);
  close(result.innovationCovariance[0][0], 2);
  close(result.gain[0][0], 0.5);
  close(result.normalizedInnovationSquared, 2);
});

test("D35:3 constant-velocity state model matches an independent matrix oracle", () => {
  const result = kalmanStep({
    state: [0, 1],
    covariance: [[1, 0], [0, 1]],
    transition: [[1, 1], [0, 1]],
    processNoise: [[0, 0], [0, 0]],
    measurementMatrix: [[1, 0]],
    measurementNoise: [[0.25]],
    measurement: [1.2]
  });
  close(result.state[0], 1.1777777777777778);
  close(result.state[1], 1.0888888888888888);
  close(result.covariance[0][0], 0.2222222222222222);
  close(result.covariance[0][1], 0.1111111111111111);
  close(result.covariance[1][1], 0.5555555555555556);
  close(result.normalizedInnovationSquared, 0.017777777777777778);
});

test("D35:3 optional control matrix contributes Bu to the predicted state", () => {
  const result = kalmanStep({
    state: [1, 0], covariance: [[1, 0], [0, 1]],
    transition: [[1, 1], [0, 1]], processNoise: [[0, 0], [0, 0]],
    measurementMatrix: [[1, 0]], measurementNoise: [[1]], measurement: [2],
    controlMatrix: [[0.5], [1]], control: [2]
  });
  close(result.predictedState[0], 2);
  close(result.predictedState[1], 2);
});

test("D35:3 Joseph update returns symmetric positive-semidefinite covariance", () => {
  const result = kalmanStep({
    state: [0, 0], covariance: [[2, 0.5], [0.5, 1]],
    transition: [[1, 0], [0, 1]], processNoise: [[0, 0], [0, 0]],
    measurementMatrix: [[1, 0], [0, 1]], measurementNoise: [[0.1, 0], [0, 0.2]],
    measurement: [1, -1]
  });
  close(result.covariance[0][1], result.covariance[1][0]);
  assert.ok(result.covariance[0][0] >= 0);
  assert.ok(result.covariance[1][1] >= 0);
});

test("D35:3 rejects singular innovation covariance, bad shapes and invalid covariance", () => {
  assert.throws(() => kalmanStep({
    state: [0], covariance: [[0]], transition: [[1]], processNoise: [[0]],
    measurementMatrix: [[1]], measurementNoise: [[0]], measurement: [1]
  }), /singular/);
  assert.throws(() => kalmanStep({
    state: [0], covariance: [[-1]], transition: [[1]], processNoise: [[0]],
    measurementMatrix: [[1]], measurementNoise: [[1]], measurement: [1]
  }), /positive semidefinite/);
  assert.throws(() => kalmanStep({
    state: [0], covariance: [[1]], transition: [[1, 0]], processNoise: [[0]],
    measurementMatrix: [[1]], measurementNoise: [[1]], measurement: [1]
  }), /column count/);
});
