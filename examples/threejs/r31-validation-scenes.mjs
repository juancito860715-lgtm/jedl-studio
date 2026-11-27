import * as THREE from "three";
import { impastoHeight, erodedHeight, integrateRk4, greedyRectangles } from "../../tests/threejs/r31_completion_kernels.mjs";

function gridGeometry(n, heightAt, extent=2) {
  const positions=[], indices=[];
  for(let z=0;z<=n;z++) for(let x=0;x<=n;x++) {
    const px=-extent/2+extent*x/n, pz=-extent/2+extent*z/n;
    positions.push(px,heightAt(px,pz),pz);
  }
  for(let z=0;z<n;z++) for(let x=0;x<n;x++) {
    const a=z*(n+1)+x,b=a+1,c=a+n+1,d=c+1;
    indices.push(a,c,b,b,c,d);
  }
  const g=new THREE.BufferGeometry();
  g.setAttribute("position",new THREE.Float32BufferAttribute(positions,3));
  g.setIndex(indices);g.computeVertexNormals();g.computeBoundingSphere();return g;
}
function makeSurface(geometry,color) {
  return new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({color,roughness:.82,metalness:0,side:THREE.DoubleSide}));
}
export function createImpastoValidationScene({segments=24}={}) {
  const scene=new THREE.Scene();scene.name="R31 Impasto deterministic validation";
  const strokes=[[-.8,-.35,.75,.35,.22,.12],[-.65,.55,.65,.55,.13,.07]];
  const geometry=gridGeometry(segments,(x,z)=>impastoHeight([x,z],strokes));
  const mesh=makeSurface(geometry,0xb36b42);mesh.name="impasto-heightfield";scene.add(mesh);
  scene.userData.validation={algorithm:"compact-segment-heightfield",segments,strokes};
  return scene;
}
export function createFlowErosionValidationScene({segments=24}={}) {
  const scene=new THREE.Scene();scene.name="R31 Flow-oriented erosion deterministic validation";
  const geometry=gridGeometry(segments,(x,z)=>{
    const base=.18*Math.sin(x*1.2)*Math.cos(z*.7);
    const slope=Math.min(1,Math.hypot(.216*Math.cos(x*1.2)*Math.cos(z*.7),.126*Math.sin(x*1.2)*Math.sin(z*.7)));
    return erodedHeight(base,[x,z],[1,.25],.025,slope,1.1,.85,.3);
  });
  const mesh=makeSurface(geometry,0x718b58);mesh.name="flow-oriented-erosion-heightfield";scene.add(mesh);
  scene.userData.validation={algorithm:"anisotropic-periodic-detail-prototype",segments,seed:"fixed"};
  return scene;
}
export function createVectorFieldValidationScene({steps=96}={}) {
  const scene=new THREE.Scene();scene.name="R31 RK4 vector-field deterministic validation";
  const points=[];let state=[1,0,0],t=0;const dt=2*Math.PI/steps;
  points.push(new THREE.Vector3(...state));
  for(let i=0;i<steps;i++){state=integrateRk4(([x,y,z])=>[-y,x,.05],state,t,t+dt,1);t+=dt;points.push(new THREE.Vector3(...state));}
  const geometry=new THREE.BufferGeometry().setFromPoints(points);
  const line=new THREE.Line(geometry,new THREE.LineBasicMaterial({color:0x2f83c5}));line.name="rk4-integrated-vector-field-trajectory";scene.add(line);
  scene.userData.validation={algorithm:"classical-rk4",steps,dt};
  return scene;
}
export function createVoxelGreedyValidationScene() {
  const scene=new THREE.Scene();scene.name="R31 Voxel greedy meshing deterministic validation";
  const mask=[["stone","stone","stone"],["stone","stone","wood"],["stone","stone","wood"]];
  const rects=greedyRectangles(mask),positions=[],indices=[],colors=[];
  const palette={stone:[.48,.52,.58],wood:[.48,.29,.14]};
  for(const [x0,z0,x1,z1,key] of rects){
    const base=positions.length/3;
    positions.push(x0,0,z0,x1,0,z0,x1,0,z1,x0,0,z1);
    indices.push(base,base+2,base+1,base,base+3,base+2);
    const c=palette[key];for(let i=0;i<4;i++)colors.push(...c);
  }
  const geometry=new THREE.BufferGeometry();
  geometry.setAttribute("position",new THREE.Float32BufferAttribute(positions,3));
  geometry.setAttribute("color",new THREE.Float32BufferAttribute(colors,3));
  geometry.setIndex(indices);geometry.computeVertexNormals();geometry.computeBoundingSphere();
  const mesh=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({vertexColors:true,roughness:.9,side:THREE.DoubleSide}));
  mesh.name="greedy-merged-voxel-top-faces";scene.add(mesh);
  scene.userData.validation={algorithm:"row-major-greedy-rectangles",sourceMask:mask,rectangleCount:rects.length,coveredCells:mask.flat().length};
  return scene;
}
export function createAllR31ValidationScenes() {
  return [createImpastoValidationScene(),createFlowErosionValidationScene(),createVectorFieldValidationScene(),createVoxelGreedyValidationScene()];
}
