import * as THREE from "three";
import { generateFractalBranches } from "./d03-character-geometry.mjs";
import { createParallelTransportSweep, createParametricSurface } from "./d02-procedural-geometry.mjs";
import { computeBoidsAcceleration, semiImplicitEulerStep, particlePositionAt } from "./d04-motion-simulation.mjs";

const EPS=1e-10;
function finite(v,name){if(!Number.isFinite(v))throw new RangeError(name+" must be finite");}
function vector(v,name){const a=Array.from(v);if(a.length!==3||!a.every(Number.isFinite))throw new RangeError(name+" must be a finite 3D vector");return a;}
function mulberry32(seed){let a=seed>>>0;return()=>{a=(a+0x6D2B79F5)>>>0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296;};}

export function generateRecursiveTree(options={}){
 const {origin=[0,0,0],direction=[0,1,0],length=1,depth=4,branchAngle=Math.PI/5,scale=.7,seed=1}=options;
 if(!(scale>0&&scale<1))throw new RangeError("scale must be in (0,1)");
 return generateFractalBranches({origin,direction,length,depth,branchAngle,shrink:scale,seed});
}

export function expandLSystem(axiom,rules,iterations,{maxSymbols=1000000}={}){
 if(typeof axiom!=="string"||!axiom.length||!rules||typeof rules!=="object"||
   !Number.isInteger(iterations)||iterations<0||!Number.isInteger(maxSymbols)||maxSymbols<1)throw new RangeError("invalid L-system configuration");
 let current=axiom;
 for(let n=0;n<iterations;n++){
  let next="";
  for(const symbol of current)next+=Object.prototype.hasOwnProperty.call(rules,symbol)?rules[symbol]:symbol;
  if(next.length>maxSymbols)throw new RangeError("L-system expansion exceeds maxSymbols");
  current=next;
 }
 return current;
}

export function interpretLSystem3D(sentence,{origin=[0,0,0],direction=[0,1,0],stepLength=1,angle=Math.PI/6,drawSymbols="F"}={}){
 if(typeof sentence!=="string"||!(Number.isFinite(stepLength)&&stepLength>0)||!Number.isFinite(angle))throw new RangeError("invalid turtle parameters");
 const start=new THREE.Vector3(...vector(origin,"origin")),dir=new THREE.Vector3(...vector(direction,"direction"));
 if(dir.lengthSq()<EPS)throw new RangeError("direction must be nonzero");
 const up=new THREE.Vector3(0,1,0),orientation=new THREE.Quaternion().setFromUnitVectors(up,dir.normalize());
 const stack=[],segments=[];
 const rotate=(axis,sign)=>orientation.multiply(new THREE.Quaternion().setFromAxisAngle(axis,sign*angle)).normalize();
 let position=start.clone();
 for(const symbol of sentence){
  if(drawSymbols.includes(symbol)){
   const forward=new THREE.Vector3(0,1,0).applyQuaternion(orientation).normalize();
   const end=position.clone().addScaledVector(forward,stepLength);
   segments.push({start:position.clone(),end:end.clone()});position=end;
  }else if(symbol==="f"){
   const forward=new THREE.Vector3(0,1,0).applyQuaternion(orientation).normalize();position.addScaledVector(forward,stepLength);
  }else if(symbol==="+")rotate(new THREE.Vector3(0,0,1),1);
  else if(symbol==="-")rotate(new THREE.Vector3(0,0,1),-1);
  else if(symbol==="&")rotate(new THREE.Vector3(1,0,0),1);
  else if(symbol==="^")rotate(new THREE.Vector3(1,0,0),-1);
  else if(symbol==="\\")rotate(new THREE.Vector3(0,1,0),1);
  else if(symbol==="/")rotate(new THREE.Vector3(0,1,0),-1);
  else if(symbol==="[")stack.push({position:position.clone(),orientation:orientation.clone()});
  else if(symbol==="]"){
   const state=stack.pop();if(!state)throw new RangeError("L-system branch stack underflow");
   position.copy(state.position);orientation.copy(state.orientation);
  }
 }
 if(stack.length)throw new RangeError("L-system branch stack not balanced");
 return segments;
}

