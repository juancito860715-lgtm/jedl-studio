import * as THREE from "three";
import { MarchingCubes } from "three/addons/objects/MarchingCubes.js";

const finite = (n, label) => {
  if (!Number.isFinite(n)) throw new RangeError(label + " must be finite");
  return n;
};
const positiveInt = (n, label, min = 1) => {
  if (!Number.isInteger(n) || n < min) throw new RangeError(label + " must be an integer >= " + min);
  return n;
};

export function createPrimitiveGeometry(kind, options = {}) {
  const constructors = {
    box: () => new THREE.BoxGeometry(options.width ?? 1, options.height ?? 1, options.depth ?? 1,
      options.widthSegments ?? 1, options.heightSegments ?? 1, options.depthSegments ?? 1),
    sphere: () => new THREE.SphereGeometry(options.radius ?? 1, options.widthSegments ?? 32, options.heightSegments ?? 16),
    cylinder: () => new THREE.CylinderGeometry(options.radiusTop ?? 1, options.radiusBottom ?? 1,
      options.height ?? 1, options.radialSegments ?? 32, options.heightSegments ?? 1, options.openEnded ?? false),
    torus: () => new THREE.TorusGeometry(options.radius ?? 1, options.tube ?? 0.4,
      options.radialSegments ?? 12, options.tubularSegments ?? 48)
  };
  if (!constructors[kind]) throw new RangeError("unsupported primitive: " + kind);
  const geometry = constructors[kind]();
  const position = geometry.getAttribute("position");
  for (let i = 0; i < position.count; i++) {
    if (![position.getX(i), position.getY(i), position.getZ(i)].every(Number.isFinite)) {
      geometry.dispose(); throw new Error("primitive generated a non-finite vertex");
    }
  }
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  return geometry;
}

export function createValidatedBufferGeometry({ positions, indices = null, normals = null, uvs = null }) {
  if (!Array.isArray(positions) && !ArrayBuffer.isView(positions)) throw new TypeError("positions must be an array or typed array");
  if (positions.length === 0 || positions.length % 3 !== 0 || !Array.from(positions).every(Number.isFinite)) {
    throw new RangeError("positions must contain finite xyz triples");
  }
  const vertexCount = positions.length / 3;
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  if (normals) {
    if (normals.length !== vertexCount * 3 || !Array.from(normals).every(Number.isFinite)) throw new RangeError("normals must match vertex count");
    geometry.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
  }
  if (uvs) {
    if (uvs.length !== vertexCount * 2 || !Array.from(uvs).every(Number.isFinite)) throw new RangeError("uvs must match vertex count");
    geometry.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
  }
  if (indices) {
    if (indices.length % 3 !== 0 || !Array.from(indices).every(i => Number.isInteger(i) && i >= 0 && i < vertexCount)) {
      geometry.dispose(); throw new RangeError("indices must be valid triangle triples");
    }
    geometry.setIndex(Array.from(indices));
  } else if (vertexCount % 3 !== 0) {
    geometry.dispose(); throw new RangeError("non-indexed triangle positions must be a multiple of three vertices");
  }
  if (!normals) geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  return geometry;
}

export function createParametricSurface(surface, slices = 32, stacks = 16) {
  if (typeof surface !== "function") throw new TypeError("surface must be a function");
  positiveInt(slices, "slices"); positiveInt(stacks, "stacks");
  const positions = [], uvs = [], indices = [];
  for (let j = 0; j <= stacks; j++) {
    const v = j / stacks;
    for (let i = 0; i <= slices; i++) {
      const u = i / slices;
      const p = surface(u, v, new THREE.Vector3());
      if (!p || ![p.x, p.y, p.z].every(Number.isFinite)) throw new RangeError("surface returned a non-finite Vector3");
      positions.push(p.x, p.y, p.z); uvs.push(u, v);
    }
  }
  const row = slices + 1;
  for (let j = 0; j < stacks; j++) for (let i = 0; i < slices; i++) {
    const a = j * row + i, b = a + row;
    indices.push(a, b, a + 1, b, b + 1, a + 1);
  }
  return createValidatedBufferGeometry({ positions, indices, uvs });
}

