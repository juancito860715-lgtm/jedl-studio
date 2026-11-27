import * as THREE from "three";
import { quantizedTime, deterministicJitter, fabrik, dualQuaternionNormalize, blendDualQuaternions } from "../../tests/threejs/r31_kernels.mjs";

function quaternionMultiply(a,b){
  const [w,x,y,z]=a,[W,X,Y,Z]=b;
  return [w*W-x*X-y*Y-z*Z,w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W];
}
function transformPoint(point,qr,qd){
  const p=[0,...point],conj=[qr[0],-qr[1],-qr[2],-qr[3]];
  const rotated=quaternionMultiply(quaternionMultiply(qr,p),conj);
  const translated=quaternionMultiply(qd,conj).map(v=>2*v);
  return [rotated[1]+translated[1],rotated[2]+translated[2],rotated[3]+translated[3]];
}
function lineObject(points,color){
  const g=new THREE.BufferGeometry().setFromPoints(points.map(p=>new THREE.Vector3(...p)));
  return new THREE.Line(g,new THREE.LineBasicMaterial({color}));
}
export function createStopMotionValidationScene({frame=12,seed=77,sampleRate=12}={}){
  const scene=new THREE.Scene();scene.name="R31 Stop-motion deterministic microjitter";
  const times=Array.from({length:9},(_,i)=>i/sampleRate);
  const base=times.map((t,i)=>[i*.12,Math.sin(i*.25)*.08,0]);
  const jittered=base.map((p,i)=>[p[0]+deterministicJitter(i,seed,0,.025),p[1]+deterministicJitter(i,seed,1,.015),p[2]]);
  scene.add(lineObject(base,0x777777));scene.children[0].name="quantized-base-poses";
  scene.add(lineObject(jittered,0xd07839));scene.children[1].name="deterministic-microjitter-poses";
  scene.userData.validation={algorithm:"hash-based-per-frame-per-channel-jitter",frame,seed,sampleRate,times,quantizedTime:quantizedTime(frame/sampleRate,sampleRate),jittered};
  return scene;
}
export function createFabrikValidationScene({target=[1.25,1.1]}={}){
  const scene=new THREE.Scene();scene.name="R31 FABRIK articulated chain";
  const root=[0,0],lengths=[.8,.7,.6],initial=[[0,0],[.8,0],[1.5,0],[2.1,0]];
  const solved=fabrik(initial,lengths,target,root,128,1e-10);
  scene.add(lineObject(initial.map(([x,y])=>[x,y,0]),0x999999));
  scene.add(lineObject(solved.map(([x,y])=>[x,y,.03]),0x2787c9));
  scene.children[0].name="initial-chain";scene.children[1].name="fabrik-solved-chain";
  scene.userData.validation={algorithm:"FABRIK-backward-forward-projection",root,lengths,target,solved,segmentLengths:solved.slice(1).map((p,i)=>Math.hypot(p[0]-solved[i][0],p[1]-solved[i][1]))};
  return scene;
}
export function createDualQuaternionValidationScene(){
  const scene=new THREE.Scene();scene.name="R31 Dual-quaternion skinning transform";
  const angle=Math.PI/4,qr=[Math.cos(angle/2),0,0,Math.sin(angle/2)];
  const translation=[.6,.2,0],tq=[0,...translation];
  const qd=quaternionMultiply(tq,qr).map(v=>v*.5);
  const [real,dual]=dualQuaternionNormalize(qr,qd);
  const blended=blendDualQuaternions([{qr:real,qd:dual,weight:.25},{qr:real.map(v=>-v),qd:dual.map(v=>-v),weight:.75}]);
  const source=[[.8,0,0],[0,.8,0],[-.8,0,0],[0,-.8,0],[.8,0,0]];
  const moved=source.map(p=>transformPoint(p,...blended));
  scene.add(lineObject(source,0x999999));scene.add(lineObject(moved,0x2787c9));
  scene.children[0].name="bind-pose";scene.children[1].name="dual-quaternion-deformed-pose";
  scene.userData.validation={algorithm:"normalized-dual-quaternion-blend-and-rigid-transform",qr:real,qd:dual,translation,source,moved,realDualDot:real.reduce((s,v,i)=>s+v*dual[i],0)};
  return scene;
}
export function createTemporalQuantizationValidationScene({sampleRate=24,duration=1}={}){
  const scene=new THREE.Scene();scene.name="R31 Temporal animation quantization";
  const raw=Array.from({length:49},(_,i)=>i*duration/48);
  const quantized=raw.map(t=>quantizedTime(t,sampleRate));
  const rawPoints=raw.map((t,i)=>[t,Math.sin(t*Math.PI*2)*.25,0]);
  const qPoints=quantized.map((t,i)=>[raw[i],Math.sin(t*Math.PI*2)*.25,.04]);
  scene.add(lineObject(rawPoints,0x999999));scene.add(lineObject(qPoints,0x2787c9));
  scene.children[0].name="continuous-reference-samples";scene.children[1].name="sample-and-hold-quantized-samples";
  scene.userData.validation={algorithm:"floor-based-fixed-rate-time-quantization",sampleRate,duration,raw,quantized,maxQuantizationError:Math.max(...raw.map((t,i)=>t-quantized[i]))};
  return scene;
}
export function createAllR31CoreScenes(){
  return [createStopMotionValidationScene(),createFabrikValidationScene(),createDualQuaternionValidationScene(),createTemporalQuantizationValidationScene()];
}