export function samplePoissonDisk2D({bounds=[0,0,1,1],minDistance=.1,attempts=30,seed=1,maxPoints=10000}={}){
 if(!Array.isArray(bounds)||bounds.length!==4||!bounds.every(Number.isFinite)||!(bounds[2]>bounds[0]&&bounds[3]>bounds[1])||
   !(Number.isFinite(minDistance)&&minDistance>0)||!Number.isInteger(attempts)||attempts<1||
   !Number.isInteger(seed)||!Number.isInteger(maxPoints)||maxPoints<1)throw new RangeError("invalid Poisson-disk parameters");
 const [xmin,ymin,xmax,ymax]=bounds,r=minDistance,cell=r/Math.SQRT2,nx=Math.ceil((xmax-xmin)/cell),ny=Math.ceil((ymax-ymin)/cell);
 const grid=new Int32Array(nx*ny);grid.fill(-1);
 const points=[],active=[],rand=mulberry32(seed),cellIndex=(x,y)=>x+nx*y;
 const add=p=>{const i=points.length;points.push(p);active.push(i);grid[cellIndex(Math.min(nx-1,Math.floor((p[0]-xmin)/cell)),Math.min(ny-1,Math.floor((p[1]-ymin)/cell)))]=i;};
 add([xmin+rand()*(xmax-xmin),ymin+rand()*(ymax-ymin)]);
 while(active.length&&points.length<maxPoints){
  const slot=Math.floor(rand()*active.length),base=points[active[slot]];let found=false;
  for(let k=0;k<attempts;k++){
   const radius=r*Math.sqrt(1+3*rand()),theta=2*Math.PI*rand();
   const p=[base[0]+radius*Math.cos(theta),base[1]+radius*Math.sin(theta)];
   if(p[0]<xmin||p[0]>=xmax||p[1]<ymin||p[1]>=ymax)continue;
   const gx=Math.floor((p[0]-xmin)/cell),gy=Math.floor((p[1]-ymin)/cell);let valid=true;
   for(let y=Math.max(0,gy-2);y<=Math.min(ny-1,gy+2)&&valid;y++)for(let x=Math.max(0,gx-2);x<=Math.min(nx-1,gx+2);x++){
    const id=grid[cellIndex(x,y)];if(id>=0&&Math.hypot(points[id][0]-p[0],points[id][1]-p[1])<r){valid=false;break;}
   }
   if(valid){add(p);found=true;break;}
  }
  if(!found)active.splice(slot,1);
 }
 return points;
}

export function generatePhyllotaxis(count,{spacing=1,goldenAngle=Math.PI*(3-Math.sqrt(5)),origin=[0,0,0]}={}){
 if(!Number.isInteger(count)||count<0||!(Number.isFinite(spacing)&&spacing>=0)||!Number.isFinite(goldenAngle))throw new RangeError("invalid phyllotaxis parameters");
 const o=vector(origin,"origin"),out=[];
 for(let n=0;n<count;n++){
  const radius=spacing*Math.sqrt(n),theta=n*goldenAngle;
  out.push([o[0]+radius*Math.cos(theta),o[1]+radius*Math.sin(theta),o[2]]);
 }
 return out;
}

export function createTaperedStemGeometry(pointsInput,{baseRadius=.1,gamma=1,radialSegments=8}={}){
 if(!(Number.isFinite(baseRadius)&&baseRadius>0&&Number.isFinite(gamma)&&gamma>0)||!Number.isInteger(radialSegments)||radialSegments<3)throw new RangeError("invalid stem profile");
 const points=pointsInput.map(p=>vector(p,"stem point"));
 if(points.length<2)throw new RangeError("stem needs at least two points");
 const geometry=createParallelTransportSweep(points,1,radialSegments),position=geometry.getAttribute("position"),ring=radialSegments+1;
 for(let i=0;i<points.length;i++){
  const s=i/(points.length-1),radius=baseRadius*Math.pow(1-s,gamma);
  for(let j=0;j<ring;j++){
   const index=i*ring+j,c=points[i];
   position.setXYZ(index,c[0]+(position.getX(index)-c[0])*radius,c[1]+(position.getY(index)-c[1])*radius,c[2]+(position.getZ(index)-c[2])*radius);
  }
 }
 position.needsUpdate=true;geometry.computeVertexNormals();geometry.computeBoundingBox();geometry.computeBoundingSphere();
 return geometry;
}

