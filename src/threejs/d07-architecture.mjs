import * as THREE from "three";
import { createParametricSurface } from "./d02-procedural-geometry.mjs";
import { solveXpbdDistanceConstraints } from "./d04-motion-simulation.mjs";

const EPS=1e-10;
function v3(a,name){if(!Array.isArray(a)||a.length!==3||!a.every(Number.isFinite))throw new RangeError(name+" must be a finite 3D vector");return a;}
function finite(x,n){if(!Number.isFinite(x))throw new RangeError(n+" must be finite");}
function mulberry32(seed){let a=seed>>>0;return()=>{a=(a+0x6D2B79F5)>>>0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296;};}

export function expandShapeGrammar(axiom,rules,iterations,{maxSymbols=100000}={}){
 if(!Array.isArray(axiom)||!axiom.length||!rules||typeof rules!=="object"||!Number.isInteger(iterations)||iterations<0||!Number.isInteger(maxSymbols)||maxSymbols<1)throw new RangeError("invalid shape grammar");
 let current=axiom.map(t=>({...t,params:{...(t.params||{})}}));
 for(let pass=0;pass<iterations;pass++){
  const next=[];
  for(const token of current){
   const production=rules[token.symbol];
   const result=typeof production==="function"?production(token):production;
   if(result===undefined){next.push(token);continue;}
   if(!Array.isArray(result))throw new TypeError("shape rule must return an array of tokens");
   if(next.length+result.length>maxSymbols)throw new RangeError("shape grammar exceeds maxSymbols");
   for(const child of result)next.push({...child,params:{...(child.params||{})}});
  }
  current=next;
 }
 return current;
}

export function assembleModularBuilding({modules,placements}={}){
 if(!modules||typeof modules!=="object"||!Array.isArray(placements))throw new TypeError("modules and placements required");
 const group=new THREE.Group(),byType=new Map();
 for(const p of placements){
  if(!modules[p.type]||!(modules[p.type].geometry instanceof THREE.BufferGeometry)||!modules[p.type].material)throw new RangeError("unknown or invalid module type: "+p.type);
  if(!byType.has(p.type))byType.set(p.type,[]);
  byType.get(p.type).push(p);
 }
 for(const [type,items] of byType){
  const module=modules[type],mesh=new THREE.InstancedMesh(module.geometry,module.material,items.length),dummy=new THREE.Object3D();
  items.forEach((item,i)=>{
   const position=item.position||[0,0,0],rotation=item.rotation||[0,0,0],scale=item.scale||[1,1,1];
   dummy.position.fromArray(v3(position,"module position"));v3(rotation,"module rotation");dummy.rotation.set(...rotation);dummy.scale.fromArray(v3(scale,"module scale"));dummy.updateMatrix();
   mesh.setMatrixAt(i,dummy.matrix);
  });
  mesh.instanceMatrix.needsUpdate=true;mesh.computeBoundingSphere();group.add(mesh);
 }
 return group;
}

export function createGableRoofGeometry({width=4,depth=4,baseY=0,pitch=.5,segments=1}={}){
 if(!(Number.isFinite(width)&&width>0&&Number.isFinite(depth)&&depth>0&&Number.isFinite(baseY)&&Number.isFinite(pitch)&&pitch>0)||!Number.isInteger(segments)||segments<1)throw new RangeError("invalid gable roof parameters");
 const positions=[],indices=[];
 const half=width/2,ridgeY=baseY+pitch*half;
 for(const side of [-1,1]){
  const start=positions.length/3;
  for(let j=0;j<=segments;j++){
   const z=-depth/2+depth*j/segments;
   if(side<0){positions.push(-half,baseY,z,0,ridgeY,z);}
   else{positions.push(0,ridgeY,z,half,baseY,z);}
  }
  for(let j=0;j<segments;j++){
   const a=start+j*2,b=a+2;
   indices.push(a,b,a+1,b,b+1,a+1);
  }
 }
 const g=new THREE.BufferGeometry();g.setAttribute("position",new THREE.Float32BufferAttribute(positions,3));g.setIndex(indices);g.computeVertexNormals();g.computeBoundingBox();g.computeBoundingSphere();return g;
}

