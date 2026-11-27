import * as THREE from "three";
import { MarchingCubes } from "three/addons/objects/MarchingCubes.js";

const finite = (values,label) => { if(!values.every(Number.isFinite)) throw new RangeError(label+" must be finite"); };
const EPS=1e-10;

export function evaluateSmoothUnionSdf(fields, point, smoothness=0) {
  if(!Array.isArray(fields)||fields.length===0||fields.some(f=>typeof f!=="function")) throw new TypeError("one or more SDF functions required");
  if(!(Number.isFinite(smoothness)&&smoothness>=0)) throw new RangeError("smoothness must be finite and nonnegative");
  const p=point instanceof THREE.Vector3?point:new THREE.Vector3(...point);
  let d=fields[0](p.clone());
  if(!Number.isFinite(d)) throw new RangeError("SDF returned non-finite distance");
  for(let i=1;i<fields.length;i++){
    const b=fields[i](p.clone());
    if(!Number.isFinite(b)) throw new RangeError("SDF returned non-finite distance");
    if(smoothness===0) d=Math.min(d,b);
    else {
      const h=Math.max(smoothness-Math.abs(d-b),0)/smoothness;
      d=Math.min(d,b)-smoothness*h*h*0.25;
    }
  }
  return d;
}

function createIsosurfaceMesh({bounds,resolution=24,field,iso=0,material=new THREE.MeshNormalMaterial(),maxPolyCount=30000}={}) {
  if(!Array.isArray(bounds)||bounds.length!==6||!bounds.every(Number.isFinite)||
    !(bounds[3]>bounds[0]&&bounds[4]>bounds[1]&&bounds[5]>bounds[2])) throw new RangeError("bounds must be [minX,minY,minZ,maxX,maxY,maxZ]");
  if(!Number.isInteger(resolution)||resolution<8||resolution>64) throw new RangeError("resolution must be an integer in [8,64]");
  if(typeof field!=="function"||!Number.isFinite(iso)) throw new TypeError("field and finite iso required");
  const mesh=new MarchingCubes(resolution,material,false,false,maxPolyCount);
  mesh.isolation=iso;
  const n=mesh.size, half=mesh.halfsize;
  for(let z=0;z<n;z++) for(let y=0;y<n;y++) for(let x=0;x<n;x++){
    const p=[
      (bounds[0]+bounds[3])/2+((x-half)/half)*(bounds[3]-bounds[0])/2,
      (bounds[1]+bounds[4])/2+((y-half)/half)*(bounds[4]-bounds[1])/2,
      (bounds[2]+bounds[5])/2+((z-half)/half)*(bounds[5]-bounds[2])/2
    ];
    const value=field(new THREE.Vector3(...p));
    if(!Number.isFinite(value)) throw new RangeError("scalar field returned non-finite value");
    mesh.field[z*n*n+y*n+x]=value;
  }
  mesh.update();
  const center=new THREE.Vector3((bounds[0]+bounds[3])/2,(bounds[1]+bounds[4])/2,(bounds[2]+bounds[5])/2);
  const scale=new THREE.Vector3((bounds[3]-bounds[0])/2,(bounds[4]-bounds[1])/2,(bounds[5]-bounds[2])/2);
  mesh.geometry.scale(scale.x,scale.y,scale.z);
  mesh.geometry.translate(center.x,center.y,center.z);
  const active=mesh.geometry.getAttribute("position"),points=[];
  for(let i=0;i<mesh.geometry.drawRange.count;i++) points.push(new THREE.Vector3().fromBufferAttribute(active,i));
  mesh.geometry.boundingBox=new THREE.Box3().setFromPoints(points);
  mesh.geometry.boundingSphere=new THREE.Sphere().setFromPoints(points);
  return mesh;
}

export function createAnatomicalVolumeMesh({fields,bounds,resolution=24,smoothness=0.15,material}={}) {
  if(!(Number.isFinite(smoothness)&&smoothness>=0)) throw new RangeError("smoothness must be nonnegative");
  return createIsosurfaceMesh({bounds,resolution,field:p=>evaluateSmoothUnionSdf(fields,p,smoothness),iso:0,material});
}