export function createRevolutionSurface(profile, radialSegments = 32) {
  if (!Array.isArray(profile) || profile.length < 2) throw new RangeError("profile requires at least two [radius,y] points");
  positiveInt(radialSegments, "radialSegments", 3);
  const positions = [], uvs = [], indices = [];
  profile.forEach((p, i) => {
    if (!Array.isArray(p) || p.length !== 2 || !p.every(Number.isFinite) || p[0] < 0) throw new RangeError("profile radius must be finite and nonnegative");
    for (let j = 0; j <= radialSegments; j++) {
      const theta = 2 * Math.PI * j / radialSegments;
      positions.push(p[0] * Math.cos(theta), p[1], p[0] * Math.sin(theta));
      uvs.push(j / radialSegments, i / (profile.length - 1));
    }
  });
  for (let i = 0; i < profile.length - 1; i++) for (let j = 0; j < radialSegments; j++) {
    const a = i * (radialSegments + 1) + j, b = a + radialSegments + 1;
    indices.push(a, a + 1, b, a + 1, b + 1, b);
  }
  return createValidatedBufferGeometry({ positions, indices, uvs });
}

export function createExtrusionGeometry(contour, depth, steps = 1) {
  finite(depth, "depth");
  positiveInt(steps, "steps");
  if (!Array.isArray(contour) || contour.length < 3) throw new RangeError("contour requires at least three 2D points");
  const shape = new THREE.Shape();
  contour.forEach((p, i) => {
    if (!Array.isArray(p) || p.length !== 2 || !p.every(Number.isFinite)) throw new RangeError("contour points must be finite xy pairs");
    if (i === 0) shape.moveTo(p[0], p[1]); else shape.lineTo(p[0], p[1]);
  });
  shape.closePath();
  const geometry = new THREE.ExtrudeGeometry(shape, { depth, steps, bevelEnabled: false, curveSegments: 1 });
  geometry.computeBoundingBox(); geometry.computeBoundingSphere();
  return geometry;
}

function tangentAt(points, i) {
  const a = points[Math.max(0, i - 1)], b = points[Math.min(points.length - 1, i + 1)];
  const t = b.clone().sub(a);
  if (t.lengthSq() < 1e-16) throw new RangeError("sweep path contains a zero tangent");
  return t.normalize();
}
function initialNormal(tangent) {
  const axis = Math.abs(tangent.x) < Math.abs(tangent.y)
    ? (Math.abs(tangent.x) < Math.abs(tangent.z) ? new THREE.Vector3(1,0,0) : new THREE.Vector3(0,0,1))
    : (Math.abs(tangent.y) < Math.abs(tangent.z) ? new THREE.Vector3(0,1,0) : new THREE.Vector3(0,0,1));
  return axis.addScaledVector(tangent, -axis.dot(tangent)).normalize();
}
export function createParallelTransportSweep(pointsInput, radius = 0.1, radialSegments = 8) {
  if (!Array.isArray(pointsInput) || pointsInput.length < 2) throw new RangeError("sweep requires at least two points");
  if (!(Number.isFinite(radius) && radius > 0)) throw new RangeError("radius must be positive");
  positiveInt(radialSegments, "radialSegments", 3);
  const points = pointsInput.map(p => {
    const v = p instanceof THREE.Vector3 ? p.clone() : new THREE.Vector3(...p);
    if (![v.x,v.y,v.z].every(Number.isFinite)) throw new RangeError("path point must be finite");
    return v;
  });
  const tangents = points.map((_, i) => tangentAt(points, i));
  const normals = [initialNormal(tangents[0])], binormals = [new THREE.Vector3().crossVectors(tangents[0], normals[0]).normalize()];
  for (let i = 1; i < points.length; i++) {
    const prev = tangents[i - 1], curr = tangents[i];
    const q = new THREE.Quaternion().setFromUnitVectors(prev, curr);
    const n = normals[i - 1].clone().applyQuaternion(q);
    n.addScaledVector(curr, -n.dot(curr)).normalize();
    normals.push(n);
    binormals.push(new THREE.Vector3().crossVectors(curr, n).normalize());
  }
  const positions = [], uvs = [], indices = [];
  for (let i = 0; i < points.length; i++) for (let j = 0; j <= radialSegments; j++) {
    const theta = 2 * Math.PI * j / radialSegments;
    const p = points[i].clone()
      .addScaledVector(normals[i], radius * Math.cos(theta))
      .addScaledVector(binormals[i], radius * Math.sin(theta));
    positions.push(p.x,p.y,p.z); uvs.push(j/radialSegments,i/(points.length-1));
  }
  for (let i = 0; i < points.length - 1; i++) for (let j = 0; j < radialSegments; j++) {
    const a = i * (radialSegments + 1) + j, b = a + radialSegments + 1;
    indices.push(a,b,a+1,a+1,b,b+1);
  }
  return createValidatedBufferGeometry({ positions, indices, uvs });
}

