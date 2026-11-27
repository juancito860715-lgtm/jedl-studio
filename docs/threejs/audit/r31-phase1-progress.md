# R31 phase 1 — implementation progress

Status: **IN PROGRESS — NOT CERTIFIED**

This record tracks the four R31 gaps separately. A green CPU workflow proves that the committed tests passed; it does not, by itself, prove equivalence to every cited paper or runtime GPU execution.

## Current implementation

### 1. Layered impasto brush relief
- Module: `src/threejs/r31-algorithms.mjs`
- Scene: `examples/threejs/r31-validation-scenes.mjs`
- Implementation: seeded low-discrepancy candidate set with farthest-point selection as a discrete approximation to an incremental Voronoi sequence; coarse-to-fine brush layers; supplied tangent-field streamline integration; configurable brush-height profile; heightfield triangulated into Three.js BufferGeometry.
- Primary source: Chen et al., *Layered Oil Painting Stylization with Multi-Scale Brushes*, Journal of Computer-Aided Design & Computer Graphics 32(4), 2020, DOI 10.3724/SP.J.1089.2020.17954.
- Source-supported requirements: large-to-small brush layers; incremental Voronoi sampling with farthest-point selection; structure-tensor tangent direction field; constrained brush streamline; brush shape and height-field texture mapping.
- Still open: implement image-gradient/Sobel and structure-tensor construction as an input pipeline; continuity-aware streamline curvature/length/coverage constraints from the full method; actual brush texture/height-field rasterization and layered canvas accumulation. Current heightfield is a 3D procedural proxy, not the complete image stylization renderer.

### 2. Flow-oriented Phasor erosion
- Module: `src/threejs/r31-algorithms.mjs`
- Scene: `examples/threejs/r31-validation-scenes.mjs`
- Implementation: deterministic finite spectral complex field with Gaussian coefficients, phase extraction, periodic transverse profile, regularization, and terrain-height sampling.
- Primary source: Grenier et al., *Real-time Terrain Enhancement with Controlled Procedural Patterns*, Computer Graphics Forum 43(1), 2024, DOI 10.1111/cgf.14992.
- Source-supported requirements: Phasor profile composed with phase of a complex Gaussian field; spatial maps for amplitude, frequency/spacing and orientation; adaptation to terrain height/gradient; cascaded patterns; radial regularization for phase singularities.
- Still open: match the paper's specified sparse-convolution Gaussian-field construction and profile/transfer functions; derive spatial control maps from terrain altitude and gradient rather than fixed scene controls; implement recursive cascades and shading derivatives; verify flow-coherence metric against the paper. The current finite spectral field is a CPU approximation, not claimed as an exact reproduction.

### 3. Vector-field trajectories with RK4
- Module: `src/threejs/r31-algorithms.mjs`
- Scene: `examples/threejs/r31-validation-scenes.mjs`
- Implementation: classical fixed-step RK4 for arbitrary finite-dimensional vector fields; emits every trajectory sample and feeds a Three.js Line/BufferGeometry.
- Mathematical oracle: analytic unit circular flow, constant vector field, reverse-time integration, and fourth-order error reduction.
- Still open: map the R31 source's full time/space semantics and units; integrate into the project's particle/trajectory update lifecycle, including per-particle state, bounds, termination and frame-delta policy; compare against an independent high-precision reference over the specified vector-field test suite.

### 4. 3D greedy voxel meshing
- Module: `src/threejs/r31-algorithms.mjs`
- Scene: `examples/threejs/r31-validation-scenes.mjs`
- Implementation: axis-sweep over all three dimensions and both face directions; 2D slice masks; greedy rectangle fusion by face merge key; preserves material interfaces; emits quads converted into indexed Three.js BufferGeometry with vertex colors and computed normals.
- Primary implementation reference: Mikola Lysenko, `greedy-mesher`, with configurable skip/merge/append behavior; see https://github.com/mikolalysenko/greedy-mesher and https://0fps.wordpress.com/2012/06/30/meshing-in-a-minecraft-game/.
- Still open: extend face key to include UV/material atlas, lighting/AO, transparency and per-face metadata from the project voxel schema; add winding/normal and watertightness checks for all axes, sparse/random volumes, chunk borders and negative world coordinates; connect the mesher to the project's actual voxel data lifecycle and disposal/rebuild policy.

## Test evidence

- Python numerical suite: 81 passed in workflow run 120.
- JavaScript/Three.js suite: 72 passed in workflow run 120.
- Structural audit and fail-closed readiness gate: passed in workflow run 120.
- Workflow run: https://github.com/juancito860715-lgtm/jedl-studio/actions/runs/45923663346
- Tested commit: `20b6ae7c1d51a19337e13fe71d9bf8d034a9c653`

## Exit criteria for phase 1

Do not mark this phase complete until each of the four sections above has:
1. A source-mapped derivation and explicit assumptions/domain/units.
2. A production implementation connected to its real Three.js runtime lifecycle.
3. Independent mathematical oracle tests, including adversarial and boundary cases.
4. Reproducible scene evidence for representative and edge cases.
5. A passing full workflow on the final phase-1 commit.

The current state has useful working implementations and passing CPU tests, but does not yet satisfy every exit criterion.