export function evaluateMetaballField(point, balls, epsilon=1e-4) {
  if(!Array.isArray(balls)||balls.length===0) throw new TypeError("metaballs required");
  if(!(Number.isFinite(epsilon)&&epsilon>0)) throw new RangeError("epsilon must be positive");
  const p=point instanceof THREE.Vector3?point:new THREE.Vector3(...point);
  let sum=0;
  for(const b of balls){
    if(!b||!Array.isArray(b.center)||b.center.length!==3||!b.center.every(Number.isFinite)||
      !(Number.isFinite(b.radius)&&b.radius>0)) throw new RangeError("each metaball needs a finite center and positive radius");
    const d2=p.distanceToSquared(new THREE.Vector3(...b.center));
    sum+=(b.radius*b.radius)/(d2+epsilon*epsilon);
  }
  return sum;
}
export function createMetaballMesh({balls,bounds,resolution=24,iso=1,epsilon=1e-4,material}={}) {
  if(!(Number.isFinite(iso)&&iso>0)) throw new RangeError("iso must be positive");
  return createIsosurfaceMesh({bounds,resolution,field:p=>evaluateMetaballField(p,balls,epsilon),iso,material});
}

export function createMonotoneAnatomicalProfile(keys) {
  if(!Array.isArray(keys)||keys.length<2) throw new RangeError("at least two profile keys required");
  const x=keys.map(k=>k.s), y=keys.map(k=>k.radius);
  if(!x.every(Number.isFinite)||!y.every(Number.isFinite)||y.some(v=>v<0)) throw new RangeError("profile keys must be finite with nonnegative radii");
  const n=x.length, h=[], delta=[];
  for(let i=0;i<n-1;i++){
    h[i]=x[i+1]-x[i];
    if(!(h[i]>0)) throw new RangeError("profile positions must be strictly increasing");
    delta[i]=(y[i+1]-y[i])/h[i];
  }
  const m=new Array(n);
  m[0]=delta[0]; m[n-1]=delta[n-2];
  for(let i=1;i<n-1;i++){
    if(delta[i-1]*delta[i]<=0) m[i]=0;
    else {
      const w1=2*h[i]+h[i-1],w2=h[i]+2*h[i-1];
      m[i]=(w1+w2)/(w1/delta[i-1]+w2/delta[i]);
    }
  }
  for(let i=0;i<n-1;i++){
    if(Math.abs(delta[i])<EPS){m[i]=0;m[i+1]=0;continue;}
    const a=m[i]/delta[i],b=m[i+1]/delta[i],q=a*a+b*b;
    if(q>9){const tau=3/Math.sqrt(q);m[i]=tau*a*delta[i];m[i+1]=tau*b*delta[i];}
  }
  return {
    keys:keys.map(k=>({s:k.s,radius:k.radius})),
    radiusAt(s){
      if(!Number.isFinite(s)) throw new RangeError("s must be finite");
      if(s<=x[0])return y[0]; if(s>=x[n-1])return y[n-1];
      let lo=0,hi=n-1;
      while(hi-lo>1){const mid=(lo+hi)>>1;if(x[mid]<=s)lo=mid;else hi=mid;}
      const u=(s-x[lo])/h[lo],u2=u*u,u3=u2*u;
      const h00=2*u3-3*u2+1,h10=u3-2*u2+u,h01=-2*u3+3*u2,h11=u3-u2;
      const r=h00*y[lo]+h10*h[lo]*m[lo]+h01*y[lo+1]+h11*h[lo]*m[lo+1];
      return Math.max(0,r);
    }
  };
}

function normalizeInfluences(influences,boneCount,maxInfluences=Infinity) {
  if(!Array.isArray(influences)||influences.length===0) throw new RangeError("vertex needs at least one influence");
  const valid=influences.filter(v=>v&&Number.isInteger(v.bone)&&v.bone>=0&&v.bone<boneCount&&Number.isFinite(v.weight)&&v.weight>0)
    .sort((a,b)=>b.weight-a.weight||a.bone-b.bone).slice(0,maxInfluences);
  const total=valid.reduce((s,v)=>s+v.weight,0);
  if(!(total>EPS)) throw new RangeError("influence weights sum to zero");
  return valid.map(v=>({bone:v.bone,weight:v.weight/total}));
}