export function loopSubdivideGeometry(input) {
  if (!(input instanceof THREE.BufferGeometry)) throw new TypeError("BufferGeometry required");
  const position = input.getAttribute("position"), index = input.getIndex();
  if (!position || !index || index.count % 3 !== 0) throw new RangeError("indexed triangle geometry required");
  const count = position.count, faces = [];
  const edgeFaces = new Map(), neighbors = Array.from({length:count},()=>new Set());
  const edgeKey = (a,b) => a < b ? a + ":" + b : b + ":" + a;
  const addEdge = (a,b,opposite) => {
    const key=edgeKey(a,b); if(!edgeFaces.has(key)) edgeFaces.set(key,{a:Math.min(a,b),b:Math.max(a,b),opposite:[]});
    edgeFaces.get(key).opposite.push(opposite); neighbors[a].add(b); neighbors[b].add(a);
  };
  for(let i=0;i<index.count;i+=3){
    const a=index.getX(i),b=index.getX(i+1),c=index.getX(i+2);
    faces.push([a,b,c]); addEdge(a,b,c); addEdge(b,c,a); addEdge(c,a,b);
  }
  for(const edge of edgeFaces.values()) if(edge.opposite.length>2) throw new RangeError("non-manifold edge");
  const old = Array.from({length:count},(_,i)=>new THREE.Vector3().fromBufferAttribute(position,i));
  const boundaryNeighbors=Array.from({length:count},()=>[]);
  for(const e of edgeFaces.values()) if(e.opposite.length===1){boundaryNeighbors[e.a].push(e.b);boundaryNeighbors[e.b].push(e.a);}
  const next = old.map((v,i)=>{
    const boundary=boundaryNeighbors[i];
    if(boundary.length){
      if(boundary.length!==2) throw new RangeError("boundary vertex must have exactly two boundary neighbors");
      return v.clone().multiplyScalar(0.75).addScaledVector(old[boundary[0]],0.125).addScaledVector(old[boundary[1]],0.125);
    }
    const ns=[...neighbors[i]], n=ns.length;
    if(n<3) throw new RangeError("interior vertex valence must be at least three");
    const beta=n===3?3/16:3/(8*n);
    const result=v.clone().multiplyScalar(1-n*beta);
    for(const k of ns) result.addScaledVector(old[k],beta);
    return result;
  });
  const edgeIndex=new Map();
  for(const [key,e] of edgeFaces){
    const p=e.opposite.length===1
      ? old[e.a].clone().add(old[e.b]).multiplyScalar(0.5)
      : old[e.a].clone().add(old[e.b]).multiplyScalar(3/8).addScaledVector(old[e.opposite[0]],1/8).addScaledVector(old[e.opposite[1]],1/8);
    edgeIndex.set(key,next.length); next.push(p);
  }
  const out=[];
  for(const [a,b,c] of faces){
    const ab=edgeIndex.get(edgeKey(a,b)),bc=edgeIndex.get(edgeKey(b,c)),ca=edgeIndex.get(edgeKey(c,a));
    out.push(a,ab,ca,b,bc,ab,c,ca,bc,ab,bc,ca);
  }
  const positions=next.flatMap(v=>[v.x,v.y,v.z]);
  return createValidatedBufferGeometry({positions,indices:out});
}