export function createCurvedRoofGeometry({width=4,depth=4,baseY=0,curvature=.1,profile=null,slices=32,stacks=8}={}){
 if(!(Number.isFinite(width)&&width>0&&Number.isFinite(depth)&&depth>0&&Number.isFinite(baseY)&&Number.isFinite(curvature))||!Number.isInteger(slices)||slices<2||!Number.isInteger(stacks)||stacks<1||profile!==null&&typeof profile!=="function")throw new RangeError("invalid curved roof parameters");
 return createParametricSurface((u,v)=>{
  const x=(u-.5)*width,z=(v-.5)*depth,y=baseY+(profile?profile(x):curvature*x*x);
  if(!Number.isFinite(y))throw new RangeError("roof profile must be finite");
  return new THREE.Vector3(x,y,z);
 },slices,stacks);
}

export function createArchGeometry({center=[0,0],radius=1,thickness=.2,depth=.4,startAngle=0,endAngle=Math.PI,segments=32,bevel=.02}={}){
 if(!Array.isArray(center)||center.length!==2||!center.every(Number.isFinite)||!(Number.isFinite(radius)&&radius>0&&Number.isFinite(thickness)&&thickness>0&&Number.isFinite(depth)&&depth>0)||!(endAngle>startAngle)||!Number.isInteger(segments)||segments<3||!Number.isFinite(bevel)||bevel<0)throw new RangeError("invalid arch parameters");
 const shape=new THREE.Shape(),outer=radius+thickness/2,inner=Math.max(EPS,radius-thickness/2);
 shape.moveTo(center[0]+outer*Math.cos(startAngle),center[1]+outer*Math.sin(startAngle));
 for(let i=1;i<=segments;i++){const a=startAngle+(endAngle-startAngle)*i/segments;shape.lineTo(center[0]+outer*Math.cos(a),center[1]+outer*Math.sin(a));}
 for(let i=segments;i>=0;i--){const a=startAngle+(endAngle-startAngle)*i/segments;shape.lineTo(center[0]+inner*Math.cos(a),center[1]+inner*Math.sin(a));}
 shape.closePath();
 const geometry=new THREE.ExtrudeGeometry(shape,{depth,bevelEnabled:bevel>0,bevelSegments:2,steps:1,bevelSize:bevel,bevelThickness:bevel});
 geometry.computeBoundingBox();geometry.computeBoundingSphere();return geometry;
}

export function createFlutedColumnGeometry({radius=.5,height=4,flutes=12,amplitude=.025,segments=64,heightSegments=8}={}){
 if(!(Number.isFinite(radius)&&radius>0&&Number.isFinite(height)&&height>0&&Number.isInteger(flutes)&&flutes>=1&&Number.isFinite(amplitude)&&amplitude>=0&&amplitude<radius)||!Number.isInteger(segments)||segments<3||!Number.isInteger(heightSegments)||heightSegments<1)throw new RangeError("invalid fluted column parameters");
 return createParametricSurface((u,v)=>{
  const theta=u*Math.PI*2,r=radius+amplitude*Math.cos(flutes*theta);
  return new THREE.Vector3(r*Math.cos(theta),v*height,r*Math.sin(theta));
 },segments,heightSegments);
}

export function createParametricStaircase({steps=8,rise=.18,run=.28,width=1.5,origin=[0,0,0],material=new THREE.MeshStandardMaterial({color:0x888888})}={}){
 if(!Number.isInteger(steps)||steps<1||![rise,run,width].every(Number.isFinite)||rise<=0||run<=0||width<=0)throw new RangeError("invalid staircase parameters");
 const o=v3(origin,"origin"),geometry=new THREE.BoxGeometry(width,rise,run),mesh=new THREE.InstancedMesh(geometry,material,steps),dummy=new THREE.Object3D();
 for(let i=0;i<steps;i++){
  dummy.position.set(o[0],o[1]+(i+.5)*rise,o[2]+(i+.5)*run);dummy.updateMatrix();mesh.setMatrixAt(i,dummy.matrix);
 }
 mesh.instanceMatrix.needsUpdate=true;mesh.computeBoundingSphere();return mesh;
}

