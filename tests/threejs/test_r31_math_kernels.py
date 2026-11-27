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




# Additional isolated kernels for the remaining R31 records. These are
# explicitly scoped reference kernels, not full production algorithms.
def deterministic_jitter(frame, seed, channel, amplitude):
    if amplitude < 0:
        raise ValueError("amplitude must be nonnegative")
    x = (int(frame) * 0x9E3779B1 + int(seed) * 0x85EBCA77 + int(channel) * 0xC2B2AE3D) & 0xFFFFFFFF
    x ^= x >> 16
    x = (x * 0x7FEB352D) & 0xFFFFFFFF
    x ^= x >> 15
    x = (x * 0x846CA68B) & 0xFFFFFFFF
    x ^= x >> 16
    unit = x / 4294967296.0
    return amplitude * (2.0 * unit - 1.0)


def ggx_ndf(cos_theta, alpha):
    if alpha <= 0:
        raise ValueError("alpha must be positive")
    c = min(1.0, max(0.0, cos_theta))
    a2 = alpha * alpha
    denom = c*c*(a2-1.0)+1.0
    return a2 / (math.pi * denom * denom)




def hair_ggx_ndf(dot_h_m, beta):
    """Huang et al. 2022 Appendix A, Eq. (41), fiber microfacet NDF."""
    if not (0.0 < beta <= 1.0) or not math.isfinite(dot_h_m):
        raise ValueError("beta must be in (0,1] and dot finite")
    d = max(-1.0, min(1.0, dot_h_m))
    b2 = beta * beta
    return b2 / (math.pi * (1.0 + (b2 - 1.0) * d * d) ** 2)


def hair_tilted_half_dot(theta_h, phi_h, phi_m, alpha):
    """Huang et al. 2022 Appendix A, Eq. (42)."""
    return (math.cos(theta_h) * math.cos(alpha) * math.cos(phi_h - phi_m)
            + math.sin(theta_h) * math.sin(alpha))


def prioritized_acceleration_allocation(requests, max_acceleration):
    """Reynolds 1987 p.29: ordered acceleration requests, strengths and trim."""
    if max_acceleration < 0 or not math.isfinite(max_acceleration):
        raise ValueError("max_acceleration must be finite and nonnegative")
    out = [0.0, 0.0, 0.0]
    used = 0.0
    for acceleration, strength in requests:
        if len(acceleration) != 3 or not all(math.isfinite(v) for v in acceleration):
            raise ValueError("each acceleration request must be a finite 3-vector")
        if not (0.0 <= strength <= 1.0) or not math.isfinite(strength):
            raise ValueError("strength must be finite and in [0,1]")
        norm = math.sqrt(sum(v*v for v in acceleration))
        if norm == 0.0 or strength == 0.0:
            continue
        # Each isolated behavior request is capped at unit magnitude.
        scale = min(1.0, 1.0 / norm) * strength
        req = [v * scale for v in acceleration]
        req_norm = math.sqrt(sum(v*v for v in req))
        remaining = max_acceleration - used
        if remaining <= 0.0:
            break
        if req_norm > remaining:
            trim = remaining / req_norm
            req = [v * trim for v in req]
            req_norm = remaining
        out = [out[i] + req[i] for i in range(3)]
        used += req_norm
        if used >= max_acceleration:
            break
    return tuple(out)

def anisotropic_kuwahara_mean(means, stddev_norms, q=8):
    """Kyprianidis et al. 2009 weighted sector mean: alpha_i=1/(1+||s_i||^q)."""
    if not means or len(means) != len(stddev_norms):
        raise ValueError("means and stddev_norms must be nonempty and same length")
    if q <= 0 or any(v < 0 for v in stddev_norms):
        raise ValueError("q must be positive and standard deviations nonnegative")
    weights = [1.0 / (1.0 + value ** q) for value in stddev_norms]
    total = sum(weights)
    if total == 0 or not math.isfinite(total):
        raise ValueError("invalid Kuwahara weight normalization")
    return sum(m * w for m, w in zip(means, weights)) / total

def weighted_sector_mean(means, variances):
    if not means or len(means) != len(variances):
        raise ValueError("means and variances must be nonempty and same length")
    if any(v < 0 for v in variances):
        raise ValueError("variances must be nonnegative")
    weights = [1.0/(1.0+v) for v in variances]
    return sum(m*w for m,w in zip(means,weights))/sum(weights)


