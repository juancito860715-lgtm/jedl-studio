import * as THREE from "three";

const EPS=1e-10;
function finite(v,name){if(!Number.isFinite(v))throw new RangeError(name+" must be finite");}
function hash2(ix,iz,seed){
 let h=Math.imul(ix|0,0x1f123bb5)^Math.imul(iz|0,0x5f356495)^Math.imul(seed|0,0x6c8e9cf5);
 h=Math.imul(h^(h>>>15),0x2c1b3c6d);h=Math.imul(h^(h>>>12),0x297a2d39);h^=h>>>15;
 return (h>>>0)/4294967295*2-1;
}
const smooth=t=>t*t*(3-2*t),lerp=(a,b,t)=>a+(b-a)*t;
export function valueNoise2D(x,z,seed=1){
 finite(x,"x");finite(z,"z");if(!Number.isInteger(seed))throw new RangeError("seed must be integer");
 const ix=Math.floor(x),iz=Math.floor(z),u=smooth(x-ix),v=smooth(z-iz);
 const a=lerp(hash2(ix,iz,seed),hash2(ix+1,iz,seed),u);
 const b=lerp(hash2(ix,iz+1,seed),hash2(ix+1,iz+1,seed),u);
 return lerp(a,b,v);
}

export function createHeightfieldGeometry({width=10,depth=10,segmentsX=64,segmentsZ=64,heightFn=()=>0,origin=[0,0]}={}){
 if(!(Number.isFinite(width)&&width>0&&Number.isFinite(depth)&&depth>0)||
   !Number.isInteger(segmentsX)||segmentsX<1||!Number.isInteger(segmentsZ)||segmentsZ<1||typeof heightFn!=="function"||
   !Array.isArray(origin)||origin.length!==2||!origin.every(Number.isFinite))throw new RangeError("invalid heightfield parameters");
 const positions=[],uvs=[],indices=[];
 for(let z=0;z<=segmentsZ;z++)for(let x=0;x<=segmentsX;x++){
  const u=x/segmentsX,v=z/segmentsZ,px=origin[0]+(u-.5)*width,pz=origin[1]+(v-.5)*depth,py=heightFn(px,pz);
  if(!Number.isFinite(py))throw new RangeError("height function returned non-finite value");
  positions.push(px,py,pz);uvs.push(u,v);
 }
 const row=segmentsX+1;
 for(let z=0;z<segmentsZ;z++)for(let x=0;x<segmentsX;x++){
  const a=z*row+x,b=a+row;indices.push(a,b,a+1,b,b+1,a+1);
 }
 const g=new THREE.BufferGeometry();
 g.setAttribute("position",new THREE.Float32BufferAttribute(positions,3));
 g.setAttribute("uv",new THREE.Float32BufferAttribute(uvs,2));
 g.setIndex(indices);g.computeVertexNormals();g.computeBoundingBox();g.computeBoundingSphere();
 return g;
}

export function ridgedMultifractal2D(x,z,{seed=1,frequency=1,lacunarity=2,persistence=.5,octaves=6,amplitude=1,baseHeight=0}={}){
 for(const [v,n] of [[x,"x"],[z,"z"],[frequency,"frequency"],[lacunarity,"lacunarity"],[persistence,"persistence"],[amplitude,"amplitude"],[baseHeight,"baseHeight"]])finite(v,n);
 if(!Number.isInteger(seed)||!Number.isInteger(octaves)||octaves<1||frequency<=0||lacunarity<=1||persistence<0||persistence>1||amplitude<0)throw new RangeError("invalid ridged multifractal parameters");
 let sum=0,f=frequency,a=1;
 for(let i=0;i<octaves;i++){const n=valueNoise2D(x*f,z*f,seed+i*1013),ridge=1-Math.abs(n);sum+=a*ridge*ridge;f*=lacunarity;a*=persistence;}
 return baseHeight+amplitude*sum;
}

export function domainWarp2D(x,z,{seed=1,warpAmplitude=1,frequency=1,baseFunction=valueNoise2D}={}){
 finite(x,"x");finite(z,"z");finite(warpAmplitude,"warpAmplitude");finite(frequency,"frequency");
 if(!Number.isInteger(seed)||warpAmplitude<0||frequency<=0||typeof baseFunction!=="function")throw new RangeError("invalid domain warp parameters");
 const qx=valueNoise2D(x*frequency+17.1,z*frequency-9.2,seed),qz=valueNoise2D(x*frequency-31.7,z*frequency+5.3,seed+1);
 const wx=x+warpAmplitude*qx,wz=z+warpAmplitude*qz;
 return {x:wx,z:wz,value:baseFunction(wx,wz,seed+2)};
}

export function cascadeTerrainDetail(x,z,{seed=1,octaves=5,frequency=1,lacunarity=2,persistence=.5,amplitude=1,baseHeight=0,baseFunction=null}={}){
 finite(x,"x");finite(z,"z");
 if(!Number.isInteger(seed)||!Number.isInteger(octaves)||octaves<1||!(frequency>0&&lacunarity>1&&persistence>=0&&persistence<=1&&amplitude>=0))throw new RangeError("invalid detail cascade");
 let sum=0,f=frequency,a=1;
 for(let i=0;i<octaves;i++){sum+=a*(baseFunction?baseFunction(x*f,z*f,seed+i):valueNoise2D(x*f,z*f,seed+i));f*=lacunarity;a*=persistence;}
 return baseHeight+amplitude*sum;
}

