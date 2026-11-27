import * as THREE from "three";
import { integrateRK4 } from "./numerics/ode-integrators.js";
import { UniformGrid3D } from "./spatial-grid.mjs";

const EPS=1e-10;
function vec(value,name="vector"){
  const out=Array.from(value);
  if(out.length===0||!out.every(Number.isFinite))throw new RangeError(name+" must contain finite values");
  return out;
}
function sameLength(a,b,label){if(a.length!==b.length)throw new RangeError(label+" dimensions must match");}
function add(a,b){sameLength(a,b,"add");return a.map((v,i)=>v+b[i]);}
function sub(a,b){sameLength(a,b,"subtract");return a.map((v,i)=>v-b[i]);}
function scale(a,s){return a.map(v=>v*s);}
function norm(a){return Math.hypot(...a);}
function lerpValue(a,b,u){
  if(typeof a==="number"&&typeof b==="number")return a+(b-a)*u;
  const av=vec(a),bv=vec(b);sameLength(av,bv,"interpolation");return av.map((v,i)=>v+(bv[i]-v)*u);
}
function finiteNumber(v,n){if(!Number.isFinite(v))throw new RangeError(n+" must be finite");}

export function interpolateKeyframes(keys,time,{mode="linear",quaternion=false,clamp=true}={}){
  finiteNumber(time,"time");
  if(!Array.isArray(keys)||keys.length===0)throw new RangeError("keyframes required");
  for(let i=0;i<keys.length;i++){
    if(!Number.isFinite(keys[i].time)||(i>0&&keys[i].time<=keys[i-1].time))throw new RangeError("keyframe times must be strictly increasing");
  }
  if(time<=keys[0].time)return clamp?structuredClone(keys[0].value):keys[0].value;
  if(time>=keys.at(-1).time)return clamp?structuredClone(keys.at(-1).value):keys.at(-1).value;
  let lo=0,hi=keys.length-1;
  while(hi-lo>1){const mid=(lo+hi)>>1;if(keys[mid].time<=time)lo=mid;else hi=mid;}
  const a=keys[lo],b=keys[hi],u=(time-a.time)/(b.time-a.time);
  if(quaternion){
    const qa=new THREE.Quaternion(...a.value),qb=new THREE.Quaternion(...b.value);
    return qa.slerp(qb,u).toArray();
  }
  const t=mode==="smoothstep"?u*u*(3-2*u):mode==="linear"?u:(()=>{throw new RangeError("unsupported interpolation mode");})();
  return lerpValue(a.value,b.value,t);
}

export function easeSmoothstep(u){
  finiteNumber(u,"u");
  const t=Math.max(0,Math.min(1,u));
  return t*t*(3-2*t);
}
export function interpolateEased(a,b,u){return lerpValue(a,b,easeSmoothstep(u));}

export function harmonicMotion({center=0,amplitude=1,omega=1,phase=0,time=0}={}){
  finiteNumber(omega,"omega");finiteNumber(phase,"phase");finiteNumber(time,"time");
  const factor=Math.sin(omega*time+phase);
  if(typeof center==="number"&&typeof amplitude==="number")return center+amplitude*factor;
  const c=vec(center,"center"),a=vec(amplitude,"amplitude");sameLength(c,a,"harmonic motion");
  return c.map((v,i)=>v+a[i]*factor);
}
export function harmonicVelocity({amplitude=1,omega=1,phase=0,time=0}={}){
  finiteNumber(omega,"omega");finiteNumber(phase,"phase");finiteNumber(time,"time");
  const factor=omega*Math.cos(omega*time+phase);
  return typeof amplitude==="number"?amplitude*factor:scale(vec(amplitude),factor);
}

