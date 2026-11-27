import test from "node:test";
import assert from "node:assert/strict";
import { fft, ifft, dftNaive, isPowerOfTwo } from "../../src/threejs/numerics/fft.js";

function maxComplexError(a, b) {
  let error = 0;
  for (let i = 0; i < a[0].length; i++) {
    error = Math.max(error, Math.abs(a[0][i] - b[0][i]), Math.abs(a[1][i] - b[1][i]));
  }
  return error;
}

test("D35:10 FFT agrees with the definition-level DFT for seeded complex input", () => {
  const re = Float64Array.from({ length: 64 }, (_, i) => Math.sin(i * 0.31) + i / 100);
  const im = Float64Array.from({ length: 64 }, (_, i) => Math.cos(i * 0.17) - i / 80);
  const fast = fft(re, im);
  const reference = dftNaive(re, im);
  assert.ok(maxComplexError(fast, reference) < 1e-10);
});

test("D35:10 inverse FFT reconstructs the original complex signal", () => {
  const re = Float64Array.from({ length: 128 }, (_, i) => Math.sin(3 * i) + 0.4 * Math.cos(11 * i));
  const im = Float64Array.from({ length: 128 }, (_, i) => Math.cos(0.2 * i) / 3);
  const reconstructed = ifft(...fft(re, im));
  assert.ok(maxComplexError(reconstructed, [re, im]) < 1e-10);
});

test("D35:10 FFT preserves Parseval energy with its declared normalization", () => {
  const re = Float64Array.from({ length: 64 }, (_, i) => Math.sin(i * 0.23));
  const im = Float64Array.from({ length: 64 }, (_, i) => Math.cos(i * 0.11) / 2);
  const [fr, fi] = fft(re, im);
  const timeEnergy = re.reduce((s, x, i) => s + x*x + im[i]*im[i], 0);
  const frequencyEnergy = fr.reduce((s, x, i) => s + x*x + fi[i]*fi[i], 0) / re.length;
  assert.ok(Math.abs(timeEnergy - frequencyEnergy) < 1e-9);
});

test("D35:10 FFT validates radix-2 lengths and matching real/imaginary arrays", () => {
  assert.equal(isPowerOfTwo(64), true);
  assert.equal(isPowerOfTwo(50), false);
  assert.throws(() => fft(new Float64Array(50)), /power of two/i);
  assert.throws(() => fft(new Float64Array(8), new Float64Array(4)), /length/i);
});

test("D35:10 FFT leaves caller-owned input arrays unchanged", () => {
  const re = Float64Array.from([1, 2, 3, 4, 5, 6, 7, 8]);
  const im = Float64Array.from([0, 1, 0, -1, 0, 1, 0, -1]);
  const beforeRe = Float64Array.from(re), beforeIm = Float64Array.from(im);
  fft(re, im);
  assert.deepEqual(re, beforeRe);
  assert.deepEqual(im, beforeIm);
});
