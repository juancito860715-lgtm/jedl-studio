# D35:3 — linear Kalman state model

Status: independent JavaScript kernel and executable tests added. Global workflow pending.

## Mathematics

Prediction:
- (x^- = Ax + Bu) (omit (Bu) when no control is supplied)
- (P^- = APA^T + Q)

Measurement update:
- (r = z-Hx^-)
- (S = HP^-H^T+R)
- (K = P^-H^TS^{-1}), computed by solving a linear system rather than explicitly forming (S^{-1})
- (x^+ = x^-+Kr)
- Joseph covariance: (P^+=(I-KH)P^-(I-KH)^T+KRK^T)
- Symmetrize only for floating-point roundoff; validate posterior positive semidefiniteness.
- Normalized innovation squared: (NIS=r^TS^{-1}r), computed by solving (Sy=r).

## Algorithm and constraints

1. Validate state/matrix dimensions and finite entries.
2. Validate (P,Q,R) as symmetric positive-semidefinite covariance matrices.
3. Predict state and covariance; apply optional control matrix/vector.
4. Form innovation and innovation covariance.
5. Solve (SK^T=(P^-H^T)^T) using pivoted Gaussian elimination. A singular/ill-conditioned innovation covariance is reported, never inverted silently.
6. Apply state correction and Joseph covariance update.
7. Symmetrize roundoff, check PSD, and return prior/posterior state, covariance, gain, innovation and NIS.

The model assumes a linear system with additive zero-mean noise and known covariance matrices. It does not implement EKF/UKF, process/measurement cross-correlation, missing observations or a smoother.

## Units

State components may use different units; each matrix must preserve dimensional compatibility. (P) has state-unit products, (Q) the same covariance units, (H) maps state units to measurement units, (R) has measurement-unit products, and (S) has measurement-unit products. (K) maps measurement residual units into state units. NIS is dimensionless.

## Source provenance

Inspected [rlabbe/filterpy](https://github.com/rlabbe/filterpy), MIT, commit `5df4e095fac07684a05c495bd72d3424f7c68c9c):
- `filterpy/kalman/kalman_filter.py`: predict/update equations, solve/gain and Joseph covariance form.
- `filterpy/kalman/tests/test_kf.py`: 1D and multi-dimensional constant-velocity models, procedural/class parity, sequential updates and Mahalanobis checks.

This implementation is an independent JavaScript adaptation with no NumPy dependency. The local tests use exact scalar and constant-velocity matrix oracles plus covariance and singularity checks.