export function createLeafGeometry(controlPoints,{width=.25,shapeExponent=.8,veinHeight=.01,slices=24,across=8}={}){
 if(!Array.isArray(controlPoints)||controlPoints.length<2||!(Number.isFinite(width)&&width>0&&Number.isFinite(shapeExponent)&&shapeExponent>0)||
   !Number.isFinite(veinHeight)||!Number.isInteger(slices)||slices<2||!Number.isInteger(across)||across<2)throw new RangeError("invalid leaf geometry parameters");
 const curve=new THREE.CatmullRomCurve3(controlPoints.map(p=>new THREE.Vector3(...vector(p,"leaf control point"))));
 return createParametricSurface((u,v)=>{
  const center=curve.getPoint(u),tangent=curve.getTangent(u).normalize();
  let side=new THREE.Vector3(0,0,1).cross(tangent);
  if(side.lengthSq()<EPS)side=new THREE.Vector3(1,0,0).cross(tangent);
  side.normalize();
  const halfWidth=width*Math.pow(Math.max(0,Math.sin(Math.PI*u)),shapeExponent);
  const acrossValue=2*v-1;
  center.addScaledVector(side,halfWidth*acrossValue);
  center.z+=veinHeight*Math.sin(Math.PI*u)*(1-Math.abs(acrossValue));
  return center;
 },slices,across);
}

function seedPhase(seed){const x=Math.sin(seed*127.1+311.7)*43758.5453123;return(x-Math.floor(x))*Math.PI*2;}
export function fallingLeafStateAt({origin=[0,0,0],velocity=[0,0,0],gravity=9.81,time=0,driftAmplitude=[.2,0,.15],windFrequency=1.2,rotationSpeed=2,seed=1}={}){
 const p=vector(origin,"origin"),v=vector(velocity,"velocity"),drift=vector(driftAmplitude,"driftAmplitude");
 finite(gravity,"gravity");finite(time,"time");finite(windFrequency,"windFrequency");finite(rotationSpeed,"rotationSpeed");
 if(gravity<0||time<0||!Number.isInteger(seed))throw new RangeError("invalid falling leaf parameters");
 const ballistic=particlePositionAt({position:p,velocity:v,acceleration:[0,-gravity,0],time}),phase=seedPhase(seed)+windFrequency*time;
 const position=[ballistic[0]+drift[0]*Math.sin(phase),ballistic[1]+drift[1]*Math.sin(phase*.7),ballistic[2]+drift[2]*Math.cos(phase)];
 return {position,rotation:[rotationSpeed*time,Math.sin(phase)*.35,Math.cos(phase*.8)*.2]};
}

export function createGrassBladeGeometry({base=[0,0,0],height=1,width=.08,bend=.2,windAmplitude=.15,windFrequency=2,time=0,phase=0,segments=12,across=2}={}){
 const b=vector(base,"base");
 if(!(Number.isFinite(height)&&height>0&&Number.isFinite(width)&&width>0&&Number.isFinite(bend)&&Number.isFinite(windAmplitude)&&Number.isFinite(windFrequency)&&Number.isFinite(time)&&Number.isFinite(phase))||
   !Number.isInteger(segments)||segments<2||!Number.isInteger(across)||across<1)throw new RangeError("invalid grass blade parameters");
 return createParametricSurface((u,v)=>{
  const envelope=u*u,wind=windAmplitude*Math.sin(windFrequency*time+phase);
  const centerX=b[0]+bend*envelope+wind*envelope,centerY=b[1]+height*u,centerZ=b[2];
  const halfWidth=width*(1-u)*.5,side=2*v-1;
  return new THREE.Vector3(centerX,centerY,centerZ+side*halfWidth);
 },segments,across);
}