export function pendulumStep({theta,angularVelocity=0,length=1,gravity=9.81,dt,substeps=4}={}){
  finiteNumber(theta,"theta");finiteNumber(angularVelocity,"angularVelocity");
  if(!(Number.isFinite(length)&&length>0&&Number.isFinite(gravity)&&gravity>=0&&Number.isFinite(dt)&&dt>=0)||
    !Number.isInteger(substeps)||substeps<1)throw new RangeError("invalid pendulum parameters");
  if(dt===0)return {theta,angularVelocity};
  const result=integrateRK4((t,y)=>[y[1],-(gravity/length)*Math.sin(y[0])],[0,dt],[theta,angularVelocity],{nSteps:substeps});
  if(!result.success)throw new Error(result.message);
  const y=result.y.at(-1);return {theta:y[0],angularVelocity:y[1]};
}

export function dampedSpringStep({position,velocity,target,mass=1,stiffness=100,damping=10,force=0,dt,substeps=4}={}){
  const x=vec(typeof position==="number"?[position]:position,"position");
  const v=vec(typeof velocity==="number"?[velocity]:velocity,"velocity");
  const targetV=vec(typeof target==="number"?[target]:target,"target");
  const forceV=vec(typeof force==="number"?x.map(()=>force):force,"force");
  sameLength(x,v,"spring");sameLength(x,targetV,"spring");sameLength(x,forceV,"spring");
  if(!(Number.isFinite(mass)&&mass>0&&Number.isFinite(stiffness)&&stiffness>=0&&Number.isFinite(damping)&&damping>=0&&Number.isFinite(dt)&&dt>=0)||
    !Number.isInteger(substeps)||substeps<1)throw new RangeError("invalid damped spring parameters");
  if(dt===0)return {position:typeof position==="number"?x[0]:x,velocity:typeof velocity==="number"?v[0]:v};
  const state=[...x,...v],n=x.length;
  const result=integrateRK4((t,y)=>{
    const dx=y.slice(n),dv=[];
    for(let i=0;i<n;i++)dv.push((forceV[i]-damping*y[n+i]-stiffness*(y[i]-targetV[i]))/mass);
    return [...dx,...dv];
  },[0,dt],state,{nSteps:substeps});
  if(!result.success)throw new Error(result.message);
  const out=result.y.at(-1),px=out.slice(0,n),vx=out.slice(n);
  return {position:typeof position==="number"?px[0]:px,velocity:typeof velocity==="number"?vx[0]:vx};
}

export function verletStep(position,previousPosition,acceleration,dt,{damping=0}={}){
  const x=vec(position,"position"),prev=vec(previousPosition,"previousPosition"),a=vec(acceleration,"acceleration");
  sameLength(x,prev,"Verlet");sameLength(x,a,"Verlet");
  if(!(Number.isFinite(dt)&&dt>0&&Number.isFinite(damping)&&damping>=0&&damping<=1))throw new RangeError("invalid Verlet dt/damping");
  return x.map((v,i)=>v+(v-prev[i])*(1-damping)+a[i]*dt*dt);
}
export function semiImplicitEulerStep({position,velocity,acceleration,dt}={}){
  const x=vec(position,"position"),v=vec(velocity,"velocity"),a=vec(acceleration,"acceleration");
  sameLength(x,v,"Euler");sameLength(x,a,"Euler");
  if(!(Number.isFinite(dt)&&dt>=0))throw new RangeError("dt must be nonnegative");
  const nextV=add(v,scale(a,dt));
  return {position:add(x,scale(nextV,dt)),velocity:nextV};
}
export function rk4Step(derivative,time,state,dt){
  finiteNumber(time,"time");finiteNumber(dt,"dt");
  if(dt<0||typeof derivative!=="function")throw new RangeError("invalid RK4 step");
  const y=vec(state,"state");
  const result=integrateRK4((t,s)=>derivative(t,s),[time,time+dt],y,{nSteps:1});
  if(!result.success)throw new Error(result.message);
  return result.y.at(-1);
}