function gridArray(value,n,name){
 if(!ArrayBuffer.isView(value)&&!Array.isArray(value))throw new TypeError(name+" must be an array or typed array");
 if(value.length!==n||Array.from(value).some(v=>!Number.isFinite(v)))throw new RangeError(name+" length/values invalid");
 return Float64Array.from(value);
}
export function hydraulicErosionStep({heightMap,waterMap,sedimentMap,width,height,dt,cellSize=1,rainRate=0,flowRate=1,capacityCoefficient=1,erosionRate=.1,depositionRate=.1,evaporationRate=0,minHeight=-1e6}={}){
 const n=width*height;
 if(!Number.isInteger(width)||width<2||!Number.isInteger(height)||height<2||!(Number.isFinite(dt)&&dt>0&&Number.isFinite(cellSize)&&cellSize>0)||
   ![rainRate,flowRate,capacityCoefficient,erosionRate,depositionRate,evaporationRate,minHeight].every(Number.isFinite)||
   [rainRate,flowRate,capacityCoefficient,erosionRate,depositionRate,evaporationRate].some(v=>v<0)||evaporationRate*dt>1)throw new RangeError("invalid hydraulic erosion parameters");
 const h=gridArray(heightMap,n,"heightMap"),w=gridArray(waterMap,n,"waterMap"),s=gridArray(sedimentMap,n,"sedimentMap");
 if(Array.from(w).some(v=>v<0)||Array.from(s).some(v=>v<0))throw new RangeError("water and sediment values must be nonnegative");
 const waterDelta=new Float64Array(n),sedimentDelta=new Float64Array(n),outflow=new Float64Array(n),maxSlope=new Float64Array(n);
 for(let z=0;z<height;z++)for(let x=0;x<width;x++){
  const i=z*width+x;w[i]+=rainRate*dt;
  const surface=h[i]+w[i],neighbors=[];
  if(x>0)neighbors.push(i-1);if(x<width-1)neighbors.push(i+1);if(z>0)neighbors.push(i-width);if(z<height-1)neighbors.push(i+width);
  const drops=neighbors.map(j=>Math.max(0,surface-(h[j]+w[j]))),sum=drops.reduce((a,b)=>a+b,0);
  if(sum<=EPS||w[i]<=EPS)continue;
  const total=Math.min(w[i],flowRate*dt*sum/cellSize),factor=total/sum;
  neighbors.forEach((j,k)=>{
   const flux=drops[k]*factor;if(flux<=0)return;
   waterDelta[i]-=flux;waterDelta[j]+=flux;
   const sedimentFlux=s[i]*Math.min(1,flux/Math.max(w[i],EPS));
   sedimentDelta[i]-=sedimentFlux;sedimentDelta[j]+=sedimentFlux;
   outflow[i]+=flux;maxSlope[i]=Math.max(maxSlope[i],drops[k]/cellSize);
  });
 }
 const nextH=h.slice(),nextW=new Float64Array(n),nextS=new Float64Array(n);
 for(let i=0;i<n;i++){
  nextW[i]=Math.max(0,(w[i]+waterDelta[i])*(1-evaporationRate*dt));
  nextS[i]=Math.max(0,s[i]+sedimentDelta[i]);
  const capacity=capacityCoefficient*outflow[i]*maxSlope[i];
  if(nextS[i]<capacity){
   const erode=Math.min(erosionRate*dt,capacity-nextS[i],Math.max(0,nextH[i]-minHeight));
   nextH[i]-=erode;nextS[i]+=erode;
  }else{
   const deposit=Math.min(depositionRate*dt,nextS[i]-capacity);
   nextH[i]+=deposit;nextS[i]-=deposit;
  }
 }
 return {heightMap:nextH,waterMap:nextW,sedimentMap:nextS};
}

export function thermalErosionStep({heightMap,width,height,cellSize=1,talusAngle=Math.PI/4,transferFraction=.2,iterations=1}={}){
 const n=width*height;
 if(!Number.isInteger(width)||width<2||!Number.isInteger(height)||height<2||!(Number.isFinite(cellSize)&&cellSize>0&&Number.isFinite(talusAngle)&&talusAngle>=0&&talusAngle<Math.PI/2&&Number.isFinite(transferFraction)&&transferFraction>0&&transferFraction<=.25)||!Number.isInteger(iterations)||iterations<1)throw new RangeError("invalid thermal erosion parameters");
 let h=gridArray(heightMap,n,"heightMap");const threshold=cellSize*Math.tan(talusAngle);
 for(let pass=0;pass<iterations;pass++){
  const delta=new Float64Array(n);
  const transfer=(i,j)=>{
   const diff=h[i]-h[j],excess=Math.abs(diff)-threshold;
   if(excess<=0)return;
   const amount=.5*excess*transferFraction,high=diff>0?i:j,low=diff>0?j:i;
   delta[high]-=amount;delta[low]+=amount;
  };
  for(let z=0;z<height;z++)for(let x=0;x<width;x++){
   const i=z*width+x;if(x+1<width)transfer(i,i+1);if(z+1<height)transfer(i,i+width);
  }
  h=h.map((v,i)=>v+delta[i]);
 }
 return h;
}

