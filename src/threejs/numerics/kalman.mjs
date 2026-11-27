/**
 * D35:3 linear Kalman predict/update kernel.
 * Independent JavaScript adaptation informed by FilterPy's MIT KalmanFilter
 * predict/update implementation and its test_kf.py reference cases.
 * No runtime dependency; matrices are ordinary finite JavaScript arrays.
 */

function matrix(value, name, rows, cols) {
  if (!Array.isArray(value) || value.length !== rows) throw new RangeError(name + " row count mismatch");
  const out = value.map((row, i) => {
    if ((!Array.isArray(row) && !ArrayBuffer.isView(row)) || row.length !== cols) {
      throw new RangeError(name + " column count mismatch at row " + i);
    }
    return Array.from(row, (v, j) => {
      if (typeof v !== "number" || !Number.isFinite(v)) throw new TypeError(name + "[" + i + "][" + j + "] must be finite");
      return v;
    });
  });
  return out;
}

function vector(value, name, length) {
  if ((!Array.isArray(value) && !ArrayBuffer.isView(value)) || value.length !== length) {
    throw new RangeError(name + " length mismatch");
  }
  return Array.from(value, (v, i) => {
    if (typeof v !== "number" || !Number.isFinite(v)) throw new TypeError(name + "[" + i + "] must be finite");
    return v;
  });
}

const zeros = (r, c) => Array.from({ length: r }, () => Array(c).fill(0));
const identity = n => Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => i === j ? 1 : 0));
const transpose = A => A[0].map((_, j) => A.map(row => row[j]));
const add = (A, B) => A.map((row, i) => row.map((v, j) => v + B[i][j]));
const subtract = (A, B) => A.map((row, i) => row.map((v, j) => v - B[i][j]));
const multiply = (A, B) => {
  const BT = transpose(B);
  return A.map(row => BT.map(col => row.reduce((sum, v, i) => sum + v * col[i], 0)));
};
const matVec = (A, x) => A.map(row => row.reduce((sum, v, i) => sum + v * x[i], 0));
const outerAdd = (A, B) => add(A, B);
const dot = (a, b) => a.reduce((sum, v, i) => sum + v * b[i], 0);

function maxAbs(A) {
  return Math.max(0, ...A.flat().map(Math.abs));
}

function validateCovariance(A, name, n) {
  const M = matrix(A, name, n, n);
  const scale = maxAbs(M);
  const tol = Math.max(Number.MIN_VALUE, scale * 1e-10);
  for (let i = 0; i < n; i += 1) {
    for (let j = i + 1; j < n; j += 1) {
      if (Math.abs(M[i][j] - M[j][i]) > tol) throw new RangeError(name + " must be symmetric");
    }
  }
  if (!isPositiveSemidefinite(M)) throw new RangeError(name + " must be positive semidefinite");
  return M;
}

function isPositiveSemidefinite(input) {
  const A = input.map(row => row.slice());
  const n = A.length;
  const scale = maxAbs(A);
  if (scale === 0) return true;
  const tol = Math.max(Number.MIN_VALUE, scale * 1e-11);
  const maxIterations = Math.max(1, 50 * n * n);
  for (let iteration = 0; iteration < maxIterations; iteration += 1) {
    let p = 0, q = 0, largest = 0;
    for (let i = 0; i < n; i += 1) {
      for (let j = i + 1; j < n; j += 1) {
        const value = Math.abs(A[i][j]);
        if (value > largest) { largest = value; p = i; q = j; }
      }
    }
    if (largest <= tol) break;
    const angle = 0.5 * Math.atan2(2 * A[p][q], A[q][q] - A[p][p]);
    const c = Math.cos(angle), s = Math.sin(angle);
    const app = A[p][p], aqq = A[q][q], apq = A[p][q];
    A[p][p] = c * c * app - 2 * s * c * apq + s * s * aqq;
    A[q][q] = s * s * app + 2 * s * c * apq + c * c * aqq;
    A[p][q] = 0;
    A[q][p] = 0;
    for (let k = 0; k < n; k += 1) {
      if (k === p || k === q) continue;
      const akp = A[k][p], akq = A[k][q];
      A[k][p] = A[p][k] = c * akp - s * akq;
      A[k][q] = A[q][k] = s * akp + c * akq;
    }
  }
  return A.every((row, i) => row[i] >= -tol);
}

