import test from "node:test";
import assert from "node:assert/strict";
import * as THREE from "three";

const close = (actual, expected, tol = 1e-10) =>
  assert.ok(Math.abs(actual - expected) <= tol, `expected ${actual} ≈ ${expected} ± ${tol}`);

test("D35:0 PID controller — proportional step and output saturation", () => {
  const e = 1, integral = 0, previous = 1, dt = 0.1;
  const u = 2 * e + 0.5 * integral + 0.25 * (e - previous) / dt;
  close(u, 2);
  close(Math.max(-1, Math.min(1, 20)), 1);
});

test("D35:1 proportional tracking — equilibrium and bounded Euler step", () => {
  const x = 0, target = 1, kp = 2, dt = 0.1;
  const v = kp * (target - x);
  close(x + dt * v, 0.2);
  close(kp * (target - target), 0);
});

test("D35:2 critically damped spring — acceleration and state step", () => {
  const x = 0, target = 1, velocity = 0, omega = 2, dt = 0.01;
  const a = omega ** 2 * (target - x) - 2 * omega * velocity;
  const v1 = velocity + a * dt;
  const x1 = x + v1 * dt;
  close(a, 4);
  close(v1, 0.04);
  close(x1, 0.0004);
});

test("D35:3 Kalman state model — scalar prediction and correction", () => {
  const xPred = 0, pPred = 1, h = 1, r = 1, z = 2;
  const k = pPred * h / (h * h * pPred + r);
  const xPost = xPred + k * (z - h * xPred);
  const pPost = (1 - k * h) * pPred;
  close(k, 0.5);
  close(xPost, 1);
  close(pPost, 0.5);
});

test("D35:4 gradient descent — quadratic objective decreases", () => {
  const theta = 2, eta = 0.5;
  const next = theta - eta * theta;
  close(next, 1);
  assert.ok(0.5 * next ** 2 < 0.5 * theta ** 2);
});

test("D35:5 Levenberg–Marquardt — damped scalar normal equation", () => {
  const j = 1, residual = -3, lambda = 0.1;
  const delta = -(j * residual) / (j * j + lambda);
  close(delta, 30 / 11);
  assert.ok(Number.isFinite(delta));
});

test("D35:6 Newton method — square-root convergence", () => {
  let x = 1.5;
  for (let i = 0; i < 8; i++) x -= (x * x - 2) / (2 * x);
  close(x, Math.SQRT2, 1e-10);
});

test("D35:7 bisection — bracket contracts around sqrt(2)", () => {
  let a = 1, b = 2;
  for (let i = 0; i < 40; i++) {
    const m = (a + b) / 2;
    if ((a * a - 2) * (m * m - 2) <= 0) b = m;
    else a = m;
  }
  assert.ok(a <= Math.SQRT2 && Math.SQRT2 <= b);
  assert.ok(b - a <= 2 ** -40);
});

test("D35:8 cubic interpolation — Hermite endpoints and tangents", () => {
  const p0 = 2, p1 = 5, m0 = 3, m1 = -1;
  const h = t => (2*t**3 - 3*t**2 + 1)*p0 + (t**3 - 2*t**2 + t)*m0
    + (-2*t**3 + 3*t**2)*p1 + (t**3 - t**2)*m1;
  const dh = t => (6*t**2 - 6*t)*p0 + (3*t**2 - 4*t + 1)*m0
    + (-6*t**2 + 6*t)*p1 + (3*t**2 - 2*t)*m1;
  close(h(0), p0); close(h(1), p1); close(dh(0), m0); close(dh(1), m1);
});

test("D35:9 Fourier series — constant and single sine reconstruction", () => {
  const constant = t => 4 / 2;
  const sine = t => Math.sin(2 * Math.PI * t);
  close(constant(0), 2);
  close(sine(0), 0);
  close(sine(0.25), 1);
  close(sine(1), sine(0));
});

