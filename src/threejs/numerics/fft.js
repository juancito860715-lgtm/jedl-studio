/**
 * D35:10 radix-2 Cooley–Tukey FFT and definition-level DFT oracle.
 *
 * Implementation basis inspected:
 *   https://github.com/abho7/fluid-sim
 *   src/core/fft.js and test/core.test.js
 * Reference repository commit: aabf3d1cee198ab3fce86909ad7c362a521b817c
 * License: MIT. This is an independent implementation of the same algorithm,
 * not a verbatim copy. The source repository validates its FFT against a naive
 * DFT, inverse round-trip and Parseval; its CI run recorded 76/76 tests passed.
 *
 * The forward transform is unnormalised; the inverse applies 1/N.
 * Three.js may consume the returned spectral arrays for scene/audio/texture
 * processing; the transform itself is a CPU numerical module.
 */

export function isPowerOfTwo(n) {
  return Number.isInteger(n) && n > 0 && (n & (n - 1)) === 0;
}

function validateComplexInput(re, im) {
  if (!re || typeof re.length !== "number" || !isPowerOfTwo(re.length)) {
    throw new RangeError("FFT length must be a positive power of two");
  }
  if (im !== null && im !== undefined && im.length !== re.length) {
    throw new RangeError("real and imaginary arrays must have matching length");
  }
}

export function fftInPlace(re, im, sign = -1) {
  validateComplexInput(re, im);
  if (sign !== -1 && sign !== 1) throw new RangeError("FFT sign must be -1 or +1");
  if (!im) throw new TypeError("fftInPlace requires real and imaginary arrays");

  const n = re.length;
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1;
    while ((j & bit) !== 0) {
      j ^= bit;
      bit >>= 1;
    }
    j ^= bit;
    if (i < j) {
      [re[i], re[j]] = [re[j], re[i]];
      [im[i], im[j]] = [im[j], im[i]];
    }
  }

  for (let length = 2; length <= n; length <<= 1) {
    const angle = sign * 2 * Math.PI / length;
    const stepRe = Math.cos(angle);
    const stepIm = Math.sin(angle);
    for (let offset = 0; offset < n; offset += length) {
      let twiddleRe = 1;
      let twiddleIm = 0;
      for (let k = 0; k < length / 2; k++) {
        const even = offset + k;
        const odd = even + length / 2;
        const oddRe = re[odd] * twiddleRe - im[odd] * twiddleIm;
        const oddIm = re[odd] * twiddleIm + im[odd] * twiddleRe;
        const evenRe = re[even];
        const evenIm = im[even];
        re[even] = evenRe + oddRe;
        im[even] = evenIm + oddIm;
        re[odd] = evenRe - oddRe;
        im[odd] = evenIm - oddIm;

        const nextTwiddleRe = twiddleRe * stepRe - twiddleIm * stepIm;
        twiddleIm = twiddleRe * stepIm + twiddleIm * stepRe;
        twiddleRe = nextTwiddleRe;
      }
    }
  }
  return [re, im];
}

export function fft(realInput, imaginaryInput = null) {
  validateComplexInput(realInput, imaginaryInput);
  const re = Float64Array.from(realInput);
  const im = imaginaryInput === null
    ? new Float64Array(re.length)
    : Float64Array.from(imaginaryInput);
  return fftInPlace(re, im, -1);
}

export function ifft(realInput, imaginaryInput) {
  validateComplexInput(realInput, imaginaryInput);
  if (imaginaryInput === null || imaginaryInput === undefined) {
    throw new TypeError("inverse FFT requires real and imaginary arrays");
  }
  const [re, im] = fftInPlace(
    Float64Array.from(realInput),
    Float64Array.from(imaginaryInput),
    1
  );
  for (let i = 0; i < re.length; i++) {
    re[i] /= re.length;
    im[i] /= im.length;
  }
  return [re, im];
}

/** O(N²) direct DFT, retained as an independent small-input test oracle. */
export function dftNaive(realInput, imaginaryInput = null) {
  validateComplexInput(realInput, imaginaryInput);
  const n = realInput.length;
  const sourceIm = imaginaryInput ?? new Float64Array(n);
  const re = new Float64Array(n);
  const im = new Float64Array(n);
  for (let k = 0; k < n; k++) {
    let sumRe = 0;
    let sumIm = 0;
    for (let sample = 0; sample < n; sample++) {
      const angle = -2 * Math.PI * k * sample / n;
      const cosine = Math.cos(angle);
      const sine = Math.sin(angle);
      sumRe += realInput[sample] * cosine - sourceIm[sample] * sine;
      sumIm += realInput[sample] * sine + sourceIm[sample] * cosine;
    }
    re[k] = sumRe;
    im[k] = sumIm;
  }
  return [re, im];
}