function deterministicNoise(seed,index,step,axis){
 const x=Math.sin(seed*17.17+index*73.31+step*19.19+axis*11.7)*43758.5453;
 return (x-Math.floor(x))*2-1;
}
function limitSpeed(v,maxSpeed){
 const speed=Math.hypot(...v);return speed>maxSpeed?v.map(x=>x*maxSpeed/speed):v;
}
export function stepInsectSwarm({agents,light,dt,stepIndex=0,seed=1,separationWeight=1,alignmentWeight=.3,cohesionWeight=.2,lightWeight=1,noiseAmplitude=.05,neighborRadius=2,maxSpeed=2}={}){
 if(!Array.isArray(agents)||!agents.length||!Number.isInteger(stepIndex)||!Number.isInteger(seed)||!(Number.isFinite(dt)&&dt>=0&&Number.isFinite(maxSpeed)&&maxSpeed>0))throw new RangeError("invalid insect swarm state");
 const lightPoint=vector(light,"light");
 return agents.map((agent,i)=>{
  const position=vector(agent.position,"agent position"),velocity=vector(agent.velocity,"agent velocity");
  const neighbors=agents.filter((_,j)=>j!==i).map(a=>({position:a.position,velocity:a.velocity}));
  const boids=computeBoidsAcceleration({position,velocity,neighbors,separationWeight,alignmentWeight,cohesionWeight,separationRadius:neighborRadius*.5,alignmentRadius:neighborRadius,cohesionRadius:neighborRadius});
  const toLight=lightPoint.map((v,k)=>v-position[k]),dist=Math.hypot(...toLight),attraction=dist>EPS?toLight.map(v=>v/dist*lightWeight):[0,0,0];
  const noise=position.map((_,axis)=>deterministicNoise(seed,i,stepIndex,axis)*noiseAmplitude);
  const acceleration=boids.acceleration.map((v,k)=>v+attraction[k]+noise[k]);
  const next=semiImplicitEulerStep({position,velocity,acceleration,dt});
  return {position:next.position,velocity:limitSpeed(next.velocity,maxSpeed)};
 });
}

export function stepBirdFlock({agents,leaderPosition,dt,stepIndex=0,leaderWeight=1,separationWeight=1,alignmentWeight=1,cohesionWeight=1,neighborRadius=5,maxSpeed=5}={}){
 if(!Array.isArray(agents)||!agents.length||!(Number.isFinite(dt)&&dt>=0&&Number.isFinite(leaderWeight)&&leaderWeight>=0&&Number.isFinite(maxSpeed)&&maxSpeed>0))throw new RangeError("invalid bird flock state");
 const leader=vector(leaderPosition,"leaderPosition");
 return agents.map((agent,i)=>{
  const position=vector(agent.position,"bird position"),velocity=vector(agent.velocity,"bird velocity");
  const neighbors=agents.filter((_,j)=>j!==i).map(a=>({position:a.position,velocity:a.velocity}));
  const boids=computeBoidsAcceleration({position,velocity,neighbors,separationWeight,alignmentWeight,cohesionWeight,separationRadius:neighborRadius*.4,alignmentRadius:neighborRadius,cohesionRadius:neighborRadius});
  const toward=leader.map((v,k)=>v-position[k]),dist=Math.hypot(...toward),follow=dist>EPS?toward.map(v=>v/dist*leaderWeight):[0,0,0];
  const acceleration=boids.acceleration.map((v,k)=>v+follow[k]);
  const next=semiImplicitEulerStep({position,velocity,acceleration,dt});
  return {position:next.position,velocity:limitSpeed(next.velocity,maxSpeed)};
 });
}
