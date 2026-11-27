import test from "node:test";
import assert from "node:assert/strict";
import * as k from "./r31_kernels.mjs";
const near=(a,b,tol=1e-9)=>assert.ok(Math.abs(a-b)<=tol, `${a} != ${b}`);
const vec=(a,b,tol=1e-9)=>{assert.equal(a.length,b.length);a.forEach((v,i)=>near(v,b[i],tol));};

test("temporal quantization matches Python references",()=>{near(k.quantizedTime(1.13,12),13/12);near(k.quantizedTime(-.01,12),-1/12);});
test("smooth minimum matches Python reference",()=>{near(k.smoothMin(0,0,.5),-.125);near(k.smoothMin(0,2,.5),0);});
test("XPBD rigid projection matches Python reference",()=>{vec(k.xpbdDistanceStep(0,2,1,1,1,0,1),[.5,1.5,-.5]);});
test("RK4 exponential decay matches Python reference",()=>{let y=1;for(let i=0;i<10;i++)y=k.rk4Scalar(v=>-v,y,i*.1,.1);near(y,.3678797744124984,1e-12);});
test("Beer-Lambert transmittance matches Python reference",()=>near(k.beerLambertTransmittance(2,.5),.36787944117144233));
test("Schlick endpoints match Python reference",()=>{near(k.fresnelSchlick(.04,1),.04);near(k.fresnelSchlick(.04,0),1);});
test("spatial hash uses floor for negative coordinates",()=>assert.deepEqual(k.spatialCell([1.9,-.1,4],[0,0,0],1),[1,-1,4]));
test("structure tensor orientation matches reference",()=>{near(k.structureTensorOrientation(4,0,1),0);near(k.structureTensorOrientation(1,0,4),Math.PI/2);});
test("dual quaternion normalization matches Python reference",()=>{const [r,d]=k.dualQuaternionNormalize([2,0,0,0],[1,3,0,0]);vec(r,[1,0,0,0]);vec(d,[0,1.5,0,0]);});
test("FABRIK preserves lengths and reaches target",()=>{const p=k.fabrik([[0,0],[1,0],[2,0]],[1,1],[1,1],[0,0]);near(Math.hypot(p[2][0]-1,p[2][1]-1),0,1e-7);near(Math.hypot(p[1][0]-p[0][0],p[1][1]-p[0][1]),1);});
test("stop-motion jitter deterministic and bounded",()=>{const v=k.deterministicJitter(12,77,0,.1);near(v,.03660585642792285,1e-15);assert.ok(v>=-.1&&v<.1);});
test("GGX NDF reference values",()=>{near(k.ggxNdf(1,.5),1.2732395447351628);near(k.ggxNdf(0,.5),.07957747154594767);});
test("hair GGX NDF and tilted half-vector match Huang et al. Appendix A",()=>{near(k.hairGgxNdf(0,.5),.25/Math.PI);near(k.hairGgxNdf(1,.5),4/Math.PI);near(k.hairTiltedHalfDot(0,.3,.3,0),1);assert.throws(()=>k.hairGgxNdf(1,0),RangeError);});
test("Reynolds prioritized acceleration allocation trims the final request",()=>{vec(k.prioritizedAccelerationAllocation([[[.8,0,0],1],[[0,.8,0],1]],1),[.8,.2,0]);vec(k.prioritizedAccelerationAllocation([[[.6,0,0],1],[[0,.2,0],1]],1),[.6,.2,0]);vec(k.prioritizedAccelerationAllocation([[[1,0,0],0]],2),[0,0,0]);assert.throws(()=>k.prioritizedAccelerationAllocation([[[1,0],1]],1),RangeError);});
test("XPBD compliance scaling changes with dt exactly as alpha/dt^2",()=>{const a=k.xpbdDistanceStep(0,2,1,1,1,1,1),b=k.xpbdDistanceStep(0,2,1,1,1,1,.5);near(a[2],-1/3);near(b[2],-1/6);near(a[1]-a[0],4/3);near(b[1]-b[0],5/3);});
test("anisotropic Kuwahara matches published weight equation and Python oracle",()=>{near(k.anisotropicKuwaharaMean([0,10],[0,3],2),10/11);near(k.anisotropicKuwaharaMean([0,10],[0,3]),10/6563);near(k.anisotropicKuwaharaMean([2,4],[0,0]),3);assert.throws(()=>k.anisotropicKuwaharaMean([1],[-.1]),RangeError);});
test("weighted sector mean matches reference convention",()=>near(k.weightedSectorMean([0,10],[0,9]),10/11));
test("impasto plane gradient matches coefficients",()=>vec(k.linearHeightGradient(2.5,-.75,3,4),[2.5,-.75],1e-8));
test("flow-oriented noise periodicity",()=>near(k.orientedPeriodicNoise([.2+Math.PI,.3],[1,0],2),k.orientedPeriodicNoise([.2,.3],[1,0],2),1e-12));
test("camera transported normal remains unit and orthogonal",()=>{const n=k.transportNormal([0,1,0],[1,0,0]);near(Math.hypot(...n),1);near(n[0],0);});
test("depth-normal edge is zero for identical samples",()=>near(k.depthNormalEdge(4,4,[0,0,1],[0,0,1],2),0));
test("halftone pattern repeats after its period",()=>near(k.halftonePattern(.3+8,.7,.25),k.halftonePattern(.3,.7,.25),1e-12));
test("hatching phase repeats after one spacing",()=>near(k.hatchPhase([.7,.4],[1,0],.5),k.hatchPhase([.2,.4],[1,0],.5)));
test("semi-Lagrangian advection preserves a constant field",()=>vec(k.semiLagrangianAdvect1d(Array(8).fill(3),.75,.2),Array(8).fill(3)));
test("boids steering vectors match reference directions",()=>{const [s,a,c]=k.boidSteering([0,0],[1,0],[[1,0]],[[0,2]]);vec(s,[-1,0]);vec(a,[-1,2]);vec(c,[1,0]);});
test("greedy mesher merges equal rectangle and splits keys",()=>{assert.equal(k.greedyRectangles([[1,1],[1,1]]).length,1);assert.equal(k.greedyRectangles([[1,2],[1,2]]).length,2);});
test("volume compositing matches Beer-Lambert reference",()=>{const [L,T]=k.volumeComposite(Array(4).fill([2,.5,.25,1]));near(T,.36787944117144233);near(L,.6321205588285577);});
test("regularized dual contour QEF recovers plane location",()=>{const c=[[[.25,.1,.1],[1,0,0]],[[.25,.8,.2],[1,0,0]],[[.25,.3,.9],[1,0,0]]];near(k.regularizedPlaneQef(c,[.5,.5,.5],1e-6)[0],.25,1e-5);});

test("Teschner spatial hash maps integer cells into a bounded table bucket",()=>{
  const expected=(((73856093^(2*19349663)^(3*83492791))>>>0)%97);
  assert.equal(k.spatialHashIndex([1,2,3],97),expected);
  assert.ok(k.spatialHashIndex([-1,-2,-3],97)>=0);
  assert.throws(()=>k.spatialHashIndex([1,2,3],0),RangeError);
});
test("dual-quaternion blending corrects antipodal signs before normalization",()=>{
  const [qr,qd]=k.blendDualQuaternions([
    {qr:[1,0,0,0],qd:[0,0,0,0],weight:.5},
    {qr:[-1,0,0,0],qd:[0,0,0,0],weight:.5}
  ]);
  vec(qr,[1,0,0,0]);vec(qd,[0,0,0,0]);
  near(qr.reduce((s,v,i)=>s+v*qd[i],0),0);
  assert.throws(()=>k.blendDualQuaternions([{qr:[1,0,0,0],qd:[0,0,0,0],weight:0}]),RangeError);
});