export function createBridgeAlongCurve(points,{width=2,deckThickness=.15,railingHeight=1,segments=32,material=new THREE.MeshStandardMaterial({color:0x777777})}={}){
 if(!Array.isArray(points)||points.length<2||!(Number.isFinite(width)&&width>0&&Number.isFinite(deckThickness)&&deckThickness>0&&Number.isFinite(railingHeight)&&railingHeight>0)||!Number.isInteger(segments)||segments<2)throw new RangeError("invalid bridge parameters");
 const curve=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...v3(p,"bridge point"))));
 const deck=createParametricSurface((u,v)=>{
  const center=curve.getPoint(u),tangent=curve.getTangent(u).normalize(),side=tangent.clone().cross(new THREE.Vector3(0,1,0));
  if(side.lengthSq()<EPS)side.set(1,0,0);side.normalize();
  return center.addScaledVector(side,(v-.5)*width).add(new THREE.Vector3(0,-deckThickness/2,0));
 },segments,2);
 const group=new THREE.Group();group.add(new THREE.Mesh(deck,material));
 for(const sign of [-1,1]){
  const pts=[];for(let i=0;i<=segments;i++){
   const u=i/segments,c=curve.getPoint(u),t=curve.getTangent(u).normalize(),side=t.clone().cross(new THREE.Vector3(0,1,0));
   if(side.lengthSq()<EPS)side.set(1,0,0);side.normalize();
   pts.push(c.addScaledVector(side,sign*width/2).add(new THREE.Vector3(0,railingHeight,0)));
  }
  const railGeometry=new THREE.BufferGeometry().setFromPoints(pts);group.add(new THREE.Line(railGeometry,new THREE.LineBasicMaterial({color:0x555555})));
 }
 group.userData.deckThickness=deckThickness;return group;
}

export function createMasonryWall({width=6,height=3,depth=.3,columns=6,rows=4,stoneWidthJitter=.12,stoneHeightJitter=.08,bevel=.04,seed=1,material=new THREE.MeshStandardMaterial({color:0x999999})}={}){
 if(!(Number.isFinite(width)&&width>0&&Number.isFinite(height)&&height>0&&Number.isFinite(depth)&&depth>0)||!Number.isInteger(columns)||columns<1||!Number.isInteger(rows)||rows<1||
   !Number.isFinite(stoneWidthJitter)||stoneWidthJitter<0||stoneWidthJitter>=1||!Number.isFinite(stoneHeightJitter)||stoneHeightJitter<0||stoneHeightJitter>=1||!Number.isFinite(bevel)||bevel<0||!Number.isInteger(seed))throw new RangeError("invalid masonry parameters");
 const rand=mulberry32(seed),group=new THREE.Group(),blocks=[];
 for(let row=0;row<rows;row++){
  const nominalH=height/rows,h=nominalH*(1+(rand()*2-1)*stoneHeightJitter);
  const offset=row%2?width/columns/2:0;
  for(let col=0;col<columns;col++){
   const nominalW=width/columns,w=nominalW*(1+(rand()*2-1)*stoneWidthJitter);
   const x=-width/2+col*nominalW+offset+(rand()-.5)*nominalW*.08,y=-height/2+row*nominalH+(rand()-.5)*nominalH*.06;
   const shape=new THREE.Shape();shape.moveTo(-w/2,-h/2);shape.lineTo(w/2,-h/2);shape.lineTo(w/2,h/2);shape.lineTo(-w/2,h/2);shape.closePath();
   const geometry=new THREE.ExtrudeGeometry(shape,{depth,bevelEnabled:bevel>0,bevelSegments:1,steps:1,bevelSize:bevel,bevelThickness:bevel});
   const mesh=new THREE.Mesh(geometry,material);mesh.position.set(x+w/2,y+h/2,0);group.add(mesh);
   blocks.push({x,y,width:w,height:h,depth});
  }
 }
 group.userData.blocks=blocks;return group;
}

