"""Numerical reference tests for selected R31 mathematical kernels.

These tests validate isolated mathematical kernels, not Three.js renderer
compatibility or visual quality. Standard library only.
"""
import math
import unittest


def quantized_time(t, sample_rate):
    if sample_rate <= 0:
        raise ValueError("sample_rate must be > 0")
    return math.floor(t * sample_rate) / sample_rate


def smooth_min(a, b, k):
    if k < 0:
        raise ValueError("k must be >= 0")
    if k == 0:
        return min(a, b)
    h = max(k - abs(a - b), 0.0) / k
    return min(a, b) - (h * h * k) / 4.0


def xpbd_distance_step(x0, x1, rest_length, w0, w1, compliance, dt, lam=0.0):
    """One scalar distance-constraint projection in 1D."""
    if dt <= 0 or min(w0, w1, compliance) < 0:
        raise ValueError("dt must be positive; weights/compliance nonnegative")
    delta = x1 - x0
    distance = abs(delta)
    if distance == 0:
        raise ValueError("coincident points have undefined distance gradient")
    direction = 1.0 if delta > 0 else -1.0
    constraint = distance - rest_length
    alpha_tilde = compliance / (dt * dt)
    denom = w0 + w1 + alpha_tilde
    if denom == 0:
        raise ValueError("constraint has zero effective inverse mass")
    dlambda = -(constraint + alpha_tilde * lam) / denom
    # Gradients: dC/dx0=-direction, dC/dx1=direction.
    x0_new = x0 + w0 * (-direction) * dlambda
    x1_new = x1 + w1 * direction * dlambda
    return x0_new, x1_new, lam + dlambda


def rk4_scalar(f, y, t, dt):
    k1 = f(y, t)
    k2 = f(y + 0.5 * dt * k1, t + 0.5 * dt)
    k3 = f(y + 0.5 * dt * k2, t + 0.5 * dt)
    k4 = f(y + dt * k3, t + dt)
    return y + dt * (k1 + 2*k2 + 2*k3 + k4) / 6.0


def beer_lambert_transmittance(sigma_t, distance):
    if sigma_t < 0 or distance < 0:
        raise ValueError("sigma_t and distance must be nonnegative")
    return math.exp(-sigma_t * distance)


def fresnel_schlick(f0, cos_theta):
    c = min(1.0, max(0.0, cos_theta))
    return f0 + (1.0 - f0) * (1.0 - c) ** 5


def spatial_cell(position, origin, cell_size):
    if cell_size <= 0:
        raise ValueError("cell_size must be > 0")
    return tuple(math.floor((p - o) / cell_size) for p, o in zip(position, origin))


def structure_tensor_orientation(jxx, jxy, jyy):
    # Principal gradient eigenvector angle, modulo pi.
    return 0.5 * math.atan2(2.0 * jxy, jxx - jyy)


def dual_quaternion_normalize(qr, qd):
    norm = math.sqrt(sum(v*v for v in qr))
    if norm == 0:
        raise ValueError("real quaternion cannot be zero")
    r = tuple(v / norm for v in qr)
    d0 = tuple(v / norm for v in qd)
    dot = sum(a*b for a, b in zip(r, d0))
    d = tuple(v - dot*a for v, a in zip(d0, r))
    return r, d


def fabrik(points, lengths, target, root, iterations=64, tolerance=1e-9):
    """Minimal positional FABRIK solver for an unconstrained open chain."""
    pts = [list(p) for p in points]
    if len(pts) != len(lengths) + 1:
        raise ValueError("points must contain one more joint than lengths")
    if any(length <= 0 for length in lengths):
        raise ValueError("segment lengths must be positive")

    def distance(a, b):
        return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))

    total = sum(lengths)
    if distance(root, target) >= total:
        direction_length = distance(root, target)
        direction = [(target[i]-root[i])/direction_length for i in range(len(root))]
        pts[0] = list(root)
        for i, length in enumerate(lengths):
            pts[i+1] = [pts[i][j] + direction[j]*length for j in range(len(root))]
        return pts

    base = list(root)
    for _ in range(iterations):
        pts[-1] = list(target)
        for i in range(len(lengths)-1, -1, -1):
            d = distance(pts[i], pts[i+1])
            if d == 0:
                raise ValueError("degenerate backward projection")
            pts[i] = [
                pts[i+1][j] + (pts[i][j]-pts[i+1][j]) * lengths[i] / d
                for j in range(len(root))
            ]
        pts[0] = base
        for i, length in enumerate(lengths):
            d = distance(pts[i], pts[i+1])
            if d == 0:
                raise ValueError("degenerate forward projection")
            pts[i+1] = [
                pts[i][j] + (pts[i+1][j]-pts[i][j]) * length / d
                for j in range(len(root))
            ]
        if distance(pts[-1], target) <= tolerance:
            break
    return pts


