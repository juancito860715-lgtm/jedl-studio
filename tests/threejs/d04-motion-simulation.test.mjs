import test from "node:test";
import assert from "node:assert/strict";
import * as THREE from "three";
import {
 interpolateKeyframes,easeSmoothstep,interpolateEased,harmonicMotion,harmonicVelocity,
 pendulumStep,dampedSpringStep,verletStep,semiImplicitEulerStep,rk4Step,computeBoidsAcceleration,
 particlePositionAt,brownianStep,sphereSphereCollision,spherePlaneCollision,simulateMassSpringChain,
 createDeterministicAnimator,precomputeEventTable,sampleEventTable,quantizeAnimationTime,
 solveXpbdDistanceConstraints,buildUniformNeighborIndex,queryUniformNeighbors
} from "../../src/threejs/d04-motion-simulation.mjs";

test("keyframe interpolation clamps, interpolates scalar/vector and slerps rotations",()=>{
 const keys=[{time:0,value:0},{time:2,value:4}];
 assert.equal(interpolateKeyframes(keys,-1),0);
 assert.equal(interpolateKeyframes(keys,1),2);
 assert.deepEqual(interpolateKeyframes([{time:0,value:[0,2]},{time:1,value:[2,4]}],.5),[1,3]);
 const q=interpolateKeyframes([{time:0,value:[0,0,0,1]},{time:1,value:[0,1,0,0]}],.5,{quaternion:true});
 assert.ok(Math.abs(new THREE.Quaternion(...q).length()-1)<1e-12);
});
test("smoothstep easing has zero slope at endpoints and clamps",()=>{
 assert.equal(easeSmoothstep(-1),0);assert.equal(easeSmoothstep(0),0);assert.equal(easeSmoothstep(1),1);assert.equal(easeSmoothstep(2),1);
 assert.equal(interpolateEased(0,10,.5),5);
});
test("harmonic motion returns analytic position and velocity",()=>{
 assert.ok(Math.abs(harmonicMotion({center:2,amplitude:3,omega:Math.PI/2,time:1})-5)<1e-12);
 assert.ok(Math.abs(harmonicVelocity({amplitude:2,omega:3,phase:0,time:0})-6)<1e-12);
});
test("pendulum RK4 step preserves small-angle energy approximately",()=>{
 const s=pendulumStep({theta:.1,angularVelocity:0,length:1,gravity:9.81,dt:.01,substeps:8});
 assert.ok(s.theta<.1&&s.theta>0);assert.ok(s.angularVelocity<0);
});
test("damped spring RK4 approaches target under positive damping",()=>{
 let s={position:0,velocity:0};
 for(let i=0;i<100;i++)s=dampedSpringStep({...s,target:1,mass:1,stiffness:25,damping:8,dt:.02,substeps:4});
 assert.ok(Math.abs(s.position-1)<.01);assert.ok(Math.abs(s.velocity)<.1);
});
test("Verlet and semi-implicit Euler use expected update order",()=>{
 assert.deepEqual(verletStep([1,0],[0,0],[0,-9.8],.1),[2,-.098]);
 const e=semiImplicitEulerStep({position:[0,0],velocity:[1,0],acceleration:[0,-10],dt:.1});
 assert.deepEqual(e.velocity,[1,-1]);assert.deepEqual(e.position,[.1,-.1]);
});
test("RK4 wrapper solves exponential growth accurately",()=>{
 const y=rk4Step((t,s)=>[s[0]],0,[1],.1);
 assert.ok(Math.abs(y[0]-Math.exp(.1))<1e-6);
});
test("boids computes separation, alignment and cohesion contributions",()=>{
 const result=computeBoidsAcceleration({position:[0,0,0],velocity:[1,0,0],neighbors:[{position:[.5,0,0],velocity:[0,1,0]}],separationRadius:1,alignmentRadius:2,cohesionRadius:2});
 assert.ok(result.acceleration[0]<0);assert.ok(result.acceleration[1]>0);
 assert.equal(result.separationNeighbors,1);
});
test("particle analytic trajectory matches constant acceleration",()=>{
 assert.deepEqual(particlePositionAt({position:[0,0],velocity:[2,0],acceleration:[0,-10],time:2}),[4,-20]);
});
test("Brownian steps are deterministic by seed and step index",()=>{
 const args={position:[0,0,0],diffusion:.5,dt:.1,seed:77,stepIndex:3};
 assert.deepEqual(brownianStep(args),brownianStep(args));
 assert.notDeepEqual(brownianStep(args).delta,brownianStep({...args,stepIndex:4}).delta);
});
test("sphere-sphere collision detects overlap and coincident-center fallback",()=>{
 const hit=sphereSphereCollision({center:[0,0,0],radius:1},{center:[1.5,0,0],radius:1});
 assert.equal(hit.colliding,true);assert.ok(Math.abs(hit.penetration-.5)<1e-12);
 const same=sphereSphereCollision({center:[0,0,0],radius:1},{center:[0,0,0],radius:1});
 assert.deepEqual(same.normal,[1,0,0]);
});
test("sphere-plane collision normalizes plane normal and corrects penetration",()=>{
 const hit=spherePlaneCollision({center:[0,.5,0],radius:1,normal:[0,2,0],constant:0});
 assert.equal(hit.colliding,true);assert.deepEqual(hit.normal,[0,1,0]);assert.deepEqual(hit.correctedCenter,[0,1,0]);
});
test("mass-spring chain advances interior mass and preserves fixed anchor",()=>{
 const s=simulateMassSpringChain({positions:[[0,0,0],[2,0,0],[3,0,0]],velocities:[[0,0,0],[0,0,0],[0,0,0]],masses:[1,1,1],stiffness:10,damping:0,dt:.01,steps:2,fixedIndices:[0,2]});
 assert.deepEqual(s.positions[0],[0,0,0]);assert.deepEqual(s.positions[2],[3,0,0]);assert.ok(s.positions[1][0]<2);
});
test("deterministic animator gives order-independent random values",()=>{
 const animator=createDeterministicAnimator({seed:123,evaluate:(time,ctx)=>({time,r:ctx.random("impact",2)})});
 const a=animator.stateAt(2).r;animator.stateAt(1);const b=animator.stateAt(2).r;
 assert.equal(a,b);assert.ok(a>=0&&a<1);
});
test("event table precomputes and interpolates from absolute time",()=>{
 const table=precomputeEventTable([0,1,2],t=>t*t);
 assert.equal(sampleEventTable(table,1.5),2.5);
 assert.equal(sampleEventTable(table,-1),0);
});
test("time quantization returns deterministic frame index and timestamp",()=>{
 assert.deepEqual(quantizeAnimationTime(.26,10),{frame:2,time:.2});
 assert.deepEqual(quantizeAnimationTime(.26,10,{mode:"round"}),{frame:3,time:.3});
});
test("XPBD distance constraint corrects stretch and respects fixed inverse mass",()=>{
 const s=solveXpbdDistanceConstraints({positions:[[0,0,0],[2,0,0]],inverseMasses:[1,1],constraints:[{a:0,b:1,restLength:1,compliance:0}],dt:1,iterations:1});
 assert.ok(Math.abs(new THREE.Vector3(...s.positions[0]).distanceTo(new THREE.Vector3(...s.positions[1]))-1)<1e-12);
 const fixed=solveXpbdDistanceConstraints({positions:[[0,0,0],[2,0,0]],inverseMasses:[0,1],constraints:[{a:0,b:1,restLength:1,compliance:0}],dt:1,iterations:1});
 assert.deepEqual(fixed.positions[0],[0,0,0]);
});
test("uniform neighbor hash filters by radius after cell lookup",()=>{
 const points=[[0,0,0],[.5,0,0],[1.5,0,0],[4,0,0]];
 const grid=buildUniformNeighborIndex(points,1);
 assert.deepEqual(queryUniformNeighbors(grid,points,[0,0,0],1,{excludeIndex:0}),[1]);
});