export function createProceduralFacade({width=8,height=10,bays=4,floors=5,wallDepth=.25,windowRatio=.55,doorWidth=1.2,doorHeight=2.4,material=new THREE.MeshStandardMaterial({color:0xc8bba6}),glassMaterial=new THREE.MeshStandardMaterial({color:0x446677,metalness:.1,roughness:.25})}={}){
 if(!(Number.isFinite(width)&&width>0&&Number.isFinite(height)&&height>0)||!Number.isInteger(bays)||bays<1||!Number.isInteger(floors)||floors<1||
   !(Number.isFinite(wallDepth)&&wallDepth>0&&Number.isFinite(windowRatio)&&windowRatio>0&&windowRatio<1&&Number.isFinite(doorWidth)&&doorWidth>0&&Number.isFinite(doorHeight)&&doorHeight>0))throw new RangeError("invalid facade parameters");
 const shape=new THREE.Shape();shape.moveTo(-width/2,0);shape.lineTo(width/2,0);shape.lineTo(width/2,height);shape.lineTo(-width/2,height);shape.closePath();
 const holes=[],openings=[],bayW=width/bays,floorH=height/floors;
 for(let floor=0;floor<floors;floor++)for(let bay=0;bay<bays;bay++){
  const cx=-width/2+(bay+.5)*bayW,cy=(floor+.5)*floorH;
  if(floor===0&&bay===Math.floor(bays/2)){
   const w=Math.min(doorWidth,bayW*.8),h=Math.min(doorHeight,floorH*.9);
   const doorBottom=Math.min(.02,h*.05);const path=new THREE.Path();path.moveTo(cx-w/2,doorBottom);path.lineTo(cx-w/2,h);path.lineTo(cx+w/2,h);path.lineTo(cx+w/2,doorBottom);path.closePath();holes.push(path);
   openings.push({type:"door",x:cx,y:h/2,width:w,height:h});
  }else{
   const w=bayW*windowRatio,h=floorH*windowRatio;
   const path=new THREE.Path();path.moveTo(cx-w/2,cy-h/2);path.lineTo(cx-w/2,cy+h/2);path.lineTo(cx+w/2,cy+h/2);path.lineTo(cx+w/2,cy-h/2);path.closePath();holes.push(path);
   openings.push({type:"window",x:cx,y:cy,width:w,height:h});
  }
 }
 shape.holes=holes;
 const geometry=new THREE.ExtrudeGeometry(shape,{depth:wallDepth,bevelEnabled:false,steps:1}),group=new THREE.Group();
 group.add(new THREE.Mesh(geometry,material));
 for(const opening of openings)if(opening.type==="window"){
  const pane=new THREE.Mesh(new THREE.BoxGeometry(opening.width,opening.height,.03),glassMaterial);
  pane.position.set(opening.x,opening.y,wallDepth/2+.02);group.add(pane);
 }
 group.userData.openings=openings;return group;
}

