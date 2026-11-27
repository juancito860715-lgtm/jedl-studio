# D35:7 and D35:8 — production implementation notes

Status: implementation added; global CI and readiness report pending. These are not certified yet.

## D35:7 — Bisection root finder

Production API: `bisectRoot(fn, lower, upper, options)` in `src/threejs/numerics/scalar-methods.mjs`.

Mathematics: for continuous (f:[a,b]\to\mathbb R) with opposite endpoint signs, the intermediate value theorem guarantees at least one root in the bracket. Each midpoint (m=(a+b)/2) selects the half interval whose endpoint signs differ. After (k) updates, the bracket width is ((b_0-a_0)/2^k), so the midpoint positional error is bounded by half that width.

Algorithm and safeguards:
1. Validate finite ordered endpoints, positive position tolerance, non-negative residual tolerance, and positive integer iteration cap.
2. Evaluate endpoints; return exact endpoint roots; reject a bracket without a sign change.
3. Evaluate midpoint without multiplying endpoint values (avoids overflow in sign tests).
4. Replace the endpoint with the same sign as the midpoint.
5. Stop on positional half-width or separately configured residual tolerance; report which criterion fired.
6. Return an explicit non-converged status on iteration or floating-point precision exhaustion.

Units: (a,b,m,xTolerance) share the independent-variable unit; (f(a),f(b),fTolerance) share the function-output unit. The two tolerances are not interchangeable.

Source project inspected: [djeada/Numerical-Methods](https://github.com/djeada/Numerical-Methods), MIT. The Python bisection implementation and pytest cases were inspected at the upstream repository. The local JavaScript implementation is an independent adaptation with separate position/residual tolerances, sign comparisons, and precision-limit reporting.

## D35:8 — Cubic Hermite interpolation

Production API: `cubicHermite(p0,p1,tangent0,tangent1,t,t0,t1)`.

Let (T=t_1-t_0>0), (s=(t-t_0)/T). The basis is:
- (h_{00}=2s^3-3s^2+1)
- (h_{10}=s^3-2s^2+s)
- (h_{01}=-2s^3+3s^2)
- (h_{11}=s^3-s^2)

Then (p(s)=h_{00}p_0+h_{10}T m_0+h_{01}p_1+h_{11}T m_1), where (m_0,m_1) are derivatives with respect to physical parameter (t). The returned derivative is (dp/dt=(1/T)dp/ds). Scalar and vector samples are supported; clamping outside the interval returns endpoint value and zero derivative.

Source project inspected: [mrdoob/three.js](https://github.com/mrdoob/three.js), MIT. The Three.js `CubicInterpolant` source and unit tests provide the production reference for cubic Hermite interpolation over parameterized sample positions. This implementation is an independent compact kernel, not a copy of the Three.js class.

## Executable local tests

`tests/threejs/d35-scalar-methods.test.mjs` covers known roots, exact endpoints/midpoints, invalid brackets, non-finite evaluations, interval error bounds, iteration exhaustion, Hermite endpoint values/tangents, linear reproduction, vector data, clamping and invalid shapes.

The global workflow must pass on the exact commit before either technique is promoted to implementation-tests-passed. Certification remains a separate gate.