export function generateFractalBranches({ origin = [0,0,0], direction = [0,1,0], length = 1, depth = 4, branchAngle = Math.PI/5, shrink = 0.7, seed = 1 } = {}) {
  positiveInt(depth,"depth",0);
  if(!(Number.isFinite(length)&&length>0) || !(shrink>0&&shrink<1) || !Number.isFinite(branchAngle)) throw new RangeError("invalid fractal parameters");
  const start=new THREE.Vector3(...origin), dir=new THREE.Vector3(...direction).normalize();
  if(dir.lengthSq()<1e-12) throw new RangeError("direction must be nonzero");
  const segments=[];
  function visit(a,d,len,level,phase){
    const b=a.clone().addScaledVector(d,len);
    segments.push({start:a.clone(),end:b.clone(),level});
    if(level===0)return;
    const side=initialNormal(d), binormal=new THREE.Vector3().crossVectors(d,side).normalize();
    const jitter=((Math.sin((seed+level*17+phase*31)*12.9898)*43758.5453)%1)*0.08;
    for(let k=0;k<2;k++){
      const sign=k===0?-1:1;
      const childDir=d.clone().multiplyScalar(Math.cos(branchAngle+jitter))
        .addScaledVector(side,sign*Math.sin(branchAngle+jitter)).addScaledVector(binormal,0.08*(phase%2?1:-1)).normalize();
      visit(b,childDir,len*shrink,level-1,phase*2+k+1);
    }
  }
  visit(start,dir,length,depth,0);
  return segments;
}

export function createMarchingCubes(resolution = 24, material = new THREE.MeshNormalMaterial(), balls = [[0.5,0.5,0.5,1,12]]) {
  positiveInt(resolution,"resolution",8);
  if(!Array.isArray(balls)) throw new TypeError("balls must be an array");
  const mesh=new MarchingCubes(resolution,material,false,false,Math.max(1000,resolution**3*5));
  for(const ball of balls){
    if(!Array.isArray(ball)||ball.length!==5||!ball.every(Number.isFinite)||ball[3]<=0||ball[4]<=0) throw new RangeError("each ball is [x,y,z,strength,subtract]");
    mesh.addBall(...ball);
  }
  mesh.update();
  return mesh;
}

function hashNoise(seed, frame, index, axis) {
  const x=Math.sin(seed*127.1+frame*311.7+index*74.7+axis*19.19)*43758.5453123;
  return (x-Math.floor(x))*2-1;
}
export function applyDeterministicMicroJitter(geometry, amplitude = 0.01, frame = 0, seed = 1) {
  if(!(geometry instanceof THREE.BufferGeometry)) throw new TypeError("BufferGeometry required");
  if(!(Number.isFinite(amplitude)&&amplitude>=0)||!Number.isInteger(frame)||!Number.isFinite(seed)) throw new RangeError("invalid jitter parameters");
  const source=geometry.getAttribute("position");
  if(!source) throw new RangeError("geometry has no position attribute");
  const result=geometry.clone(), target=result.getAttribute("position");
  for(let i=0;i<source.count;i++){
    target.setXYZ(i,
      source.getX(i)+amplitude*hashNoise(seed,frame,i,0),
      source.getY(i)+amplitude*hashNoise(seed,frame,i,1),
      source.getZ(i)+amplitude*hashNoise(seed,frame,i,2));
  }
  target.needsUpdate=true; result.computeVertexNormals(); result.computeBoundingBox(); result.computeBoundingSphere();
  return result;
}