export function linearBlendSkinning({positions,influences,skinMatrices,normals=null}={}) {
  if(!Array.isArray(positions)||!Array.isArray(influences)||positions.length!==influences.length||
    !Array.isArray(skinMatrices)||skinMatrices.length===0||skinMatrices.some(m=>!(m instanceof THREE.Matrix4))) throw new TypeError("positions, influences and skinMatrices must match");
  const outPositions=[],outNormals=[];
  for(let i=0;i<positions.length;i++){
    const p=new THREE.Vector3(...positions[i]); if(![p.x,p.y,p.z].every(Number.isFinite)) throw new RangeError("position must be finite");
    const inf=normalizeInfluences(influences[i],skinMatrices.length);
    const result=new THREE.Vector3();
    let normalResult=new THREE.Vector3();
    for(const item of inf){
      result.addScaledVector(p.clone().applyMatrix4(skinMatrices[item.bone]),item.weight);
      if(normals){const nm=new THREE.Matrix3().getNormalMatrix(skinMatrices[item.bone]);normalResult.addScaledVector(new THREE.Vector3(...normals[i]).applyMatrix3(nm),item.weight);}
    }
    outPositions.push(result.toArray());
    if(normals)outNormals.push(normalResult.lengthSq()>EPS?normalResult.normalize().toArray():[0,1,0]);
  }
  return {positions:outPositions,normals:normals?outNormals:null};
}

export function dualQuaternionFromRigidTransform(rotation,translation) {
  const real=rotation instanceof THREE.Quaternion?rotation.clone():new THREE.Quaternion(...rotation);
  const t=translation instanceof THREE.Vector3?translation.clone():new THREE.Vector3(...translation);
  if(![real.x,real.y,real.z,real.w,t.x,t.y,t.z].every(Number.isFinite)||real.lengthSq()<EPS) throw new RangeError("invalid rigid transform");
  real.normalize();
  const tq=new THREE.Quaternion(t.x,t.y,t.z,0);
  const dual=tq.multiply(real).multiplyScalar(0.5);
  return {real,dual};
}

function dqsTransform(position,normal,influences,dualBones,maxInfluences=Infinity) {
  const inf=normalizeInfluences(influences,dualBones.length,maxInfluences);
  const ref=dualBones[inf[0].bone].real;
  const r=new THREE.Quaternion(0,0,0,0),d=new THREE.Quaternion(0,0,0,0);
  for(const item of inf){
    const q=dualBones[item.bone];
    let sign=q.real.dot(ref)<0?-1:1;
    r.x+=q.real.x*item.weight*sign;r.y+=q.real.y*item.weight*sign;r.z+=q.real.z*item.weight*sign;r.w+=q.real.w*item.weight*sign;
    d.x+=q.dual.x*item.weight*sign;d.y+=q.dual.y*item.weight*sign;d.z+=q.dual.z*item.weight*sign;d.w+=q.dual.w*item.weight*sign;
  }
  const norm=r.length();
  if(!(norm>EPS)) throw new RangeError("degenerate dual quaternion blend");
  r.multiplyScalar(1/norm); d.multiplyScalar(1/norm);
  const orthogonality=r.dot(d);
  d.x-=r.x*orthogonality;d.y-=r.y*orthogonality;d.z-=r.z*orthogonality;d.w-=r.w*orthogonality;
  const p=new THREE.Vector3(...position).applyQuaternion(r);
  const translation=d.clone().multiply(new THREE.Quaternion(-r.x,-r.y,-r.z,r.w));
  p.add(new THREE.Vector3(2*translation.x,2*translation.y,2*translation.z));
  const n=normal?new THREE.Vector3(...normal).applyQuaternion(r).normalize().toArray():null;
  return {position:p.toArray(),normal:n,real:r,dual:d};
}

export function dualQuaternionSkinning({positions,influences,dualBones,normals=null}={}) {
  if(!Array.isArray(positions)||!Array.isArray(influences)||positions.length!==influences.length||
    !Array.isArray(dualBones)||dualBones.length===0) throw new TypeError("positions, influences and dualBones must match");
  const outPositions=[],outNormals=[];
  for(let i=0;i<positions.length;i++){
    const result=dqsTransform(positions[i],normals?normals[i]:null,influences[i],dualBones);
    outPositions.push(result.position);if(normals)outNormals.push(result.normal);
  }
  return {positions:outPositions,normals:normals?outNormals:null};
}

