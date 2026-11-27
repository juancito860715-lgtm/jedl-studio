import test from "node:test";
import assert from "node:assert/strict";
import * as THREE from "three";
import {
 evaluateSmoothUnionSdf,createAnatomicalVolumeMesh,evaluateMetaballField,createMetaballMesh,
 createMonotoneAnatomicalProfile,linearBlendSkinning,dualQuaternionFromRigidTransform,
 dualQuaternionSkinning,dualQuaternionSkinningBounded,computePupilPosition,solveFabrik
} from "../../src/threejs/d03-character-geometry.mjs";

test("smooth SDF union is exact at k=0 and bounded blend at k>0",()=>{
 const a=p=>p.length()-1,b=p=>p.clone().sub(new THREE.Vector3(1,0,0)).length()-1;
 assert.equal(evaluateSmoothUnionSdf([a,b],[0,0,0],0),-1);
 assert.ok(evaluateSmoothUnionSdf([a,b],[0.5,0,0],0.2)<0);
 assert.throws(()=>evaluateSmoothUnionSdf([], [0,0,0]),TypeError);
});
test("anatomical SDF volume extracts a mesh from supplied signed fields",()=>{
 const sphere=p=>p.length()-0.65;
 const mesh=createAnatomicalVolumeMesh({fields:[sphere],bounds:[-1,-1,-1,1,1,1],resolution:12,smoothness:0});
 assert.ok(mesh.isMarchingCubes);
 assert.ok(mesh.geometry.drawRange.count>0);
 assert.ok(mesh.geometry.boundingSphere.radius>0);
});
test("metaball field sums inverse-square contributions and extracts isosurface",()=>{
 const balls=[{center:[-0.25,0,0],radius:0.5},{center:[0.25,0,0],radius:0.5}];
 assert.ok(evaluateMetaballField([0,0,0],balls)>evaluateMetaballField([1,0,0],balls));
 const mesh=createMetaballMesh({balls,bounds:[-1,-1,-1,1,1,1],resolution:12,iso:1});
 assert.ok(mesh.geometry.drawRange.count>0);
});
test("monotone anatomical profile interpolates keys without negative radii",()=>{
 const profile=createMonotoneAnatomicalProfile([{s:0,radius:0.1},{s:1,radius:0.5},{s:2,radius:0.2},{s:3,radius:0.1}]);
 assert.equal(profile.radiusAt(0),0.1);
 assert.equal(profile.radiusAt(1),0.5);
 for(let i=0;i<=300;i++)assert.ok(profile.radiusAt(i/100)>=0);
 assert.equal(profile.radiusAt(-2),0.1);
 assert.equal(profile.radiusAt(5),0.1);
 assert.throws(()=>createMonotoneAnatomicalProfile([{s:1,radius:1},{s:1,radius:2}]),RangeError);
});
test("linear blend skinning preserves identity and applies weighted translation",()=>{
 const matrices=[new THREE.Matrix4(),new THREE.Matrix4().makeTranslation(2,0,0)];
 const result=linearBlendSkinning({positions:[[1,0,0]],influences:[[{bone:0,weight:0.25},{bone:1,weight:0.75}]],skinMatrices:matrices});
 assert.ok(Math.abs(result.positions[0][0]-2.5)<1e-9);
 const identity=linearBlendSkinning({positions:[[1,2,3]],influences:[[{bone:0,weight:1}]],skinMatrices:[new THREE.Matrix4()]});
 assert.deepEqual(identity.positions,[[1,2,3]]);
});
test("dual quaternion skinning blends rigid transforms without losing translation",()=>{
 const dq=[dualQuaternionFromRigidTransform(new THREE.Quaternion(),new THREE.Vector3(0,0,0)),
           dualQuaternionFromRigidTransform(new THREE.Quaternion(),new THREE.Vector3(2,0,0))];
 const out=dualQuaternionSkinning({positions:[[1,0,0]],influences:[[{bone:0,weight:0.5},{bone:1,weight:0.5}]],dualBones:dq});
 assert.ok(Math.abs(out.positions[0][0]-2)<1e-8);
 assert.ok(Math.abs(out.positions[0][1])<1e-8);
});
test("bounded DQS keeps top influences and reports discarded weight",()=>{
 const dq=[0,1,2].map(x=>dualQuaternionFromRigidTransform(new THREE.Quaternion(),new THREE.Vector3(x,0,0)));
 const out=dualQuaternionSkinningBounded({positions:[[0,0,0]],influences:[[{bone:0,weight:0.6},{bone:1,weight:0.3},{bone:2,weight:0.1}]],dualBones:dq,maxInfluences:2});
 assert.ok(Math.abs(out.discardedWeight[0]-0.1)<1e-9);
 assert.ok(Math.abs(out.positions[0][0]-0.3333333333)<1e-8);
});
test("pupil projection stays in eye plane and uses fallback for zero gaze",()=>{
 const p=computePupilPosition({eyeCenter:[0,0,0],target:[1,0,2],normal:[0,0,1],maxOffset:0.2});
 assert.ok(Math.abs(p.position[2])<1e-9);
 assert.ok(Math.abs(p.position[0]-0.2)<1e-9);
 const f=computePupilPosition({eyeCenter:[0,0,0],target:[0,0,0],normal:[0,0,1],maxOffset:0.1});
 assert.ok(Math.abs(f.position[0]-0.1)<1e-9);
});
test("FABRIK converges to reachable target while preserving segment lengths",()=>{
 const result=solveFabrik({positions:[[0,0,0],[1,0,0],[2,0,0]],lengths:[1,1],target:[1,1,0],tolerance:1e-5,maxIterations:100});
 assert.equal(result.reachable,true);
 assert.ok(result.error<=1e-5);
 for(let i=0;i<2;i++)assert.ok(Math.abs(new THREE.Vector3(...result.positions[i]).distanceTo(new THREE.Vector3(...result.positions[i+1]))-1)<1e-8);
});
test("FABRIK extends unreachable chain to maximum reach",()=>{
 const result=solveFabrik({positions:[[0,0,0],[1,0,0],[2,0,0]],lengths:[1,1],target:[5,0,0]});
 assert.equal(result.reachable,false);
 assert.deepEqual(result.positions,[[0,0,0],[1,0,0],[2,0,0]]);
});