export function computeBoidsAcceleration({position,velocity,neighbors=[],separationWeight=1,alignmentWeight=1,cohesionWeight=1,separationRadius=1,alignmentRadius=2,cohesionRadius=2}={}){
  const p=vec(position,"position"),v=vec(velocity,"velocity");
  sameLength(p,v,"boid");
  for(const [n,x] of Object.entries({separationWeight,alignmentWeight,cohesionWeight,separationRadius,alignmentRadius,cohesionRadius}))finiteNumber(x,n);
  if(separationRadius<0||alignmentRadius<0||cohesionRadius<0)throw new RangeError("neighbor radii must be nonnegative");
  const sep=p.map(()=>0),align=p.map(()=>0),cohesion=p.map(()=>0);
  let ns=0,na=0,nc=0;
  for(const item of neighbors){
    const q=vec(item.position,"neighbor position"),w=vec(item.velocity,"neighbor velocity");
    sameLength(p,q,"neighbor");sameLength(v,w,"neighbor");
    const delta=sub(q,p),d=norm(delta);
    if(d<EPS)continue;
    if(d<=separationRadius){for(let k=0;k<p.length;k++)sep[k]-=delta[k]/(d*d);ns++;}
    if(d<=alignmentRadius){for(let k=0;k<p.length;k++)align[k]+=w[k];na++;}
    if(d<=cohesionRadius){for(let k=0;k<p.length;k++)cohesion[k]+=q[k];nc++;}
  }
  if(na)for(let k=0;k<p.length;k++)align[k]=align[k]/na-v[k];
  if(nc)for(let k=0;k<p.length;k++)cohesion[k]=cohesion[k]/nc-p[k];
  const acceleration=p.map((_,i)=>separationWeight*sep[i]+alignmentWeight*align[i]+cohesionWeight*cohesion[i]);
  return {acceleration,separationNeighbors:ns,alignmentNeighbors:na,cohesionNeighbors:nc};
}

export function particlePositionAt({position,velocity,acceleration,time}={}){
  const p=vec(position,"position"),v=vec(velocity,"velocity"),a=vec(acceleration,"acceleration");
  sameLength(p,v,"particle");sameLength(p,a,"particle");finiteNumber(time,"time");
  return p.map((x,i)=>x+v[i]*time+0.5*a[i]*time*time);
}

function hash32(value){
  let x=value|0;x=Math.imul(x^(x>>>16),0x7feb352d);x=Math.imul(x^(x>>>15),0x846ca68b);return (x^(x>>>16))>>>0;
}
function uniform(seed,step,axis,lane){
  return (hash32(seed^Math.imul(step+1,0x9e3779b1)^Math.imul(axis+1,0x85ebca6b)^Math.imul(lane+1,0xc2b2ae35))+0.5)/4294967296;
}
export function brownianStep({position,diffusion,dt,seed=1,stepIndex=0}={}){
  const p=vec(position,"position");
  if(!(Number.isFinite(diffusion)&&diffusion>=0&&Number.isFinite(dt)&&dt>=0&&Number.isInteger(seed)&&Number.isInteger(stepIndex)&&stepIndex>=0))throw new RangeError("invalid Brownian parameters");
  const sigma=Math.sqrt(2*diffusion*dt),delta=p.map((_,axis)=>{
    const u1=Math.max(uniform(seed,stepIndex,axis,0),Number.MIN_VALUE),u2=uniform(seed,stepIndex,axis,1);
    return sigma*Math.sqrt(-2*Math.log(u1))*Math.cos(2*Math.PI*u2);
  });
  return {position:add(p,delta),delta};
}

export function sphereSphereCollision(a,b){
  const ca=vec(a.center,"sphere center"),cb=vec(b.center,"sphere center");sameLength(ca,cb,"sphere collision");
  if(!(Number.isFinite(a.radius)&&a.radius>=0&&Number.isFinite(b.radius)&&b.radius>=0))throw new RangeError("sphere radii must be nonnegative");
  const delta=sub(cb,ca),distance=norm(delta),sum=a.radius+b.radius,normal=distance>EPS?scale(delta,1/distance):ca.map((_,i)=>i===0?1:0);
  const penetration=sum-distance;
  return {colliding:penetration>0,normal,penetration:Math.max(0,penetration),distance};
}
export function spherePlaneCollision({center,radius,normal,constant=0}={}){
  const p=vec(center,"center"),n=vec(normal,"normal");sameLength(p,n,"plane collision");
  if(!(Number.isFinite(radius)&&radius>=0&&Number.isFinite(constant)))throw new RangeError("invalid plane/sphere parameters");
  const len=norm(n);if(len<EPS)throw new RangeError("plane normal must be nonzero");
  const unit=scale(n,1/len),c=constant/len,d=unit.reduce((s,v,i)=>s+v*p[i],c),penetration=radius-d;
  return {colliding:penetration>0,normal:unit,signedDistance:d,penetration:Math.max(0,penetration),correctedCenter:penetration>0?add(p,scale(unit,penetration)):p};
}