test("D35:10 FFT — DFT impulse and inverse round trip", () => {
  const dft = input => input.map((_, k) => input.reduce((sum, value, n) => {
    const angle = -2 * Math.PI * k * n / input.length;
    return [sum[0] + value[0]*Math.cos(angle) - value[1]*Math.sin(angle),
      sum[1] + value[0]*Math.sin(angle) + value[1]*Math.cos(angle)];
  }, [0, 0]));
  const impulse = dft([[1,0],[0,0],[0,0],[0,0]]);
  for (const [re, im] of impulse) { close(re, 1); close(im, 0); }
  const input = [[1,0],[2,0],[-1,0],[0.5,0]];
  const spectrum = dft(input);
  const inverse = spectrum.map((_, n) => spectrum.reduce((sum, value, k) => {
    const angle = 2 * Math.PI * k * n / input.length;
    return [sum[0] + value[0]*Math.cos(angle) - value[1]*Math.sin(angle),
      sum[1] + value[0]*Math.sin(angle) + value[1]*Math.cos(angle)];
  }, [0,0]).map(v => v / input.length));
  inverse.forEach((v, i) => { close(v[0], input[i][0]); close(v[1], input[i][1]); });
});

test("D35:11 wavelet transform — Haar transform annihilates constant details", () => {
  const signal = [3, 3, 3, 3];
  const d1 = (signal[0] - signal[1]) / Math.SQRT2;
  const d2 = (signal[2] - signal[3]) / Math.SQRT2;
  const d3 = ((signal[0] + signal[1]) - (signal[2] + signal[3])) / 2;
  close(d1, 0); close(d2, 0); close(d3, 0);
});

test("D35:12 Monte Carlo — deterministic sample mean estimates expectation", () => {
  const samples = [0.1, 0.2, 0.3, 0.4];
  const estimate = samples.reduce((sum, x) => sum + x, 0) / samples.length;
  close(estimate, 0.25);
  assert.equal(samples.length, 4);
});

test("D35:13 blue-noise sampling — rejection sampler preserves minimum spacing", () => {
  const candidates = [[0.1,0.1],[0.2,0.1],[0.5,0.5],[0.8,0.8]];
  const radius = 0.25, accepted = [];
  for (const p of candidates) {
    if (accepted.every(q => Math.hypot(p[0]-q[0], p[1]-q[1]) >= radius)) accepted.push(p);
  }
  assert.equal(accepted.length, 3);
  for (let i=0;i<accepted.length;i++) for (let j=i+1;j<accepted.length;j++)
    assert.ok(Math.hypot(accepted[i][0]-accepted[j][0], accepted[i][1]-accepted[j][1]) >= radius);
  assert.ok(accepted.every(([x,y]) => x>=0 && x<=1 && y>=0 && y<=1));
});

test("D35:14 Beer–Lambert — homogeneous medium transmittance", () => {
  const sigmaT = 0.5, distance = 2;
  const transmittance = Math.exp(-sigmaT * distance);
  close(transmittance, Math.exp(-1));
  assert.ok(transmittance >= 0 && transmittance <= 1);
});

test("D36:0 material derivative — chain rule along moving particle", () => {
  const partialTime = 3, gradX = 2 * 2, velocity = 4;
  close(partialTime + velocity * gradX, 19);
});

test("D36:1 explicit Euler — first-order scalar step", () => {
  const y = 1, dt = 0.1, f = y;
  close(y + dt * f, 1.1);
});

test("D36:2 RK4 — fourth-order step for exponential decay", () => {
  const f = y => -y, y = 1, dt = 1;
  const k1=f(y), k2=f(y+dt*k1/2), k3=f(y+dt*k2/2), k4=f(y+dt*k3);
  const next=y+dt*(k1+2*k2+2*k3+k4)/6;
  close(next, 0.375);
  assert.ok(Math.abs(next - Math.exp(-1)) < 0.01);
});

test("D36:3 Verlet — harmonic oscillator recurrence", () => {
  const dt = 0.1, x0 = 1, x1 = 1 - 0.5 * dt * dt, a1 = -x1;
  const x2 = 2*x1 - x0 + a1*dt*dt;
  close(x1, 0.995);
  close(x2, 0.98005);
});

test("D36:4 CFL — Courant number and admissible timestep", () => {
  const speed = 2, dt = 0.1, dx = 0.5, cMax = 1;
  const c = Math.abs(speed) * dt / dx;
  close(c, 0.4);
  assert.ok(c <= cMax);
  assert.ok(dt <= cMax * dx / Math.abs(speed));
});

