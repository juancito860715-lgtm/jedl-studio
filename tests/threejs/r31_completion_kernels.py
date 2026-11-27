"""Independent completion kernels for the four outstanding R31 records.

These are explicitly scoped mathematical prototypes. They do not claim that
the published Phasor erosion model or a complete PBR impasto model has been
reproduced. Inputs use consistent scene/world units and finite values.
"""
import math


def _finite(values, name):
    if not all(math.isfinite(float(v)) for v in values):
        raise ValueError(f"{name} must contain only finite values")


def _norm(v):
    return math.sqrt(sum(x*x for x in v))


def _unit(v, name="vector"):
    n = _norm(v)
    if n <= 1e-15:
        raise ValueError(f"{name} must be nonzero")
    return tuple(x/n for x in v)


def point_segment_distance_2d(point, a, b):
    _finite((*point, *a, *b), "coordinates")
    if len(point) != 2 or len(a) != 2 or len(b) != 2:
        raise ValueError("point and segment endpoints must be 2-vectors")
    dx, dy = b[0]-a[0], b[1]-a[1]
    den = dx*dx + dy*dy
    if den <= 1e-30:
        return math.hypot(point[0]-a[0], point[1]-a[1])
    t = max(0.0, min(1.0, ((point[0]-a[0])*dx+(point[1]-a[1])*dy)/den))
    return math.hypot(point[0]-(a[0]+t*dx), point[1]-(a[1]+t*dy))


def impasto_height(point, strokes):
    """Compact C1 radial stroke profile: a*(max(0,1-(d/r)^2))^2.

    Each stroke is (x0,y0,x1,y1,radius,amplitude). Amplitude has height units;
    radius and point coordinates share a length unit.
    """
    _finite(point, "point")
    if len(point) != 2:
        raise ValueError("point must be a 2-vector")
    height = 0.0
    for stroke in strokes:
        if len(stroke) != 6:
            raise ValueError("stroke must have six values")
        _finite(stroke, "stroke")
        x0,y0,x1,y1,radius,amplitude = stroke
        if radius <= 0:
            raise ValueError("stroke radius must be positive")
        d = point_segment_distance_2d(point, (x0,y0), (x1,y1))
        q = max(0.0, 1.0-(d/radius)**2)
        height += amplitude*q*q
    return height


def height_gradient(height_fn, point, step=1e-4):
    _finite((*point, step), "gradient inputs")
    if len(point) != 2 or step <= 0:
        raise ValueError("point must be 2D and step positive")
    x,y=point
    gx=(height_fn((x+step,y))-height_fn((x-step,y)))/(2*step)
    gy=(height_fn((x,y+step))-height_fn((x,y-step)))/(2*step)
    return gx,gy


def impasto_normal(gradient, strength=1.0):
    _finite((*gradient, strength), "normal inputs")
    if len(gradient) != 2:
        raise ValueError("gradient must be 2D")
    return _unit((-strength*gradient[0], 1.0, -strength*gradient[1]), "normal")


def oriented_periodic_detail(position, flow, frequency, anisotropy=0.8, phase=0.0):
    """Deterministic anisotropic Fourier detail, not the paper's Phasor noise."""
    _finite((*position, *flow, frequency, anisotropy, phase), "noise inputs")
    if len(position) != 2 or len(flow) != 2 or frequency <= 0 or not 0 <= anisotropy <= 1:
        raise ValueError("2D position/flow, frequency>0 and anisotropy in [0,1] required")
    f=_unit(flow, "flow")
    n=(-f[1], f[0])
    along=position[0]*f[0]+position[1]*f[1]
    across=position[0]*n[0]+position[1]*n[1]
    # Smooth, globally periodic deterministic components with stronger
    # correlation along the flow direction.
    return (anisotropy*math.sin(2*math.pi*frequency*along+phase)
            +(1-anisotropy)*math.sin(2*math.pi*frequency*4*across+phase*0.5))


def eroded_height(base_height, position, flow, amplitude, slope, frequency,
                  anisotropy=0.8, phase=0.0):
    _finite((base_height, amplitude, slope, frequency, anisotropy, phase), "erosion inputs")
    if amplitude < 0 or slope < 0:
        raise ValueError("amplitude and slope must be nonnegative")
    exposure=min(1.0, slope)
    detail=oriented_periodic_detail(position, flow, frequency, anisotropy, phase)
    return base_height + amplitude*exposure*detail


def rk4_step(field, state, time, dt):
    """Classical RK4 for dx/dt=field(x,t), with derivative-valued k stages."""
    _finite((*state, time, dt), "RK4 inputs")
    if dt == 0:
        return tuple(state)
    def add_scaled(x, k, scale):
        return tuple(a+scale*b for a,b in zip(x,k))
    def derivative(x,t):
        out=tuple(field(tuple(x),t))
        if len(out)!=len(state):
            raise ValueError("field derivative dimension mismatch")
        _finite(out, "field derivative")
        return out
    k1=derivative(state,time)
    k2=derivative(add_scaled(state,k1,dt/2),time+dt/2)
    k3=derivative(add_scaled(state,k2,dt/2),time+dt/2)
    k4=derivative(add_scaled(state,k3,dt),time+dt)
    result=tuple(state[i]+dt*(k1[i]+2*k2[i]+2*k3[i]+k4[i])/6 for i in range(len(state)))
    _finite(result, "RK4 result")
    return result


def integrate_rk4(field, initial_state, start_time, end_time, steps):
    if not isinstance(steps,int) or steps <= 0 or not math.isfinite(start_time) or not math.isfinite(end_time):
        raise ValueError("steps must be a positive integer and times finite")
    state=tuple(initial_state)
    _finite(state, "initial state")
    dt=(end_time-start_time)/steps
    t=start_time
    for _ in range(steps):
        state=rk4_step(field,state,t,dt)
        t+=dt
    return state


def greedy_rectangles(mask):
    """Deterministic row-major greedy merge of equal non-empty face keys."""
    if not isinstance(mask,(list,tuple)) or not mask:
        raise ValueError("mask must be a nonempty rectangular grid")
    width=len(mask[0])
    if width == 0 or any(len(row)!=width for row in mask):
        raise ValueError("mask must be rectangular and nonempty")
    grid=[list(row) for row in mask]
    height=len(grid)
    rects=[]
    for y in range(height):
        for x in range(width):
            key=grid[y][x]
            if key is None:
                continue
            x2=x+1
            while x2<width and grid[y][x2]==key:
                x2+=1
            y2=y+1
            while y2<height and all(grid[y2][xx]==key for xx in range(x,x2)):
                y2+=1
            for yy in range(y,y2):
                for xx in range(x,x2):
                    grid[yy][xx]=None
            rects.append((x,y,x2,y2,key))
    return rects