export function classifyBiome({altitude,slope,moisture,exposure,seed=1}={}){
 for(const [v,n] of [[altitude,"altitude"],[slope,"slope"],[moisture,"moisture"],[exposure,"exposure"]])finite(v,n);
 if(!Number.isInteger(seed)||slope<0||moisture<0||moisture>1||exposure<0||exposure>1)throw new RangeError("invalid biome inputs");
 const z=[Math.max(0,Math.min(1,altitude)),Math.max(0,Math.min(1,slope)),moisture,exposure];
 const scores={
  alpine:.9*z[0]-.1*z[1]-.25*z[2]+.3*z[3],
  forest:.15*z[0]-.45*z[1]+.85*z[2]-.15*z[3],
  grassland:.1*z[0]-.65*z[1]+.25*z[2]+.1*z[3],
  desert:-.1*z[0]+.25*z[1]-.95*z[2]+.85*z[3],
  wetland:-.3*z[0]-.8*z[1]+1.05*z[2]-.15*z[3]
 };
 const biome=Object.keys(scores).sort((a,b)=>scores[b]-scores[a])[0];
 const variant=(Math.imul(seed>>>0,0x9e3779b1)>>>0)%4;
 return {biome,variant,scores};
}

function norm(v){return Math.hypot(...v);}
function normalize(v,name){const l=norm(v);if(!(l>EPS))throw new RangeError(name+" must be nonzero");return v.map(x=>x/l);}
function dot(a,b){return a.reduce((s,v,i)=>s+v*b[i],0);}
function gaussian(x,sigma){return Math.exp(-.5*(x/sigma)**2)/(Math.sqrt(2*Math.PI)*sigma);}
function fresnelSchlick(cosine,ior){const f0=((ior-1)/(ior+1))**2;return f0+(1-f0)*Math.pow(1-Math.max(0,Math.min(1,cosine)),5);}
export function evaluateHairMicrofacetApproximation({wi,wo,tangent=[0,1,0],albedo=[.25,.12,.06],radius=.04,ior=1.55,absorption=1,roughness=.25,azimuthalRoughness=.35,cuticleTilt=.05}={}){
 const I=normalize(Array.from(wi),"wi"),O=normalize(Array.from(wo),"wo"),T=normalize(Array.from(tangent),"tangent");
 if(!Array.isArray(albedo)||albedo.length!==3||!albedo.every(Number.isFinite)||![radius,ior,absorption,roughness,azimuthalRoughness,cuticleTilt].every(Number.isFinite)||!(radius>0&&ior>1&&absorption>=0&&roughness>0&&azimuthalRoughness>0))throw new RangeError("invalid hair scattering parameters");
 const sinI=Math.max(-1,Math.min(1,dot(I,T))),sinO=Math.max(-1,Math.min(1,dot(O,T)));
 const thetaI=Math.asin(sinI),thetaO=Math.asin(sinO);
 const perpI=I.map((v,i)=>v-sinI*T[i]),perpO=O.map((v,i)=>v-sinO*T[i]);
 const li=norm(perpI),lo=norm(perpO);
 const cosPhi=Math.max(-1,Math.min(1,dot(perpI,perpO)/Math.max(li*lo,EPS))),phi=Math.acos(cosPhi);
 const cosI=Math.sqrt(Math.max(EPS,1-sinI*sinI)),cosO=Math.sqrt(Math.max(EPS,1-sinO*sinO));
 const cosT=Math.sqrt(Math.max(EPS,1-(sinI/ior)**2)),pathLength=2*radius/cosT,attenuation=Math.exp(-absorption*pathLength);
 const h=normalize(I.map((v,i)=>v+O[i]),"half vector"),F=fresnelSchlick(Math.abs(dot(I,h)),ior);
 const longitudinal=gaussian(thetaI+thetaO-2*cuticleTilt,roughness);
 const azR=gaussian(phi,azimuthalRoughness),azTT=gaussian(Math.PI-phi,azimuthalRoughness);
 const G=Math.min(1,2*cosI*cosO/Math.max(cosI+cosO,EPS));
 const R=F*longitudinal*azR*G/Math.max(4*cosI*cosO,EPS);
 const TT=(1-F)*(1-F)*attenuation*longitudinal*azTT;
 const TRT=F*(1-F)*(1-F)*attenuation*attenuation*longitudinal*azR;
 const lobes={R:albedo.map(c=>c*R),TT:albedo.map(c=>c*TT),TRT:albedo.map(c=>c*TRT)};
 return {...lobes,total:albedo.map((c,i)=>c*(R+TT+TRT)),pathLength,attenuation,approximation:true};
}
