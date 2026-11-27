import test from "node:test";
import assert from "node:assert/strict";
import * as THREE from "three";
import {
 valueNoise2D,createHeightfieldGeometry,ridgedMultifractal2D,domainWarp2D,cascadeTerrainDetail,
 hydraulicErosionStep,thermalErosionStep,classifyBiome,evaluateHairMicrofacetApproximation
} from "../../src/threejs/d06-terrain-erosion.mjs";

test("heightfield builds indexed grid with finite normals and expected vertex count",()=>{
 const g=createHeightfieldGeometry({width:4,depth:2,segmentsX:4,segmentsZ:2,heightFn:(x,z)=>x*x*.1+z*.2});
 assert.equal(g.getAttribute("position").count,15);assert.equal(g.index.count,48);
 const n=g.getAttribute("normal");for(let i=0;i<n.count;i++)assert.ok(Number.isFinite(n.getY(i)));
});
test("seeded value noise and ridged multifractal are deterministic",()=>{
 assert.equal(valueNoise2D(1.25,-2.5,9),valueNoise2D(1.25,-2.5,9));
 const a=ridgedMultifractal2D(2,3,{seed:4,octaves:5}),b=ridgedMultifractal2D(2,3,{seed:4,octaves:5});
 assert.equal(a,b);assert.ok(a>=0);
 assert.notEqual(a,ridgedMultifractal2D(2,3,{seed:5,octaves:5}));
});
test("domain warping deterministically offsets sample coordinates",()=>{
 const a=domainWarp2D(1,2,{seed:7,warpAmplitude:2,frequency:.5});
 const b=domainWarp2D(1,2,{seed:7,warpAmplitude:2,frequency:.5});
 assert.deepEqual(a,b);assert.notEqual(a.x,1);assert.notEqual(a.z,2);
});
test("detail cascade adds reproducible multi-octave displacement",()=>{
 const a=cascadeTerrainDetail(1,2,{seed:5,octaves:4,amplitude:2}),b=cascadeTerrainDetail(1,2,{seed:5,octaves:4,amplitude:2});
 assert.equal(a,b);assert.ok(Number.isFinite(a));
});
test("hydraulic erosion conserves terrain plus sediment and water on closed grid",()=>{
 const heightMap=Float64Array.from([3,2,1,3,2,1,3,2,1]),waterMap=Float64Array.from([1,1,1,1,1,1,1,1,1]),sedimentMap=new Float64Array(9);
 const totalBefore=heightMap.reduce((a,b)=>a+b,0)+sedimentMap.reduce((a,b)=>a+b,0),waterBefore=waterMap.reduce((a,b)=>a+b,0);
 const out=hydraulicErosionStep({heightMap,waterMap,sedimentMap,width:3,height:3,dt:.1,flowRate:.5,capacityCoefficient:1,erosionRate:.2,depositionRate:.2});
 const totalAfter=out.heightMap.reduce((a,b)=>a+b,0)+out.sedimentMap.reduce((a,b)=>a+b,0);
 assert.ok(Math.abs(totalBefore-totalAfter)<1e-9);
 assert.ok(Math.abs(waterBefore-out.waterMap.reduce((a,b)=>a+b,0))<1e-9);
 assert.ok(out.heightMap.some((v,i)=>v!==heightMap[i]));
});
test("thermal erosion lowers excessive slopes and conserves total height",()=>{
 const h=Float64Array.from([10,0,0,0,0,0,0,0,0]),before=h.reduce((a,b)=>a+b,0);
 const out=thermalErosionStep({heightMap:h,width:3,height:3,cellSize:1,talusAngle:.1,transferFraction:.2,iterations:3});
 assert.ok(out[0]<10);assert.ok(Math.abs(out.reduce((a,b)=>a+b,0)-before)<1e-9);
});
test("biome classifier selects wetland and alpine under contrasting climates",()=>{
 assert.equal(classifyBiome({altitude:.1,slope:.05,moisture:.95,exposure:.2,seed:1}).biome,"wetland");
 assert.equal(classifyBiome({altitude:.95,slope:.2,moisture:.05,exposure:.9,seed:1}).biome,"alpine");
});
test("hair microfacet approximation returns finite R, TT and TRT lobes with Beer-Lambert attenuation",()=>{
 const result=evaluateHairMicrofacetApproximation({wi:[0,0,1],wo:[0,0,1],tangent:[0,1,0],radius:.04,absorption:2});
 for(const key of ["R","TT","TRT","total"])assert.ok(result[key].every(v=>Number.isFinite(v)&&v>=0));
 assert.ok(result.attenuation>0&&result.attenuation<1);
 assert.equal(result.approximation,true);
});