export function dualQuaternionSkinningBounded({positions,influences,dualBones,normals=null,maxInfluences=4}={}) {
  if(!Number.isInteger(maxInfluences)||maxInfluences<1) throw new RangeError("maxInfluences must be a positive integer");
  if(!Array.isArray(positions)||!Array.isArray(influences)||positions.length!==influences.length||
    !Array.isArray(dualBones)||dualBones.length===0) throw new TypeError("positions, influences and dualBones must match");
  const outPositions=[],outNormals=[],discardedWeight=[];
  for(let i=0;i<positions.length;i++){
    const sorted=influences[i].slice().filter(v=>v&&Number.isFinite(v.weight)&&v.weight>0)
      .sort((a,b)=>b.weight-a.weight||a.bone-b.bone);
    const kept=sorted.slice(0,maxInfluences),total=sorted.reduce((s,v)=>s+v.weight,0),keptTotal=kept.reduce((s,v)=>s+v.weight,0);
    if(!(total>EPS&&keptTotal>EPS)) throw new RangeError("influence weights sum to zero");
    discardedWeight.push(Math.max(0,(total-keptTotal)/total));
    const result=dqsTransform(positions[i],normals?normals[i]:null,kept,dualBones,maxInfluences);
    outPositions.push(result.position);if(normals)outNormals.push(result.normal);
  }
  return {positions:outPositions,normals:normals?outNormals:null,discardedWeight};
}

export function computePupilPosition({eyeCenter,target,normal=[0,0,1],maxOffset=0.1,fallbackDirection=[1,0,0]}={}) {
  const e=new THREE.Vector3(...eyeCenter),g=new THREE.Vector3(...target),n=new THREE.Vector3(...normal);
  if(![e.x,e.y,e.z,g.x,g.y,g.z,n.x,n.y,n.z,maxOffset].every(Number.isFinite)||maxOffset<0) throw new RangeError("invalid eye parameters");
  if(n.lengthSq()<EPS) throw new RangeError("eye normal must be nonzero");
  n.normalize();
  let tangent=g.sub(e); if(tangent.lengthSq()<EPS)tangent=new THREE.Vector3(...fallbackDirection);
  tangent.addScaledVector(n,-tangent.dot(n));
  if(tangent.lengthSq()<EPS){const axis=Math.abs(n.x)<0.8?new THREE.Vector3(1,0,0):new THREE.Vector3(0,1,0);tangent=axis.addScaledVector(n,-axis.dot(n));}
  tangent.normalize();
  const displacement=Math.min(maxOffset,Math.max(0,new THREE.Vector3(...target).sub(e).length()));
  return {position:e.addScaledVector(tangent,displacement).toArray(),direction:tangent.toArray()};
}

export function solveFabrik({positions,lengths,target,root=null,tolerance=1e-4,maxIterations=20}={}) {
  if(!Array.isArray(positions)||!Array.isArray(lengths)||positions.length!==lengths.length+1||lengths.length===0) throw new RangeError("positions must contain one more joint than lengths");
  if(!Number.isFinite(tolerance)||tolerance<=0||!Number.isInteger(maxIterations)||maxIterations<1) throw new RangeError("invalid solver limits");
  if(lengths.some(l=>!Number.isFinite(l)||l<=0)) throw new RangeError("segment lengths must be positive and finite");
  const p=positions.map(v=>new THREE.Vector3(...v)),goal=new THREE.Vector3(...target),anchor=root?new THREE.Vector3(...root):p[0].clone();
  if(p.some(v=>![v.x,v.y,v.z].every(Number.isFinite))||![goal.x,goal.y,goal.z].every(Number.isFinite)) throw new RangeError("joint positions and target must be finite");
  const total=lengths.reduce((a,b)=>a+b,0),distance=anchor.distanceTo(goal);
  if(distance>total){
    const dir=goal.clone().sub(anchor).normalize();
    p[0].copy(anchor);for(let i=0;i<lengths.length;i++)p[i+1].copy(p[i]).addScaledVector(dir,lengths[i]);
    return {positions:p.map(v=>v.toArray()),reachable:false,converged:false,error:p[p.length-1].distanceTo(goal),iterations:0};
  }
  let error=Infinity,iterations=0;
  for(let iter=0;iter<maxIterations;iter++){
    p[p.length-1].copy(goal);
    for(let i=p.length-2;i>=0;i--){
      let dir=p[i].clone().sub(p[i+1]);
      if(dir.lengthSq()<EPS)dir.set(1,0,0);
      dir.normalize();p[i].copy(p[i+1]).addScaledVector(dir,lengths[i]);
    }
    p[0].copy(anchor);
    for(let i=0;i<lengths.length;i++){
      let dir=p[i+1].clone().sub(p[i]);if(dir.lengthSq()<EPS)dir.set(1,0,0);
      p[i+1].copy(p[i]).addScaledVector(dir.normalize(),lengths[i]);
    }
    error=p[p.length-1].distanceTo(goal);iterations=iter+1;
    if(error<=tolerance)break;
  }
  return {positions:p.map(v=>v.toArray()),reachable:true,converged:error<=tolerance,error,iterations};
}