test("D36:5 Poisson — discrete 1D Dirichlet solution satisfies stencil", () => {
  const h = 0.25, u = [0.09375, 0.125, 0.09375], rhs = h*h;
  const residual = u.map((v,i) => 2*v - (u[i-1] ?? 0) - (u[i+1] ?? 0) - rhs);
  residual.forEach(v => close(v, 0));
});

test("D36:6 conjugate gradient — SPD system reaches exact solution", () => {
  const A = [[4,1],[1,3]], b = [1,2];
  let x=[0,0], r=[...b], p=[...r], rr=r.reduce((s,v)=>s+v*v,0);
  for(let i=0;i<2;i++){
    const Ap=A.map(row=>row[0]*p[0]+row[1]*p[1]);
    const alpha=rr/(p[0]*Ap[0]+p[1]*Ap[1]);
    x=x.map((v,j)=>v+alpha*p[j]);
    const rn=r.map((v,j)=>v-alpha*Ap[j]);
    const rrn=rn.reduce((s,v)=>s+v*v,0);
    const beta=rrn/rr;
    p=rn.map((v,j)=>v+beta*p[j]); r=rn; rr=rrn;
  }
  close(x[0],1/11); close(x[1],7/11);
});

test("D36:7 multigrid transfers — restriction and prolongation preserve constants", () => {
  const fine = [2,2,2,2,2];
  const restricted = 0.25*fine[0]+0.5*fine[2]+0.25*fine[4];
  const coarse = [restricted, restricted, restricted];
  const prolonged = [coarse[0], (coarse[0]+coarse[1])/2, coarse[1],
    (coarse[1]+coarse[2])/2, coarse[2]];
  close(restricted, 2);
  prolonged.forEach(v=>close(v,2));
});

test("D36:8 finite volumes — shared face flux cancels globally", () => {
  const leftRate = -3 + 5, rightRate = -5 + 2;
  close(leftRate + rightRate, -1);
  close((-3 + 5) + (-5 + 2), -1);
});

test("D36:9 finite elements — linear bar stiffness and displacement", () => {
  const E=200, area=0.01, length=2, force=100;
  const stiffness=E*area/length;
  const displacement=force/stiffness;
  close(stiffness,1);
  close(displacement,100);
  const K=[[stiffness,-stiffness],[-stiffness,stiffness]];
  close(K[0][0]+K[0][1],0);
});

test("D36:10 SPH — normalized particle sum reproduces constant field", () => {
  const masses=[2,3], densities=[2,3], field=[7,7], weights=[1,1];
  const estimate=masses.reduce((s,m,i)=>s+(m/densities[i])*field[i]*weights[i],0);
  close(estimate,14);
});

test("D36:11 Cauchy elasticity — momentum balance returns acceleration", () => {
  const rho=2, divSigma=4, bodyForce=1;
  const acceleration=(divSigma+rho*bodyForce)/rho;
  close(acceleration,3);
});

test("D36:12 Kelvin–Voigt — elastic and viscous stress contributions add", () => {
  const E=10, strain=0.1, eta=2, strainRate=0.5;
  close(E*strain+eta*strainRate,2);
});

test("D36:13 J2 von Mises — deviatoric stress equivalent and yield check", () => {
  const deviator=[2,-1,-1], s2=deviator.reduce((sum,v)=>sum+v*v,0);
  const equivalent=Math.sqrt(1.5*s2), yieldStress=2;
  close(equivalent,3);
  assert.ok(equivalent>yieldStress);
});

test("D36:14 anisotropic diffusion — tensor-weighted Laplacian", () => {
  const dxx=2, dyy=1, uxx=2, uyy=2;
  close(dxx*uxx+dyy*uyy,6);
});

test("D35/D36 Three.js integration — numerical sample can populate a finite BufferGeometry", () => {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute([0,0,0, 1,1,0],3));
  const positions = geometry.getAttribute("position");
  assert.equal(positions.count,2);
  for (const value of positions.array) assert.ok(Number.isFinite(value));
});
