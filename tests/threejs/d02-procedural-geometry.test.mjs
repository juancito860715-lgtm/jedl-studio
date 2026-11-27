import test from "node:test";
import assert from "node:assert/strict";
import * as THREE from "three";
import {
 createPrimitiveGeometry,createValidatedBufferGeometry,createParametricSurface,
 createRevolutionSurface,createExtrusionGeometry,createParallelTransportSweep,
 loopSubdivideGeometry,generateFractalBranches,createMarchingCubes,applyDeterministicMicroJitter
} from "../../src/threejs/d02-procedural-geometry.mjs";

test("primitives generate finite BufferGeometry and bounds",()=>{
 for(const kind of ["box","sphere","cylinder","torus"]){
  const g=createPrimitiveGeometry(kind); assert.ok(g.getAttribute("position").count>0); assert.ok(g.boundingSphere.radius>0);
 }
});
test("manual BufferGeometry validates indices and attribute cardinality",()=>{
 const g=createValidatedBufferGeometry({positions:[0,0,0,1,0,0,0,1,0],indices:[0,1,2],uvs:[0,0,1,0,0,1]});
 assert.equal(g.index.count,3);
 assert.throws(()=>createValidatedBufferGeometry({positions:[0,0,0,1,0,0,0,1,0],indices:[0,1,3]}),RangeError);
 assert.throws(()=>createValidatedBufferGeometry({positions:[0,0,0],uvs:[0,0,1,1]}),RangeError);
});
test("parametric surface samples grid and creates indexed triangles",()=>{
 const g=createParametricSurface((u,v)=>new THREE.Vector3(u,v,Math.sin(Math.PI*u)*Math.sin(Math.PI*v)),4,3);
 assert.equal(g.getAttribute("position").count,20); assert.equal(g.index.count,72);
 assert.ok(g.getAttribute("normal").count===20);
});
test("surface of revolution closes angular seam",()=>{
 const g=createRevolutionSurface([[1,0],[1,2],[0.5,3]],12);
 const p=g.getAttribute("position");
 assert.ok(new THREE.Vector3().fromBufferAttribute(p,0).distanceTo(new THREE.Vector3().fromBufferAttribute(p,12))<1e-6);
 assert.equal(g.index.count,144);
});
test("extrusion creates a finite closed profile mesh with expected depth",()=>{
 const g=createExtrusionGeometry([[0,0],[2,0],[2,1],[0,1]],3,2);
 assert.ok(g.getAttribute("position").count>0);
 assert.ok(Math.abs(g.boundingBox.max.z-g.boundingBox.min.z-3)<1e-6);
});
test("parallel-transport sweep maintains finite geometry and stable frames",()=>{
 const g=createParallelTransportSweep([[0,0,0],[1,0,0],[1,1,0],[1,1,1]],0.2,8);
 assert.equal(g.getAttribute("position").count,36);
 assert.ok(g.boundingSphere.radius>0);
});
test("Loop subdivision refines each triangle into four",()=>{
 const g=createValidatedBufferGeometry({positions:[0,0,0,1,0,0,0,1,0],indices:[0,1,2]});
 const s=loopSubdivideGeometry(g);
 assert.equal(s.getAttribute("position").count,6); assert.equal(s.index.count,12);
 assert.ok(s.getAttribute("position").getX(0)>0);
});
test("fractal branches are deterministic and grow by binary levels",()=>{
 const a=generateFractalBranches({depth:3,seed:7}),b=generateFractalBranches({depth:3,seed:7});
 assert.equal(a.length,15); assert.deepEqual(a.map(x=>x.end.toArray()),b.map(x=>x.end.toArray()));
 assert.equal(generateFractalBranches({depth:0}).length,1);
});
test("MarchingCubes addon builds a non-empty isosurface",()=>{
 const mc=createMarchingCubes(12,new THREE.MeshNormalMaterial(),[[0.5,0.5,0.5,1,12]]);
 assert.equal(mc.isMarchingCubes,true);
 assert.ok(mc.geometry.getAttribute("position").count>0);
});
test("microjitter is reproducible for same seed/frame and changes with frame",()=>{
 const g=new THREE.BoxGeometry(1,1,1);
 const a=applyDeterministicMicroJitter(g,0.02,3,9),b=applyDeterministicMicroJitter(g,0.02,3,9),c=applyDeterministicMicroJitter(g,0.02,4,9);
 const p=a.getAttribute("position"),q=b.getAttribute("position"),r=c.getAttribute("position");
 assert.deepEqual(Array.from(p.array),Array.from(q.array));
 assert.notDeepEqual(Array.from(p.array),Array.from(r.array));
 assert.deepEqual(Array.from(g.getAttribute("position").array),Array.from(new THREE.BoxGeometry(1,1,1).getAttribute("position").array));
});
