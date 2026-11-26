// R31 isolated mathematical kernels ported from the Python reference suite.
// This module intentionally exposes kernels, not complete production solvers.
export function quantizedTime(t, sampleRate) {
  if (!(sampleRate > 0)) throw new RangeError("sampleRate must be > 0");
  return Math.floor(t * sampleRate) / sampleRate;
}
export function smoothMin(a,b,k) {
  if (k < 0) throw new RangeError("k must be >= 0");
  if (k === 0) return Math.min(a,b);
  const h=Math.max(k-Math.abs(a-b),0)/k;
  return Math.min(a,b)-h*h*k/4;
}
export function xpbdDistanceStep(x0,x1,restLength,w0,w1,compliance,dt,lambda=0) {
  if (!(dt>0) || Math.min(w0,w1,compliance)<0) throw new RangeError("invalid XPBD parameters");
  const delta=x1-x0, distance=Math.abs(delta);
  if (distance===0) throw new RangeError("coincident points have undefined gradient");
  const direction=delta>0?1:-1, C=distance-restLength;
  const alphaTilde=compliance/(dt*dt), denom=w0+w1+alphaTilde;
  if (denom===0) throw new RangeError("zero effective inverse mass");
  const dlambda=-(C+alphaTilde*lambda)/denom;
  return [x0+w0*(-direction)*dlambda,x1+w1*direction*dlambda,lambda+dlambda];
}
export function rk4Scalar(f,y,t,dt) {
  const k1=f(y,t), k2=f(y+dt*k1/2,t+dt/2);
  const k3=f(y+dt*k2/2,t+dt/2), k4=f(y+dt*k3,t+dt);
  return y+dt*(k1+2*k2+2*k3+k4)/6;
}
export function beerLambertTransmittance(sigmaT,distance) {
  if (sigmaT<0 || distance<0) throw new RangeError("nonnegative sigmaT and distance required");
  return Math.exp(-sigmaT*distance);
}
export function fresnelSchlick(f0,cosTheta) {
  const c=Math.min(1,Math.max(0,cosTheta));
  return f0+(1-f0)*(1-c)**5;
}
export function spatialCell(position,origin,cellSize) {
  if (!(cellSize>0)) throw new RangeError("cellSize must be > 0");
  return position.map((p,i)=>Math.floor((p-origin[i])/cellSize));
}
export function structureTensorOrientation(jxx,jxy,jyy) {
  return 0.5*Math.atan2(2*jxy,jxx-jyy);
}
export function dualQuaternionNormalize(qr,qd) {
  const norm=Math.hypot(...qr);
  if (norm===0) throw new RangeError("real quaternion cannot be zero");
  const r=qr.map(v=>v/norm), d0=qd.map(v=>v/norm);
  const dot=r.reduce((s,v,i)=>s+v*d0[i],0);
  return [r,d0.map((v,i)=>v-dot*r[i])];
}
export function fabrik(points,lengths,target,root,iterations=64,tolerance=1e-9) {
  const pts=points.map(p=>[...p]);
  if (pts.length!==lengths.length+1 || lengths.some(v=>!(v>0))) throw new RangeError("invalid chain");
  const dist=(a,b)=>Math.hypot(...a.map((v,i)=>v-b[i]));
  const total=lengths.reduce((a,b)=>a+b,0), rootTarget=dist(root,target);
  if(rootTarget>=total) {
    const dir=root.map((v,i)=>(target[i]-v)/rootTarget);
    pts[0]=[...root];
    lengths.forEach((l,i)=>pts[i+1]=pts[i].map((v,k)=>v+dir[k]*l));
    return pts;
  }
  const base=[...root];
  for(let it=0;it<iterations;it++){
    pts[pts.length-1]=[...target];
    for(let i=lengths.length-1;i>=0;i--){
      const d=dist(pts[i],pts[i+1]); if(d===0) throw new RangeError("degenerate backward projection");
      pts[i]=pts[i+1].map((v,k)=>v+(pts[i][k]-v)*lengths[i]/d);
    }
    pts[0]=base;
    for(let i=0;i<lengths.length;i++){
      const d=dist(pts[i],pts[i+1]); if(d===0) throw new RangeError("degenerate forward projection");
      pts[i+1]=pts[i].map((v,k)=>v+(pts[i+1][k]-v)*lengths[i]/d);
    }
    if(dist(pts.at(-1),target)<=tolerance) break;
  }
  return pts;
}
export function deterministicJitter(frame,seed,channel,amplitude) {
  if(amplitude<0) throw new RangeError("amplitude must be nonnegative");
  let x=(Math.imul(frame|0,0x9E3779B1)+Math.imul(seed|0,0x85EBCA77)+Math.imul(channel|0,0xC2B2AE3D))>>>0;
  x=(x^(x>>>16))>>>0; x=Math.imul(x,0x7FEB352D)>>>0; x=(x^(x>>>15))>>>0;
  x=Math.imul(x,0x846CA68B)>>>0; x=(x^(x>>>16))>>>0;
  return amplitude*(2*(x/4294967296)-1);
}
export function ggxNdf(cosTheta,alpha) {
  if(!(alpha>0)) throw new RangeError("alpha must be positive");
  const c=Math.min(1,Math.max(0,cosTheta)),a2=alpha*alpha,denom=c*c*(a2-1)+1;
  return a2/(Math.PI*denom*denom);
}
export function weightedSectorMean(means,variances) {
  if(!means.length||means.length!==variances.length||variances.some(v=>v<0)) throw new RangeError("invalid sector data");
  const weights=variances.map(v=>1/(1+v));
  return means.reduce((s,m,i)=>s+m*weights[i],0)/weights.reduce((a,b)=>a+b,0);
}
export function linearHeightGradient(a,b,x,y) {
  const e=1e-5,h=(px,py)=>a*px+b*py;
  return [(h(x+e,y)-h(x-e,y))/(2*e),(h(x,y+e)-h(x,y-e))/(2*e)];
}
export function orientedPeriodicNoise(position,direction,frequency) {
  const len=Math.hypot(...direction); if(len===0||frequency<=0) throw new RangeError("invalid direction/frequency");
  return Math.sin(position.reduce((s,p,i)=>s+p*direction[i]/len,0)*frequency);
}
export function transportNormal(normal,newTangent) {
  const dot=normal.reduce((s,v,i)=>s+v*newTangent[i],0);
  let p=normal.map((v,i)=>v-dot*newTangent[i]),len=Math.hypot(...p);
  if(len<1e-12){
    const axis=Math.abs(newTangent[0])<0.9?[1,0,0]:[0,1,0],d=axis.reduce((s,v,i)=>s+v*newTangent[i],0);
    p=axis.map((v,i)=>v-d*newTangent[i]);len=Math.hypot(...p);
  }
  return p.map(v=>v/len);
}
export function depthNormalEdge(z0,z1,n0,n1,normalWeight) {
  if(normalWeight<0) throw new RangeError("normalWeight must be nonnegative");
  const dot=n0.reduce((s,v,i)=>s+v*n1[i],0);
  return Math.abs(z0-z1)+normalWeight*(1-Math.max(-1,Math.min(1,dot)));
}
export function halftonePattern(x,y,frequency) {
  if(frequency<=0) throw new RangeError("frequency must be positive");
  return 0.5+0.5*Math.sin(Math.PI*frequency*x)*Math.sin(Math.PI*frequency*y);
}
export function hatchPhase(position,direction,spacing) {
  const len=Math.hypot(...direction); if(len===0||spacing<=0) throw new RangeError("invalid direction/spacing");
  const v=position.reduce((s,p,i)=>s+p*direction[i]/len,0)/spacing;
  return v-Math.floor(v);
}
export function sampleLinear1d(values,x) {
  if(x<=0)return values[0]; if(x>=values.length-1)return values.at(-1);
  const i=Math.floor(x),f=x-i; return values[i]*(1-f)+values[i+1]*f;
}
export function semiLagrangianAdvect1d(values,velocity,dt) {
  return values.map((_,i)=>sampleLinear1d(values,i-velocity*dt));
}
export function boidSteering(position,velocity,neighborPositions,neighborVelocities) {
  if(!neighborPositions.length)return [[0,0],[0,0],[0,0]];
  const n=neighborPositions.length;
  const center=[0,1].map(k=>neighborPositions.reduce((s,p)=>s+p[k],0)/n);
  const avgV=[0,1].map(k=>neighborVelocities.reduce((s,v)=>s+v[k],0)/n);
  const separation=[0,1].map(k=>neighborPositions.reduce((s,p)=>s+position[k]-p[k],0)/n);
  const alignment=[0,1].map(k=>avgV[k]-velocity[k]),cohesion=[0,1].map(k=>center[k]-position[k]);
  return [separation,alignment,cohesion];
}
export function greedyRectangles(mask) {
  const g=mask.map(r=>[...r]),h=g.length,w=h?g[0].length:0,rects=[];
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const key=g[y][x];if(key===null||key===undefined)continue;
    let x2=x;while(x2<w&&g[y][x2]===key)x2++;
    let y2=y+1;while(y2<h&&g[y2].slice(x,x2).every(v=>v===key))y2++;
    for(let yy=y;yy<y2;yy++)for(let xx=x;xx<x2;xx++)g[yy][xx]=null;
    rects.push([x,y,x2,y2,key]);
  }
  return rects;
}
export function volumeComposite(segments) {
  let trans=1,radiance=0;
  for(const [sigmaT,density,ds,source] of segments){
    const alpha=1-Math.exp(-sigmaT*density*ds);
    radiance+=trans*alpha*source;trans*=1-alpha;
  }
  return [radiance,trans];
}
export function regularizedPlaneQef(constraints,center,regularization) {
  if(regularization<0)throw new RangeError("regularization must be nonnegative");
  const A=center.map(()=>regularization),b=center.map(v=>regularization*v);
  for(const [point,normal] of constraints)for(let axis=0;axis<3;axis++){
    A[axis]+=normal[axis]*normal[axis];
    const projection=normal.reduce((s,v,k)=>s+v*point[k],0);
    b[axis]+=normal[axis]*projection;
  }
  return b.map((v,i)=>A[i]?v/A[i]:center[i]);
}
