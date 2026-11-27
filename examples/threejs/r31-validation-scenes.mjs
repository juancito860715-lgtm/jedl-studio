import * as THREE from "three";
import { generateLayeredImpasto, evaluatePhasorPhase, createPhasorSpectrum, phasorErosionHeight, rk4Trajectory, greedyMeshVoxels } from "../../src/threejs/r31-algorithms.mjs";

function makeHeightfield(n,heightAt,extent=2){
 const positions=[],indices=[];
 for(let z=0;z<=n;z++)for(let x=0;x<=n;x++){const px=-extent/2+extent*x/n,pz=-extent/2+extent*z/n;positions.push(px,heightAt(px,pz),pz);}
 for(let z=0;z<n;z++)for(let x=0;x<n;x++){const a=z*(n+1)+x,b=a+1,c=a+n+1,d=c+1;indices.push(a,c,b,b,c,d);}
 const g=new THREE.BufferGeometry();g.setAttribute("position",new THREE.Float32BufferAttribute(positions,3));g.setIndex(indices);g.computeVertexNormals();g.computeBoundingSphere();return g;
}
function surface(geometry,color){return new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({color,roughness:.82,metalness:0,side:THREE.DoubleSide}));}
function segmentDistance(p,a,b){const dx=b[0]-a[0],dz=b[1]-a[1],d=dx*dx+dz*dz;if(d<1e-12)return Math.hypot(p[0]-a[0],p[1]-a[1]);const t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dz)/d));return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dz);}
export function createImpastoValidationScene({segments=24}={}){
 const scene=new THREE.Scene();scene.name="R31 layered multi-scale impasto";
 const strokes=generateLayeredImpasto({bounds:[-1,-1,1,1],layers:[{scale:.22,count:12},{scale:.11,count:24},{scale:.055,count:48}],seed:2026,steps:9,stepLength:.035,tangentField:([x,z])=>[-.25*z,1+.15*x]});
 const heightAt=(x,z)=>{let h=0;for(const s of strokes){const radius=s.scale*.5;let d=Infinity;for(let i=1;i<s.line.length;i++)d=Math.min(d,segmentDistance([x,z],s.line[i-1],s.line[i]));const q=Math.max(0,1-(d/radius)**2);h+=s.scale*.16*q*q;}return h;};
 const mesh=surface(makeHeightfield(segments,heightAt),0xb36b42);mesh.name="layered-impasto-heightfield";scene.add(mesh);
 scene.userData.validation={algorithm:"coarse-to-fine incremental low-discrepancy sampling + tangent streamlines + brush height profiles",seed:2026,segments,strokeCount:strokes.length,layerCounts:[12,24,48]};
 return scene;
}
export function createFlowErosionValidationScene({segments=24}={}){
 const scene=new THREE.Scene();scene.name="R31 spectral Phasor flow-oriented erosion";
 const spectrum=createPhasorSpectrum({seed:31415,components:64,frequency:3.5,orientation:.62,bandwidth:.18,radial:.04});
 const base=(x,z)=>.18*Math.sin(x*1.2)*Math.cos(z*.7);
 const heightAt=(x,z)=>{const b=base(x,z),gx=.216*Math.cos(x*1.2)*Math.cos(z*.7),gz=-.126*Math.sin(x*1.2)*Math.sin(z*.7),slope=Math.min(1,Math.hypot(gx,gz));const atten=.25+.75*slope;return phasorErosionHeight({base:b,point:[x,z],spectrum,depth:.12,rounding:.08,amplitude:1,attenuation:atten});};
 const mesh=surface(makeHeightfield(segments,heightAt),0x718b58);mesh.name="phasor-flow-erosion-heightfield";scene.add(mesh);
 scene.userData.validation={algorithm:"finite spectral complex-Gaussian Phasor field with terrain-slope amplitude control",segments,seed:spectrum.seed,components:spectrum.waves.length,phaseSample:evaluatePhasorPhase(spectrum,[.25,-.5])};
 return scene;
}
export function createVectorFieldValidationScene({steps=96}={}){
 const scene=new THREE.Scene();scene.name="R31 RK4 vector-field trajectory";
 const points=rk4Trajectory(([x,y,z])=>[-y,x,.05], [1,0,0],0,2*Math.PI,steps).map(p=>new THREE.Vector3(...p));
 const geometry=new THREE.BufferGeometry().setFromPoints(points);const line=new THREE.Line(geometry,new THREE.LineBasicMaterial({color:0x2f83c5}));line.name="rk4-integrated-vector-field-trajectory";scene.add(line);
 scene.userData.validation={algorithm:"classical fourth-order Runge-Kutta trajectory integration",steps,start:0,end:2*Math.PI,stepSize:2*Math.PI/steps,pointCount:points.length};
 return scene;
}
function voxelGeometry(quads){
 const positions=[],colors=[],indices=[],palette={stone:[.48,.52,.58],wood:[.48,.29,.14],grass:[.25,.55,.22]};
 for(const q of quads){const {axis,sign,lo,hi,material}=q,u=(axis+1)%3,v=(axis+2)%3;
  const p0=lo.slice(),p1=lo.slice(),p2=hi.slice(),p3=lo.slice();p1[u]=hi[u];p3[v]=hi[v];
  const face=sign>0?[p0,p1,p2,p3]:[p0,p3,p2,p1],base=positions.length/3;
  for(const p of face)positions.push(...p);
  const color=palette[material]??[.7,.2,.7];for(let i=0;i<4;i++)colors.push(...color);
  indices.push(base,base+1,base+2,base,base+2,base+3);
 }
 const g=new THREE.BufferGeometry();g.setAttribute("position",new THREE.Float32BufferAttribute(positions,3));g.setAttribute("color",new THREE.Float32BufferAttribute(colors,3));g.setIndex(indices);g.computeVertexNormals();g.computeBoundingSphere();return g;
}
export function createVoxelGreedyValidationScene(){
 const scene=new THREE.Scene();scene.name="R31 3D voxel greedy meshing";
 const size=[3,3,2],data=[];
 for(let z=0;z<size[2];z++)for(let y=0;y<size[1];y++)for(let x=0;x<size[0];x++)data.push(x===2&&z===1?"wood":"stone");
 const quads=greedyMeshVoxels({data,size}),geometry=voxelGeometry(quads);
 const mesh=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({vertexColors:true,roughness:.9,side:THREE.DoubleSide}));mesh.name="greedy-merged-3d-voxel-faces";scene.add(mesh);
 scene.userData.validation={algorithm:"3D axis-sweep greedy meshing with material-aware face merging",sourceDimensions:size,sourceVoxelCount:data.length,rectangleCount:quads.length,quadCount:quads.length,triangleCount:quads.length*2,coveredBoundaryFaces:quads.length};
 return scene;
}
export function createAllR31ValidationScenes(){return [createImpastoValidationScene(),createFlowErosionValidationScene(),createVectorFieldValidationScene(),createVoxelGreedyValidationScene()];}