def linear_height_gradient(a, b, x, y):
    # h(x,y)=a*x+b*y; central differences have this exact gradient.
    eps = 1e-5
    h = lambda px,py: a*px+b*py
    gx = (h(x+eps,y)-h(x-eps,y))/(2*eps)
    gy = (h(x,y+eps)-h(x,y-eps))/(2*eps)
    return gx,gy


def oriented_periodic_noise(position, direction, frequency):
    length = math.sqrt(sum(v*v for v in direction))
    if length == 0 or frequency <= 0:
        raise ValueError("direction and frequency must be nonzero/positive")
    d = tuple(v/length for v in direction)
    phase = sum(p*v for p,v in zip(position,d))*frequency
    return math.sin(phase)


def transport_normal(normal, new_tangent):
    dot = sum(a*b for a,b in zip(normal,new_tangent))
    projected = [normal[i]-dot*new_tangent[i] for i in range(3)]
    length = math.sqrt(sum(v*v for v in projected))
    if length < 1e-12:
        axis = (1.0,0.0,0.0) if abs(new_tangent[0]) < 0.9 else (0.0,1.0,0.0)
        dot2 = sum(a*b for a,b in zip(axis,new_tangent))
        projected = [axis[i]-dot2*new_tangent[i] for i in range(3)]
        length = math.sqrt(sum(v*v for v in projected))
    return tuple(v/length for v in projected)


def depth_normal_edge(z0, z1, n0, n1, normal_weight):
    if normal_weight < 0:
        raise ValueError("normal_weight must be nonnegative")
    dot = sum(a*b for a,b in zip(n0,n1))
    return abs(z0-z1)+normal_weight*(1.0-max(-1.0,min(1.0,dot)))


def halftone_pattern(x, y, frequency):
    if frequency <= 0:
        raise ValueError("frequency must be positive")
    return 0.5+0.5*math.sin(math.pi*frequency*x)*math.sin(math.pi*frequency*y)


def hatch_phase(position, direction, spacing):
    length = math.sqrt(sum(v*v for v in direction))
    if length == 0 or spacing <= 0:
        raise ValueError("direction and spacing must be nonzero/positive")
    d = tuple(v/length for v in direction)
    value = sum(p*v for p,v in zip(position,d))/spacing
    return value-math.floor(value)


def sample_linear_1d(values, x):
    if x <= 0:
        return values[0]
    if x >= len(values)-1:
        return values[-1]
    i = math.floor(x)
    f = x-i
    return values[i]*(1-f)+values[i+1]*f


def semi_lagrangian_advect_1d(values, velocity, dt):
    return [sample_linear_1d(values, i-velocity*dt) for i in range(len(values))]


def boid_steering(position, velocity, neighbor_positions, neighbor_velocities):
    if not neighbor_positions:
        return (0.0,0.0)
    count=len(neighbor_positions)
    center=tuple(sum(p[k] for p in neighbor_positions)/count for k in range(2))
    avg_v=tuple(sum(v[k] for v in neighbor_velocities)/count for k in range(2))
    separation=tuple(sum(position[k]-p[k] for p in neighbor_positions)/count for k in range(2))
    alignment=tuple(avg_v[k]-velocity[k] for k in range(2))
    cohesion=tuple(center[k]-position[k] for k in range(2))
    return separation,alignment,cohesion


def greedy_rectangles(mask):
    grid=[list(row) for row in mask]
    h=len(grid); w=len(grid[0]) if h else 0
    rects=[]
    for y in range(h):
        for x in range(w):
            key=grid[y][x]
            if key is None:
                continue
            x2=x
            while x2<w and grid[y][x2]==key:
                x2+=1
            y2=y+1
            while y2<h and all(grid[y2][xx]==key for xx in range(x,x2)):
                y2+=1
            for yy in range(y,y2):
                for xx in range(x,x2):
                    grid[yy][xx]=None
            rects.append((x,y,x2,y2,key))
    return rects


def volume_composite(segments):
    trans=1.0
    radiance=0.0
    for sigma_t, density, ds, source in segments:
        mu=sigma_t*density
        alpha=1.0-math.exp(-mu*ds)
        radiance += trans*alpha*source
        trans *= 1.0-alpha
    return radiance,trans


