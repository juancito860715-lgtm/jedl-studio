import test from "node:test";
import assert from "node:assert/strict";
import {generateLayeredImpasto,evaluateBrushHeight,createPhasorSpectrum,evaluatePhasorPhase,evaluateErosionProfile,phasorErosionHeight,rk4Trajectory,greedyMeshVoxels} from "../../src/threejs/r31-algorithms.mjs";

test("impasto sampling is seeded, coarse-to-fine and tangent-field driven",()=>{
 const opts={bounds:[0,0,1,1],layers:[{scale:.3,count:8},{scale:.1,count:16}],seed:42,steps:5,stepLength:.02,tangentField:()=>[1,0]};
 const a=generateLayeredImpasto(opts),b=generateLayeredImpasto(opts);
 assert.deepEqual(a.map(s=>s.center),b.map(s=>s.center));
 assert.equal(a.length,24);
 assert.ok(a.slice(0,8).every(s=>s.scale===.3));
 assert.ok(a.slice(8).every(s=>s.scale===.1));
 for(const s of a) for(let i=1;i<s.line.length;i++) assert.ok(s.line[i][0]>s.line[i-1][0]);
 assert.equal(evaluateBrushHeight(a[0],[0,0]),1);
 assert.equal(evaluateBrushHeight(a[0],[2,0]),0);
});
test("spectral Phasor field is deterministic and finite",()=>{
 const a=createPhasorSpectrum({seed:91,components:64,frequency:4,orientation:.3});
 const b=createPhasorSpectrum({seed:91,components:64,frequency:4,orientation:.3});
 assert.deepEqual(a,b);
 const p=evaluatePhasorPhase(a,[.2,-.4]);
 assert.ok(Number.isFinite(p)&&p>=-Math.PI&&p<=Math.PI);
 assert.ok(evaluateErosionProfile(p,{depth:.2,amplitude:1})<=0);
 assert.ok(phasorErosionHeight({base:3,point:[.2,-.4],spectrum:a})<=3);
});
test("RK4 trajectory converges at fourth order on unit circular flow",()=>{
 const field=([x,y])=>[-y,x];
 const exact=[Math.cos(1),Math.sin(1)];
 const coarse=rk4Trajectory(field,[1,0],0,1,10).at(-1);
 const fine=rk4Trajectory(field,[1,0],0,1,20).at(-1);
 const err=x=>Math.hypot(x[0]-exact[0],x[1]-exact[1]);
 assert.ok(err(fine)<err(coarse)/12);
 assert.ok(err(fine)<1e-5);
});
test("3D greedy mesher emits six merged quads for a solid 2x2x2 block",()=>{
 const data=new Array(8).fill("stone");
 const faces=greedyMeshVoxels({data,size:[2,2,2]});
 assert.equal(faces.length,6);
 assert.ok(faces.every(f=>f.material==="stone"&&f.lo.length===3&&f.hi.length===3));
});
test("3D greedy mesher preserves material interfaces",()=>{
 const faces=greedyMeshVoxels({data:["stone","wood"],size:[2,1,1]});
 assert.equal(faces.length,12);
 assert.equal(faces.filter(f=>f.material==="stone"&&f.axis===0&&f.sign===1).length,1);
 assert.equal(faces.filter(f=>f.material==="wood"&&f.axis===0&&f.sign===-1).length,1);
});
test("3D greedy mesher handles empty cells and rejects malformed volumes",()=>{
 assert.equal(greedyMeshVoxels({data:[0,"stone",0],size:[3,1,1]}).length,6);
 assert.throws(()=>greedyMeshVoxels({data:[1],size:[2,2,2]}),/length mismatch/);
});
