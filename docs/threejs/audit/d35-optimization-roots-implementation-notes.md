# D35:4 and D35:6 — implementation notes

Status: source inspection complete; implementation and executable tests added; global CI pending.

## D35:4 — Gradient descent

`gradientDescent(objective, gradient, initial, options)` minimizes a differentiable scalar objective over a finite-dimensional vector. Each step uses (\theta_{k+1}=\Pi_\Omega(\theta_k-\alpha_k\nabla J(\theta_k))). The Armijo condition accepts a step only if (J(\theta_{k+1})\le J(\theta_k)-c\alpha_k\|\nabla J\|_2^2). Backtracking reduces alpha by a fixed factor; failure to find a step above minStep is returned explicitly. The projection callback supports simple constraints, but does not claim to solve arbitrary constrained optimization.

Units: objective and gradient units must be coherent with parameter units; learning rate carries parameter-unit / gradient-unit. The Armijo scalar is dimensionless.

## D35:6 — Newton scalar root finder

`newtonRoot(fn, derivative, initial, options)` uses (x_{k+1}=x_k-\alpha_k f(x_k)/f'(x_k)), with optional backtracking to remain in a declared interval and decrease the residual. A small derivative is compared with the caller's derivativeFloor; no universal absolute threshold is imposed. Residual tolerance and step tolerance are reported separately. Step-size convergence alone is not accepted as a root if the residual remains above tolerance.

Units: x and xTolerance share the independent-variable unit; f and fTolerance share output units; f' has output-unit / x-unit; the Newton step therefore has x units.

## Source provenance

Inspected [djeada/Numerical-Methods](https://github.com/djeada/Numerical-Methods), MIT:
- `gradient_descent` implementation and tests for quadratic/Rosenbrock objectives, stationary points, convergence failure and dimension behavior.
- `newton_raphson` implementation and tests for linear/quadratic/trigonometric roots, exact/near-zero derivative behavior, small-scale derivatives, and iteration failure.

The local kernels are independent JavaScript adaptations. They add Armijo backtracking, projection support, explicit result statuses, domain limits and separate convergence criteria. No upstream test is represented as a local test.

## Local executable tests

`tests/threejs/d35-optimization-roots.test.mjs` tests convergence, projected boundaries, initial optimum, dimensions, small-scale derivatives, domain constraints and non-convergence. Full global workflow is required before promotion; certification remains pending.