def regularized_plane_qef(points_normals, center, regularization):
    """Solve the full 3x3 regularized Hermite QEF normal equations."""
    if regularization < 0 or not math.isfinite(regularization):
        raise ValueError("regularization must be finite and nonnegative")
    if len(center) != 3 or not all(math.isfinite(v) for v in center):
        raise ValueError("center must be a finite 3-vector")
    A=[[regularization if i==j else 0.0 for j in range(3)] for i in range(3)]
    b=[regularization*c for c in center]
    for point,normal in points_normals:
        if len(point)!=3 or len(normal)!=3 or not all(math.isfinite(v) for v in tuple(point)+tuple(normal)):
            raise ValueError("Hermite point and normal must be finite 3-vectors")
        norm=math.sqrt(sum(v*v for v in normal))
        if abs(norm-1.0)>1e-6:
            raise ValueError("Hermite normals must be unit length")
        projection=sum(normal[k]*point[k] for k in range(3))
        for i in range(3):
            b[i]+=normal[i]*projection
            for j in range(3):
                A[i][j]+=normal[i]*normal[j]
    # Gaussian elimination with partial pivoting; reject singular unregularized systems.
    for col in range(3):
        pivot=max(range(col,3),key=lambda row:abs(A[row][col]))
        if abs(A[pivot][col])<1e-12:
            raise ValueError("singular QEF; use positive regularization or SVD fallback")
        A[col],A[pivot]=A[pivot],A[col]
        b[col],b[pivot]=b[pivot],b[col]
        scale=A[col][col]
        for j in range(col,3): A[col][j]/=scale
        b[col]/=scale
        for row in range(3):
            if row==col: continue
            factor=A[row][col]
            for j in range(col,3): A[row][j]-=factor*A[col][j]
            b[row]-=factor*b[col]
    return tuple(b)


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

    def test_xpbd_compliance_scaled_by_dt_matches_closed_form(self):
        # C=1 m, sum(w)=2 kg^-1, alpha=1 s^2/kg.
        at_dt_1 = xpbd_distance_step(0.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        at_dt_half = xpbd_distance_step(0.0, 2.0, 1.0, 1.0, 1.0, 1.0, 0.5)
        self.assertAlmostEqual(at_dt_1[2], -1.0/3.0)
        self.assertAlmostEqual(at_dt_half[2], -1.0/6.0)
        self.assertAlmostEqual(at_dt_1[1]-at_dt_1[0], 4.0/3.0)
        self.assertAlmostEqual(at_dt_half[1]-at_dt_half[0], 5.0/3.0)

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


    def test_stop_motion_jitter_is_deterministic_bounded_and_channel_specific(self):
        a=deterministic_jitter(12,77,0,0.1)
        self.assertEqual(a,deterministic_jitter(12,77,0,0.1))
        self.assertGreaterEqual(a,-0.1)
        self.assertLess(a,0.1)
        self.assertNotEqual(a,deterministic_jitter(12,77,1,0.1))

    def test_hair_ggx_normal_distribution_reference(self):
        alpha=0.5
        self.assertAlmostEqual(ggx_ndf(1.0,alpha),1.0/(math.pi*alpha*alpha))
        self.assertGreater(ggx_ndf(1.0,alpha),ggx_ndf(0.0,alpha))

    def test_hair_microfacet_ggx_matches_published_appendix_a_eq41(self):
        self.assertAlmostEqual(hair_ggx_ndf(0.0, 0.5), 0.25/math.pi)
        self.assertAlmostEqual(hair_ggx_ndf(1.0, 0.5), 4.0/math.pi)
        self.assertAlmostEqual(hair_tilted_half_dot(0.0, 0.3, 0.3, 0.0), 1.0)
        with self.assertRaises(ValueError):
            hair_ggx_ndf(1.0, 0.0)

    def test_reynolds_prioritized_acceleration_allocation_closed_form(self):
        got = prioritized_acceleration_allocation([
            ((0.8, 0.0, 0.0), 1.0),
            ((0.0, 0.8, 0.0), 1.0)
        ], 1.0)
        self.assertVecAlmostEqual(got, (0.8, 0.2, 0.0))
        full = prioritized_acceleration_allocation([
            ((0.6, 0.0, 0.0), 1.0),
            ((0.0, 0.2, 0.0), 1.0)
        ], 1.0)
        self.assertVecAlmostEqual(full, (0.6, 0.2, 0.0))
        self.assertVecAlmostEqual(prioritized_acceleration_allocation([((1,0,0),0)], 2), (0,0,0))
        with self.assertRaises(ValueError):
            prioritized_acceleration_allocation([((1,0),1)], 1)

    def test_anisotropic_kuwahara_matches_published_weight_rule(self):
        # Independent closed-form fixture: s=(0,3), q=2 -> weights (1,1/10).
        self.assertAlmostEqual(anisotropic_kuwahara_mean([0.0, 10.0], [0.0, 3.0], q=2), 10.0/11.0)
        # Published example setting q=8: weights (1,1/6562).
        self.assertAlmostEqual(anisotropic_kuwahara_mean([0.0, 10.0], [0.0, 3.0]), 10.0/6563.0)
        self.assertAlmostEqual(anisotropic_kuwahara_mean([2.0, 4.0], [0.0, 0.0]), 3.0)
        with self.assertRaises(ValueError):
            anisotropic_kuwahara_mean([1.0], [-0.1])
    def test_kuwahara_weighted_sector_mean_prefers_low_variance(self):
        self.assertAlmostEqual(weighted_sector_mean([0.0,10.0],[0.0,9.0]),10.0/11.0)

    def test_impasto_height_gradient_matches_plane_coefficients(self):
        gx,gy=linear_height_gradient(2.5,-0.75,3.0,4.0)
        self.assertAlmostEqual(gx,2.5,places=8)
        self.assertAlmostEqual(gy,-0.75,places=8)

    def test_flow_oriented_noise_is_periodic_along_flow(self):
        a=oriented_periodic_noise((0.2,0.3),(1,0),2.0)
        b=oriented_periodic_noise((0.2+math.pi,0.3),(1,0),2.0)
        self.assertAlmostEqual(a,b,places=12)

    def test_camera_parallel_transport_keeps_normal_orthogonal(self):
        n=transport_normal((0,1,0),(1,0,0))
        self.assertAlmostEqual(math.sqrt(sum(v*v for v in n)),1.0)
        self.assertAlmostEqual(sum(a*b for a,b in zip(n,(1,0,0))),0.0)

    def test_depth_normal_edge_zero_for_identical_samples(self):
        n=(0.0,0.0,1.0)
        self.assertAlmostEqual(depth_normal_edge(4.0,4.0,n,n,2.0),0.0)
        self.assertGreater(depth_normal_edge(4.0,4.2,n,(0,0,-1),2.0),0.2)

    def test_halftone_pattern_has_expected_spatial_period(self):
        f=0.25
        self.assertAlmostEqual(halftone_pattern(0.3,0.7,f),halftone_pattern(0.3+2/f,0.7,f))

    def test_hatching_phase_repeats_after_one_spacing(self):
        phase=hatch_phase((0.2,0.4),(1,0),0.5)
        shifted=hatch_phase((0.7,0.4),(1,0),0.5)
        self.assertAlmostEqual(phase,shifted)

    def test_semi_lagrangian_advection_preserves_constant_field(self):
        out=semi_lagrangian_advect_1d([3.0]*8,0.75,0.2)
        self.assertVecAlmostEqual(out,[3.0]*8)

    def test_boids_components_point_toward_expected_behaviors(self):
        separation,alignment,cohesion=boid_steering((0,0),(1,0),[(1,0)],[(0,2)])
        self.assertEqual(separation,(-1.0,0.0))
        self.assertEqual(alignment,(-1.0,2.0))
        self.assertEqual(cohesion,(1.0,0.0))

    def test_greedy_voxel_meshing_merges_equal_face_rectangle(self):
        rects=greedy_rectangles([[1,1],[1,1]])
        self.assertEqual(len(rects),1)
        self.assertEqual(rects[0],(0,0,2,2,1))
        split=greedy_rectangles([[1,2],[1,2]])
        self.assertEqual(len(split),2)

    def test_volume_compositing_matches_constant_medium_transmittance(self):
        segments=[(2.0,0.5,0.25,1.0)]*4
        radiance,trans=volume_composite(segments)
        self.assertAlmostEqual(trans,math.exp(-1.0))
        self.assertAlmostEqual(radiance,1.0-trans)

    def test_dual_contouring_qef_minimizes_consistent_plane_constraints(self):
        constraints=[((0.25,0.1,0.1),(1,0,0)),((0.25,0.8,0.2),(1,0,0)),((0.25,0.3,0.9),(1,0,0))]
        x=regularized_plane_qef(constraints,(0.5,0.5,0.5),1e-6)
        self.assertAlmostEqual(x[0],0.25,places=5)




def spatial_hash_index(cell, table_size):
    if not isinstance(table_size, int) or table_size <= 0:
        raise ValueError("table_size must be a positive integer")
    if len(cell) != 3 or any(not isinstance(v, int) for v in cell):
        raise ValueError("cell must be an integer 3-vector")
    x, y, z = cell
    # Python integers avoid overflow; mask to the same uint32 domain as JS.
    mixed = ((x * 73856093) ^ (y * 19349663) ^ (z * 83492791)) & 0xffffffff
    return mixed % table_size


def blend_dual_quaternions(items):
    """Antipodal-corrected weighted blend; returns a Study-normalized pair."""
    if not items:
        raise ValueError("at least one transform is required")
    reference = None
    real = [0.0] * 4
    dual = [0.0] * 4
    weight_sum = 0.0
    for qr, qd, weight in items:
        if weight < 0 or not math.isfinite(weight) or len(qr) != 4 or len(qd) != 4:
            raise ValueError("invalid weighted dual quaternion")
        if not all(math.isfinite(v) for v in tuple(qr) + tuple(qd)):
            raise ValueError("quaternion components must be finite")
        if weight == 0:
            continue
        if reference is None:
            reference = qr
        sign = -1.0 if sum(a*b for a, b in zip(qr, reference)) < 0 else 1.0
        for i in range(4):
            real[i] += weight * sign * qr[i]
            dual[i] += weight * sign * qd[i]
        weight_sum += weight
    if weight_sum <= 0:
        raise ValueError("weight sum must be positive")
    return dual_quaternion_normalize(real, dual)

    def test_spatial_hash_matches_published_integer_cell_hash(self):
        # Teschner et al. Sec. 4.1; positive modulo maps to a table bucket.
        cell = (1, 2, 3)
        expected = ((73856093 ^ (2*19349663) ^ (3*83492791)) & 0xffffffff) % 97
        self.assertEqual(spatial_hash_index(cell, 97), expected)
        self.assertEqual(spatial_hash_index((-1, -2, -3), 97),
                         spatial_hash_index((-1, -2, -3), 97))
        with self.assertRaises(ValueError):
            spatial_hash_index((1, 2, 3), 0)

    def test_dual_quaternion_blend_antipodal_and_weight_scale_invariant(self):
        identity = ((1,0,0,0), (0,0,0,0), 0.5)
        antipodal = ((-1,0,0,0), (0,0,0,0), 0.5)
        qr, qd = blend_dual_quaternions([identity, antipodal])
        self.assertVecAlmostEqual(qr, (1,0,0,0))
        self.assertVecAlmostEqual(qd, (0,0,0,0))
        self.assertAlmostEqual(sum(a*b for a,b in zip(qr,qd)), 0.0)
        with self.assertRaises(ValueError):
            blend_dual_quaternions([((1,0,0,0),(0,0,0,0),0.0)])




    def test_schlick_fresnel_interior_value_and_monotonicity(self):
        self.assertAlmostEqual(fresnel_schlick(0.04, 0.5), 0.07)
        values=[fresnel_schlick(0.04, u/10) for u in range(11)]
        self.assertTrue(all(values[i] >= values[i+1] for i in range(10)))

    def test_beer_lambert_subdivision_invariance(self):
        whole=beer_lambert_transmittance(1.7, 2.4)
        subdivided=math.prod(beer_lambert_transmittance(1.7, 2.4/8) for _ in range(8))
        self.assertAlmostEqual(whole, subdivided, places=14)


    def test_dual_contouring_full_qef_solves_non_axis_aligned_planes(self):
        inv=1.0/math.sqrt(2.0)
        constraints=[
            ((0.5,0.5,0.0),(inv,inv,0.0)),   # x+y=1
            ((0.25,-0.25,0.0),(inv,-inv,0.0)), # x-y=.5
            ((0.0,0.0,0.4),(0.0,0.0,1.0))
        ]
        result=regularized_plane_qef(constraints,(0.5,0.5,0.5),1e-10)
        self.assertVecAlmostEqual(result,(0.75,0.25,0.4),places=6)

    def test_dual_contouring_qef_rejects_singular_unregularized_system(self):
        with self.assertRaises(ValueError):
            regularized_plane_qef([((0,0,0),(1,0,0))],(0,0,0),0.0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