export function simulateMassSpringChain({positions,velocities,masses,stiffness=30,damping=1,dt,steps=1,fixedIndices=[0]}={}){
  if(!Array.isArray(positions)||!Array.isArray(velocities)||positions.length<2||positions.length!==velocities.length||
    !Array.isArray(masses)||masses.length!==positions.length)throw new RangeError("chain arrays must have equal length >= 2");
  const x=positions.map(v=>vec(v,"position")),v=velocities.map(q=>vec(q,"velocity"));
  for(let i=0;i<x.length;i++){sameLength(x[i],v[i],"chain");if(!(Number.isFinite(masses[i])&&masses[i]>0))throw new RangeError("masses must be positive");}
  if(!(Number.isFinite(stiffness)&&stiffness>=0&&Number.isFinite(damping)&&damping>=0&&Number.isFinite(dt)&&dt>0)||
    !Number.isInteger(steps)||steps<1)throw new RangeError("invalid chain parameters");
  const fixed=new Set(fixedIndices),anchors=new Map([...fixed].map(i=>[i,x[i].slice()]));
  for(let step=0;step<steps;step++){
    const nextX=x.map(q=>q.slice()),nextV=v.map(q=>q.slice());
    for(let i=0;i<x.length;i++){
      if(fixed.has(i)){nextX[i]=anchors.get(i).slice();nextV[i]=x[i].map(()=>0);continue;}
      const force=x[i].map(()=>0);
      if(i>0){const f=scale(sub(x[i-1],x[i]),stiffness);for(let k=0;k<force.length;k++)force[k]+=f[k];}
      if(i<x.length-1){const f=scale(sub(x[i+1],x[i]),stiffness);for(let k=0;k<force.length;k++)force[k]+=f[k];}
      for(let k=0;k<force.length;k++)force[k]-=damping*v[i][k];
      const acc=scale(force,1/masses[i]),state=semiImplicitEulerStep({position:x[i],velocity:v[i],acceleration:acc,dt});
      nextX[i]=state.position;nextV[i]=state.velocity;
    }
    for(let i=0;i<x.length;i++){x[i]=nextX[i];v[i]=nextV[i];}
  }
  return {positions:x,velocities:v};
}

export function createDeterministicAnimator({seed=1,evaluate}={}){
  if(!Number.isInteger(seed)||typeof evaluate!=="function")throw new TypeError("integer seed and evaluate function required");
  return {
    stateAt(time,events=[]){
      finiteNumber(time,"time");
      const random=(eventId,channel=0)=>uniform(seed,hash32(String(eventId).split("").reduce((h,c)=>Math.imul(h^c.charCodeAt(0),16777619)>>>0,2166136261)),hash32(String(channel).length+String(channel).split("").reduce((h,c)=>Math.imul(h^c.charCodeAt(0),16777619)>>>0,2166136261)),0);
      return evaluate(time,{events,random,seed});
    }
  };
}