function solveLinear(A, B) {
  const n = A.length;
  const M = A.map((row, i) => [...row, ...B[i]]);
  const rhsCols = B[0].length;
  const scale = maxAbs(A);
  if (scale === 0) throw new RangeError("innovation covariance is singular");
  const pivotTolerance = scale * Number.EPSILON * n * 16;
  for (let col = 0; col < n; col += 1) {
    let pivot = col;
    for (let row = col + 1; row < n; row += 1) {
      if (Math.abs(M[row][col]) > Math.abs(M[pivot][col])) pivot = row;
    }
    if (Math.abs(M[pivot][col]) <= pivotTolerance) {
      throw new RangeError("innovation covariance is singular or ill-conditioned");
    }
    [M[col], M[pivot]] = [M[pivot], M[col]];
    const divisor = M[col][col];
    for (let j = col; j < n + rhsCols; j += 1) M[col][j] /= divisor;
    for (let row = 0; row < n; row += 1) {
      if (row === col) continue;
      const factor = M[row][col];
      for (let j = col; j < n + rhsCols; j += 1) M[row][j] -= factor * M[col][j];
    }
  }
  return M.map(row => row.slice(n));
}

function symmetrize(A) {
  return A.map((row, i) => row.map((v, j) => 0.5 * (v + A[j][i])));
}

/**
 * One linear Kalman predict/update cycle.
 * state x, covariance P; transition A; process covariance Q;
 * measurement matrix H; measurement covariance R; measurement z.
 * Optional control matrix B and control vector u implement x⁻=Ax+Bu.
 */
export function kalmanStep({
  state, covariance, transition, processNoise,
  measurementMatrix, measurementNoise, measurement,
  controlMatrix = null, control = null
}) {
  if (!Array.isArray(state) || state.length < 1) throw new RangeError("state must be a non-empty vector");
  const n = state.length;
  const x = vector(state, "state", n);
  const P = validateCovariance(covariance, "covariance", n);
  const A = matrix(transition, "transition", n, n);
  const Q = validateCovariance(processNoise, "processNoise", n);
  if (!Array.isArray(measurementMatrix) || measurementMatrix.length < 1) {
    throw new RangeError("measurementMatrix must have at least one row");
  }
  const m = measurementMatrix.length;
  if ((!Array.isArray(measurementMatrix[0]) && !ArrayBuffer.isView(measurementMatrix[0])) ||
      measurementMatrix[0].length !== n) throw new RangeError("measurementMatrix column count mismatch");
  const H = matrix(measurementMatrix, "measurementMatrix", m, n);
  const R = validateCovariance(measurementNoise, "measurementNoise", m);
  const z = vector(measurement, "measurement", m);

  let xPred = matVec(A, x);
  if (controlMatrix !== null) {
    if (!Array.isArray(control) && !ArrayBuffer.isView(control)) {
      throw new RangeError("control vector is required when controlMatrix is provided");
    }
    const u = Array.from(control);
    const B = matrix(controlMatrix, "controlMatrix", n, u.length);
    const bu = matVec(B, vector(u, "control", u.length));
    xPred = xPred.map((v, i) => v + bu[i]);
  } else if (control !== null) {
    throw new RangeError("controlMatrix is required when control is provided");
  }

  const PPred = add(multiply(multiply(A, P), transpose(A)), Q);
  const innovation = z.map((v, i) => v - matVec(H, xPred)[i]);
  const PHT = multiply(PPred, transpose(H));
  const S = add(multiply(H, PHT), R);
  const solved = solveLinear(S, transpose(PHT));
  const K = transpose(solved);
  const correction = matVec(K, innovation);
  const xPost = xPred.map((v, i) => v + correction[i]);

  const IminusKH = subtract(identity(n), multiply(K, H));
  const josephLeft = multiply(multiply(IminusKH, PPred), transpose(IminusKH));
  const josephNoise = multiply(multiply(K, R), transpose(K));
  const PPost = symmetrize(outerAdd(josephLeft, josephNoise));
  if (!isPositiveSemidefinite(PPost)) {
    throw new RangeError("posterior covariance lost positive semidefiniteness");
  }
  const whitenedInnovation = solveLinear(S, innovation.map(v => [v])).map(row => row[0]);
  const nis = dot(innovation, whitenedInnovation);

  return {
    state: xPost,
    covariance: PPost,
    predictedState: xPred,
    predictedCovariance: PPred,
    innovation,
    innovationCovariance: S,
    gain: K,
    normalizedInnovationSquared: nis
  };
}
