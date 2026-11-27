import test from "node:test";
import assert from "node:assert/strict";
import * as THREE from "three";
import {
 generateRecursiveTree,expandLSystem,interpretLSystem3D,samplePoissonDisk2D,generatePhyllotaxis,
 createTaperedStemGeometry,createLeafGeometry,fallingLeafStateAt,createGrassBladeGeometry,
 stepInsectSwarm,stepBirdFlock
} from "../../src/threejs/d05-vegetation-ecology.mjs";

test("recursive tree creates binary branches with geometric length decay",()=>{
 const branches=generateRecursiveTree({depth:3,length:1,scale:.5,seed:4});
 assert.equal(branches.length,15);
 const first=branches[0].start.distanceTo(branches[0].end);
 const next=branches[1].start.distanceTo(branches[1].end);
 assert.ok(Math.abs(first-1)<1e-12);assert.ok(Math.abs(next-.5)<1e-12);
});
test("L-system rewrites grammar and turtle restores branch state",()=>{
 const sentence=expandLSystem("F",{"F":"F[+F]F[-F]F"},1);
 const segments=interpretLSystem3D(sentence,{stepLength:1,angle:Math.PI/4});
 assert.equal(segments.length,5);
 assert.ok(segments[0].start.distanceTo(segments[0].end)>0);
 assert.throws(()=>expandLSystem("F",{"F":"FFFF"},10,{maxSymbols:20}),RangeError);
});
test("Poisson disk points are deterministic and respect minimum separation",()=>{
 const options={bounds:[0,0,1,1],minDistance:.12,attempts:20,seed:17,maxPoints:200};
 const a=samplePoissonDisk2D(options),b=samplePoissonDisk2D(options);
 assert.deepEqual(a,b);assert.ok(a.length>10);
 for(let i=0;i<a.length;i++)for(let j=i+1;j<a.length;j++)assert.ok(Math.hypot(a[i][0]-a[j][0],a[i][1]-a[j][1])>=.12-1e-10);
});
test("phyllotaxis follows golden-angle radial square-root growth",()=>{
 const points=generatePhyllotaxis(4,{spacing:2});
 assert.deepEqual(points[0],[0,0,0]);
 assert.ok(Math.abs(Math.hypot(points[1][0],points[1][1])-2)<1e-12);
 assert.ok(Math.abs(Math.hypot(points[3][0],points[3][1])-2*Math.sqrt(3))<1e-12);
});
test("tapered stem geometry narrows from base to tip",()=>{
 const g=createTaperedStemGeometry([[0,0,0],[0,1,0],[0,2,0]],{baseRadius:.2,gamma:1,radialSegments:8});
 const p=g.getAttribute("position");
 const r0=Math.hypot(p.getX(0),p.getZ(0));
 const tipIndex=2*9;
 const rt=Math.hypot(p.getX(tipIndex),p.getZ(tipIndex));
 assert.ok(Math.abs(r0-.2)<1e-6);assert.ok(rt<1e-6);
});
test("leaf geometry is a finite parametric blade with tapered ends",()=>{
 const g=createLeafGeometry([[0,0,0],[0,1,0],[0,2,0]],{width:.3,slices:12,across:4});
 assert.equal(g.getAttribute("position").count,65);
 assert.ok(g.boundingBox.max.x-g.boundingBox.min.x>.4);
});
test("falling leaf state is random-access deterministic and includes drift",()=>{
 const args={origin:[0,5,0],velocity:[0,0,0],gravity:9.8,time:1,windAcceleration:[.2,0,.1],seed:3};
 const a=fallingLeafStateAt(args),b=fallingLeafStateAt(args);
 assert.deepEqual(a,b);assert.ok(a.position[1]<5);assert.notDeepEqual(a.rotation,[2,0,0]);
});
test("grass blade geometry bends over time while keeping its base fixed",()=>{
 const a=createGrassBladeGeometry({base:[1,0,2],height:1,width:.1,bend:.2,windAmplitude:.2,time:0,segments:8,across:2});
 const b=createGrassBladeGeometry({base:[1,0,2],height:1,width:.1,bend:.2,windAmplitude:.2,time:1,segments:8,across:2});
 assert.equal(a.getAttribute("position").count,27);
 assert.ok(Math.abs(a.getAttribute("position").getX(0)-1)<1e-12);
 assert.notDeepEqual(Array.from(a.getAttribute("position").array),Array.from(b.getAttribute("position").array));
});
test("insect swarm is deterministic and steers toward a light attractor",()=>{
 const agents=[{position:[0,0,0],velocity:[0,0,0]},{position:[0,1,0],velocity:[0,0,0]}];
 const args={agents,light:[5,0,0],dt:.1,seed:4,stepIndex:2,lightWeight:2,noiseAmplitude:0};
 const a=stepInsectSwarm(args),b=stepInsectSwarm(args);
 assert.deepEqual(a,b);assert.ok(a[0].position[0]>0);
});
test("bird flock combines local boids with leader following and speed cap",()=>{
 const agents=[{position:[0,0,0],velocity:[0,0,0]},{position:[0,1,0],velocity:[0,0,0]}];
 const out=stepBirdFlock({agents,leaderPosition:[10,0,0],dt:.1,leaderWeight:2,maxSpeed:.5});
 assert.ok(out[0].position[0]>0);
 assert.ok(Math.hypot(...out[0].velocity)<=.5+1e-12);
});