export function precomputeEventTable(times,evaluate){
  if(!Array.isArray(times)||times.length===0||typeof evaluate!=="function")throw new TypeError("times and evaluate required");
  for(let i=0;i<times.length;i++)if(!Number.isFinite(times[i])||(i>0&&times[i]<=times[i-1]))throw new RangeError("event times must be strictly increasing");
  return times.map(time=>({time,value:evaluate(time)}));
}
export function sampleEventTable(table,time){
  finiteNumber(time,"time");
  if(!Array.isArray(table)||table.length===0)throw new RangeError("event table required");
  if(time<=table[0].time)return structuredClone(table[0].value);
  if(time>=table.at(-1).time)return structuredClone(table.at(-1).value);
  let lo=0,hi=table.length-1;while(hi-lo>1){const mid=(lo+hi)>>1;if(table[mid].time<=time)lo=mid;else hi=mid;}
  const u=(time-table[lo].time)/(table[hi].time-table[lo].time);
  return lerpValue(table[lo].value,table[hi].value,u);
}
export function quantizeAnimationTime(time,fps,{mode="floor"}={}){
  if(!(Number.isFinite(time)&&time>=0&&Number.isFinite(fps)&&fps>0))throw new RangeError("time and fps must be valid");
  const raw=time*fps,frame=mode==="floor"?Math.floor(raw):mode==="round"?Math.round(raw):mode==="ceil"?Math.ceil(raw):null;
  if(frame===null)throw new RangeError("mode must be floor, round or ceil");
  return {frame,time:frame/fps};
}

export function solveXpbdDistanceConstraints({positions,inverseMasses,constraints,dt,iterations=8}={}){
  if(!Array.isArray(positions)||!Array.isArray(inverseMasses)||positions.length!==inverseMasses.length||
    !Array.isArray(constraints)||!Number.isFinite(dt)||dt<=0||!Number.isInteger(iterations)||iterations<1)throw new RangeError("invalid XPBD inputs");
  const x=positions.map(p=>vec(p,"position")),w=inverseMasses.slice();
  if(w.some(v=>!Number.isFinite(v)||v<0))throw new RangeError("inverse masses must be nonnegative");
  const lambdas=constraints.map(()=>0);
  const checked=constraints.map(c=>{
    if(!Number.isInteger(c.a)||!Number.isInteger(c.b)||c.a<0||c.b<0||c.a>=x.length||c.b>=x.length||c.a===c.b||
      !(Number.isFinite(c.restLength)&&c.restLength>=0&&Number.isFinite(c.compliance)&&c.compliance>=0))throw new RangeError("invalid distance constraint");
    return c;
  });
  for(let iter=0;iter<iterations;iter++)for(let ci=0;ci<checked.length;ci++){
    const c=checked[ci],delta=sub(x[c.b],x[c.a]),distance=norm(delta);
    if(distance<EPS)continue;
    const n=scale(delta,1/distance),C=distance-c.restLength,alphaTilde=c.compliance/(dt*dt);
    const denom=w[c.a]+w[c.b]+alphaTilde;if(denom<EPS)continue;
    const dlambda=-(C+alphaTilde*lambdas[ci])/denom;lambdas[ci]+=dlambda;
    x[c.a]=add(x[c.a],scale(n,-w[c.a]*dlambda));
    x[c.b]=add(x[c.b],scale(n,w[c.b]*dlambda));
  }
  return {positions:x,lambdas};
}

export function buildUniformNeighborIndex(points,cellSize=1){
  if(!Array.isArray(points))throw new TypeError("points array required");
  const grid=new UniformGrid3D({cellSize});
  points.forEach((p,i)=>{const v=vec(p,"point");if(v.length!==3)throw new RangeError("3D points required");grid.insert(i,v,v,i);});
  return grid;
}
export function queryUniformNeighbors(grid,points,point,radius,{excludeIndex=null}={}){
  if(!(grid instanceof UniformGrid3D)||!Array.isArray(points)||!(Number.isFinite(radius)&&radius>=0))throw new RangeError("invalid neighbor query");
  const p=vec(point,"query point");if(p.length!==3)throw new RangeError("3D query point required");
  const min=p.map(v=>v-radius),max=p.map(v=>v+radius);
  return grid.queryAABB(min,max).filter(i=>i!==excludeIndex&&Math.hypot(...sub(vec(points[i]),p))<=radius);
}