class TestR31NumericalKernels(unittest.TestCase):
    def assertVecAlmostEqual(self, actual, expected, places=9):
        self.assertEqual(len(actual), len(expected))
        for a, e in zip(actual, expected):
            self.assertAlmostEqual(a, e, places=places)

    def test_temporal_quantization_floor(self):
        self.assertAlmostEqual(quantized_time(1.13, 12), 13/12)
        self.assertAlmostEqual(quantized_time(-0.01, 12), -1/12)

    def test_smooth_min_disjoint_and_midpoint(self):
        self.assertAlmostEqual(smooth_min(0.0, 2.0, 0.5), 0.0)
        self.assertAlmostEqual(smooth_min(0.0, 0.0, 0.5), -0.125)
        self.assertAlmostEqual(smooth_min(0.0, 2.0, 0.0), 0.0)

    def test_xpbd_rigid_distance_constraint_one_projection(self):
        x0, x1, lam = xpbd_distance_step(0.0, 2.0, 1.0, 1.0, 1.0, 0.0, 1.0)
        self.assertAlmostEqual(x0, 0.5)
        self.assertAlmostEqual(x1, 1.5)
        self.assertAlmostEqual(abs(x1-x0), 1.0)
        self.assertAlmostEqual(lam, -0.5)

    def test_xpbd_compliance_reduces_single_step_correction(self):
        rigid = xpbd_distance_step(0.0, 2.0, 1.0, 1.0, 1.0, 0.0, 1.0)
        soft = xpbd_distance_step(0.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        self.assertGreater(abs(soft[1]-soft[0]), abs(rigid[1]-rigid[0]))

    def test_rk4_exponential_decay_converges(self):
        y = 1.0
        dt = 0.1
        for i in range(10):
            y = rk4_scalar(lambda value, _t: -value, y, i*dt, dt)
        self.assertAlmostEqual(y, math.exp(-1.0), places=6)

    def test_beer_lambert_reference_value(self):
        self.assertAlmostEqual(beer_lambert_transmittance(2.0, 0.5), math.exp(-1.0))
        self.assertEqual(beer_lambert_transmittance(0.0, 10.0), 1.0)

    def test_fresnel_schlick_endpoints(self):
        f0 = 0.04
        self.assertAlmostEqual(fresnel_schlick(f0, 1.0), f0)
        self.assertAlmostEqual(fresnel_schlick(f0, 0.0), 1.0)

    def test_spatial_hash_floor_including_negative_coordinates(self):
        self.assertEqual(spatial_cell((1.9, -0.1, 4.0), (0, 0, 0), 1.0), (1, -1, 4))

    def test_structure_tensor_orientation_axis_aligned(self):
        self.assertAlmostEqual(structure_tensor_orientation(4.0, 0.0, 1.0), 0.0)
        self.assertAlmostEqual(structure_tensor_orientation(1.0, 0.0, 4.0), math.pi/2)

    def test_dual_quaternion_normalization_and_orthogonality(self):
        qr, qd = dual_quaternion_normalize((2, 0, 0, 0), (1, 3, 0, 0))
        self.assertVecAlmostEqual(qr, (1, 0, 0, 0))
        self.assertVecAlmostEqual(qd, (0, 1.5, 0, 0))
        self.assertAlmostEqual(sum(a*b for a,b in zip(qr, qd)), 0.0)


    def test_fabrik_reaches_reachable_target_and_preserves_lengths(self):
        result = fabrik([(0, 0), (1, 0), (2, 0)], [1.0, 1.0], (1, 1), (0, 0))
        self.assertAlmostEqual(math.dist(result[-1], (1, 1)), 0.0, places=7)
        self.assertAlmostEqual(math.dist(result[0], result[1]), 1.0, places=9)
        self.assertAlmostEqual(math.dist(result[1], result[2]), 1.0, places=9)

    def test_fabrik_unreachable_target_extends_chain_to_max_reach(self):
        result = fabrik([(0, 0), (1, 0), (2, 0)], [1.0, 1.0], (3, 0), (0, 0))
        self.assertVecAlmostEqual(result[-1], (2.0, 0.0))

    def test_dual_quaternion_rejects_zero_real_part(self):
        with self.assertRaises(ValueError):
            dual_quaternion_normalize((0, 0, 0, 0), (1, 0, 0, 0))


if __name__ == "__main__":
    unittest.main(verbosity=2)
