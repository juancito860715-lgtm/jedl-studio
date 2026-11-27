import test from "node:test";
import assert from "node:assert/strict";
import * as THREE from "three";
import {
 expandShapeGrammar,assembleModularBuilding,createGableRoofGeometry,createCurvedRoofGeometry,
 createArchGeometry,createFlutedColumnGeometry,createParametricStaircase,createBridgeAlongCurve,
 createMasonryWall,createProceduralFacade,createFlagState,stepFlag,createFlagGeometry,createPendulumLantern
} from "../../src/threejs/d07-architecture.mjs";

test("shape grammar expands rules with parameters and enforces symbol budget",()=>{
 const out=expandShapeGrammar([{symbol:"B",params:{floors:2}}],{B:t=>[{symbol:"F",params:{floors:t.params.floors}},{symbol:"R"}],F:[{symbol:"W"}]},2);
 assert.deepEqual(out.map(x=>x.symbol),["W","W","R"]);
 assert.throws(()=>expandShapeGrammar([{symbol:"A"}],{A:[{symbol:"A"},{symbol:"A"}]},8,{maxSymbols:20}),RangeError);
});
test("modular building groups repeated modules into InstancedMesh batches",()=>{
 const geometry=new THREE.BoxGeometry(1,1,1),material=new THREE.MeshBasicMaterial();
 const group=assembleModularBuilding({modules:{pillar:{geometry,material}},placements:[{type:"pillar",position:[0,0,0]},{type:"pillar",position:[2,0,0]}]});
 assert.equal(group.children.length,1);assert.equal(group.children[0].count,2);
});
test("gable roof builds two pitched planes with correct bounds",()=>{
 const g=createGableRoofGeometry({width:4,depth:3,baseY:2,pitch:.5,segments:4});
 assert.ok(g.getAttribute("position").count>0);assert.ok(Math.abs(g.boundingBox.max.y-3)<1e-6);
});
test("curved roof samples a finite parabolic profile",()=>{
 const g=createCurvedRoofGeometry({width:4,depth:3,baseY:1,curvature:.2,slices:8,stacks:2});
 assert.ok(g.getAttribute("position").count>0);assert.ok(g.boundingBox.max.y>1);
});
test("arch geometry has a closed extruded ring profile",()=>{
 const g=createArchGeometry({radius:1,thickness:.3,depth:.4,segments:24,bevel:.01});
 assert.ok(g.getAttribute("position").count>0);assert.ok(g.boundingBox.max.y>1);
});
test("fluted column varies radial profile periodically",()=>{
 const g=createFlutedColumnGeometry({radius:.5,height:3,flutes:8,amplitude:.05,segments:32,heightSegments:4});
 assert.ok(g.getAttribute("position").count>0);assert.ok(g.boundingBox.max.y>=3-1e-6);
});
test("parametric staircase places one instanced tread per step",()=>{
 const mesh=createParametricStaircase({steps:7,rise:.2,run:.3,width:1});
 assert.equal(mesh.count,7);assert.ok(mesh.boundingSphere.radius>0);
});
test("bridge follows a curved centerline and builds two railings",()=>{
 const group=createBridgeAlongCurve([[0,0,0],[2,1,0],[4,0,1]],{width:2,segments:12});
 assert.equal(group.children.length,3);assert.ok(group.children[0].geometry.getAttribute("position").count>0);
});
test("masonry wall generates deterministic beveled blocks",()=>{
 const a=createMasonryWall({width:4,height:2,columns:4,rows:2,seed:5,bevel:.03});
 const b=createMasonryWall({width:4,height:2,columns:4,rows:2,seed:5,bevel:.03});
 assert.equal(a.children.length,8);assert.deepEqual(a.userData.blocks,b.userData.blocks);
 assert.ok(a.children[0].geometry.getAttribute("position").count>0);
});
test("procedural facade creates grid openings and a ground-floor door",()=>{
 const facade=createProceduralFacade({width:8,height:10,bays:4,floors:5});
 const openings=facade.userData.openings;
 assert.equal(openings.length,20);assert.equal(openings.filter(x=>x.type==="door").length,1);
 assert.equal(openings.filter(x=>x.type==="window").length,19);
});
test("flag XPBD state pins the top edge and deforms under gravity and wind",()=>{
 const state=createFlagState({widthSegments:4,heightSegments:3,spacing:.2});
 const next=stepFlag(state,{dt:1/60,wind:[1,0,0],iterations:4});
 for(let i=0;i<=4;i++)assert.deepEqual(next.positions[i],state.anchors[i]);
 assert.ok(next.positions[5][1]<state.positions[5][1]);
 const geometry=createFlagGeometry(next);assert.equal(geometry.getAttribute("position").count,20);
});
test("pendulum lantern uses small-angle analytic frequency and fixed length",()=>{
 const s=createPendulumLantern({pivot:[1,2,3],length:2,gravity:9.81,amplitude:.1,time:1});
 const distance=Math.hypot(s.position[0]-1,s.position[1]-2,s.position[2]-3);
 assert.ok(Math.abs(distance-2)<1e-12);assert.ok(Number.isFinite(s.angularVelocity));
});