export function createFlagState({widthSegments=12,heightSegments=8,spacing=.2,origin=[0,0,0],compliance=1e-6}={}){
 if(!Number.isInteger(widthSegments)||widthSegments<1||!Number.isInteger(heightSegments)||heightSegments<1||!(Number.isFinite(spacing)&&spacing>0&&Number.isFinite(compliance)&&compliance>=0))throw new RangeError("invalid flag grid");
 const o=v3(origin,"origin"),positions=[],inverseMasses=[],anchors=[],constraints=[],index=(x,y)=>y*(widthSegments+1)+x;
 for(let y=0;y<=heightSegments;y++)for(let x=0;x<=widthSegments;x++){
  const p=[o[0]+x*spacing,o[1]-y*spacing,o[2]];positions.push(p);const fixed=y===0;inverseMasses.push(fixed?0:1);anchors.push(fixed?p.slice():null);
 }
 const add=(a,b,restLength,kind)=>constraints.push({a,b,restLength,compliance,kind});
 for(let y=0;y<=heightSegments;y++)for(let x=0;x<=widthSegments;x++){
  const i=index(x,y);
  if(x<widthSegments)add(i,index(x+1,y),spacing,"structural");
  if(y<heightSegments)add(i,index(x,y+1),spacing,"structural");
  if(x<widthSegments&&y<heightSegments){add(i,index(x+1,y+1),Math.SQRT2*spacing,"shear");add(index(x+1,y),index(x,y+1),Math.SQRT2*spacing,"shear");}
  if(x+2<=widthSegments)add(i,index(x+2,y),2*spacing,"bend");
  if(y+2<=heightSegments)add(i,index(x,y+2),2*spacing,"bend");
 }
 return {widthSegments,heightSegments,spacing,positions,previousPositions:positions.map(p=>p.slice()),inverseMasses,anchors,constraints};
}

export function stepFlag(state,{dt,gravity=[0,-9.81,0],wind=[0,0,0],damping=.02,iterations=6}={}){
 if(!state||!Array.isArray(state.positions)||!(Number.isFinite(dt)&&dt>0)||!Number.isFinite(damping)||damping<0||damping>1||!Number.isInteger(iterations)||iterations<1)throw new RangeError("invalid flag simulation step");
 const g=v3(gravity,"gravity"),w=v3(wind,"wind");
 const predicted=state.positions.map((p,i)=>{
  if(state.inverseMasses[i]===0)return state.anchors[i].slice();
  const prev=state.previousPositions[i],acc=g.map((a,k)=>a+w[k]);
  return p.map((value,k)=>value+(value-prev[k])*(1-damping)+acc[k]*dt*dt);
 });
 const solved=solveXpbdDistanceConstraints({positions:predicted,inverseMasses:state.inverseMasses,constraints:state.constraints,dt,iterations});
 const positions=solved.positions.map((p,i)=>state.inverseMasses[i]===0?state.anchors[i].slice():p);
 return {...state,previousPositions:state.positions.map(p=>p.slice()),positions};
}

export function createFlagGeometry(state){
 if(!state||!Array.isArray(state.positions))throw new TypeError("flag state required");
 const {widthSegments:wx,heightSegments:hy}=state,positions=state.positions.flat(),uvs=[],indices=[];
 for(let y=0;y<=hy;y++)for(let x=0;x<=wx;x++)uvs.push(x/wx,y/hy);
 const row=wx+1;
 for(let y=0;y<hy;y++)for(let x=0;x<wx;x++){const a=y*row+x,b=a+row;indices.push(a,b,a+1,b,b+1,a+1);}
 const g=new THREE.BufferGeometry();g.setAttribute("position",new THREE.Float32BufferAttribute(positions,3));g.setAttribute("uv",new THREE.Float32BufferAttribute(uvs,2));g.setIndex(indices);g.computeVertexNormals();return g;
}

export function createPendulumLantern({pivot=[0,0,0],length=1,gravity=9.81,amplitude=.2,phase=0,time=0}={}){
 const p=v3(pivot,"pivot");
 if(!(Number.isFinite(length)&&length>0&&Number.isFinite(gravity)&&gravity>=0&&Number.isFinite(amplitude)&&Math.abs(amplitude)<=.5&&Number.isFinite(phase)&&Number.isFinite(time)&&time>=0))throw new RangeError("invalid pendulum lantern");
 const omega=Math.sqrt(gravity/length),theta=amplitude*Math.cos(omega*time+phase);
 return {theta,position:[p[0]+length*Math.sin(theta),p[1]-length*Math.cos(theta),p[2]],angularVelocity:-amplitude*omega*Math.sin(omega*time+phase)};
}
