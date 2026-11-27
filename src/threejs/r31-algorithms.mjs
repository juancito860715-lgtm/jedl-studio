// R31 production-oriented CPU algorithms. Deterministic and renderer-agnostic.
// The impasto path follows the published pipeline (coarse-to-fine layers,
// incremental Voronoi-like sampling, tangent-field streamlines, brush height).
// The erosion field uses a finite spectral approximation of a complex Gaussian
// field; it is an explicit, reproducible CPU model, not a bitwise reproduction
// of the authors' GPU sparse-convolution implementation.
const TAU = Math.PI * 2;
const finite = (values, label) => {
  if (!values.every(Number.isFinite)) throw new RangeError(label + " must be finite");
};
const hypot2 = (a,b) => Math.hypot(a[0]-b[0],a[1]-b[1]);
function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function radicalInverse(index, base) {
  let n=index, inv=1/base, value=0;
  while(n>0){value+=(n%base)*inv;n=Math.floor(n/base);inv/=base;}
  return value;
}
function sampleIncrementalVoronoi(count, bounds, minDistance, seed=1) {
  if(!Number.isInteger(count)||count<0||!(minDistance>=0)||bounds.length!==4) throw new RangeError("invalid sampling parameters");
  const [xmin,ymin,xmax,ymax]=bounds;finite(bounds,"bounds");
  if(!(xmax>xmin&&ymax>ymin))throw new RangeError("bounds must have positive area");
  const rand=mulberry32(seed),points=[];
  // Low-discrepancy sequence with seeded Cranley-Patterson rotation. Rejecting
  // points closer than minDistance yields an incremental Poisson/Voronoi-like
  // distribution while preserving deterministic order.
  const ox=rand(),oy=rand(),limit=Math.max(count*100,1000);
  for(let i=1;i<=limit&&points.length<count;i++){
    const x=xmin+(((radicalInverse(i,2)+ox)%1)*(xmax-xmin));
    const y=ymin+(((radicalInverse(i,3)+oy)%1)*(ymax-ymin));
    if(points.every(p=>hypot2(p,[x,y])>=minDistance))points.push([x,y]);
  }
  return points;
}
export function generateLayeredImpasto({bounds=[-1,-1,1,1],layers=[{scale:.18,count:36},{scale:.08,count:90},{scale:.035,count:180}],seed=19,tangentField=([x,y])=>[-y,x],steps=8,stepLength=.025,brushHeight=(u,v)=>Math.max(0,1-u*u)*Math.max(0,1-v*v)}={}) {
  if(!Array.isArray(layers)||steps<1||!(stepLength>0))throw new RangeError("invalid impasto configuration");
  const output=[];
  layers.forEach((layer,layerIndex)=>{
    if(!(layer.scale>0)||!Number.isInteger(layer.count)||layer.count<0)throw new RangeError("invalid impasto layer");
    const centers=sampleIncrementalVoronoi(layer.count,bounds,layer.scale*.55,seed+layerIndex*7919);
    for(let index=0;index<centers.length;index++){
      const center=centers[index],line=[center.slice()];let p=center.slice();
      for(let s=0;s<steps;s++){
        const v=tangentField(p.slice());if(!Array.isArray(v)||v.length!==2)throw new RangeError("tangentField must return a 2-vector");
        finite(v,"tangent field");const n=Math.hypot(...v);if(n<1e-12)break;
        const q=[p[0]+v[0]/n*stepLength,p[1]+v[1]/n*stepLength];
        if(q[0]<bounds[0]||q[0]>bounds[2]||q[1]<bounds[1]||q[1]>bounds[3])break;
        line.push(q);p=q;
      }
      output.push({layer:layerIndex,scale:layer.scale,center:center.slice(),line,brushHeight});
    }
  });
  return output;
}
export function evaluateBrushHeight(stroke, uv) {
  if(!stroke||typeof stroke.brushHeight!=="function"||uv.length!==2)throw new RangeError("invalid brush sample");
  const [u,v]=uv;finite([u,v],"brush UV");
  if(Math.abs(u)>1||Math.abs(v)>1)return 0;
  const h=stroke.brushHeight(u,v);if(!Number.isFinite(h))throw new RangeError("brush height must be finite");
  return h;
}
function gaussianPair(rand) {
  const u1=Math.max(rand(),Number.MIN_VALUE),u2=rand(),r=Math.sqrt(-2*Math.log(u1)),a=TAU*u2;
  return [r*Math.cos(a),r*Math.sin(a)];
}
export function createPhasorSpectrum({seed=7,components=48,frequency=5,orientation=0,bandwidth=.12,radial=0.025}={}) {
  if(!Number.isInteger(components)||components<1||!(frequency>0)||!(bandwidth>=0)||!(radial>=0))throw new RangeError("invalid Phasor spectrum");
  finite([frequency,orientation,bandwidth,radial],"spectrum parameters");
  const rand=mulberry32(seed),waves=[];
  for(let i=0;i<components;i++){
    const [g0,g1]=gaussianPair(rand),angle=orientation+(rand()-.5)*bandwidth;
    const f=frequency*Math.exp(g0*.12);
    waves.push({kx:Math.cos(angle)*f,ky:Math.sin(angle)*f,re:g0/Math.sqrt(components),im:g1/Math.sqrt(components)});
  }
  return {waves,radial,seed,frequency,orientation};
}
export function evaluatePhasorPhase(spectrum, point) {
  if(!spectrum||point.length!==2)throw new RangeError("spectrum and 2D point required");
  finite(point,"phasor point");let re=0,im=0;
  for(const w of spectrum.waves){const a=TAU*(w.kx*point[0]+w.ky*point[1]);re+=w.re*Math.cos(a)-w.im*Math.sin(a);im+=w.re*Math.sin(a)+w.im*Math.cos(a);}
  // The radial regularizer prevents a zero complex field from making phase
  // undefined. Its direction is fixed, so the field remains deterministic.
  re+=spectrum.radial;
  return Math.atan2(im,re);
}
export function evaluateErosionProfile(phase,{depth=.12,rounding=.08,amplitude=1}={}) {
  finite([phase,depth,rounding,amplitude],"erosion profile");
  if(depth<0||rounding<0||amplitude<0)throw new RangeError("profile controls must be nonnegative");
  const cycle=((phase/TAU)%1+1)%1;
  const ridge=1-Math.abs(2*cycle-1);
  const softened=ridge*ridge*(3-2*ridge);
  return -amplitude*depth*(rounding===0?ridge:softened);
}
export function phasorErosionHeight({base,point,spectrum,depth=.12,rounding=.08,amplitude=1,attenuation=1}) {
  finite([base,depth,rounding,amplitude,attenuation],"erosion inputs");
  if(depth<0||amplitude<0||attenuation<0)throw new RangeError("erosion controls must be nonnegative");
  return base+attenuation*evaluateErosionProfile(evaluatePhasorPhase(spectrum,point),{depth,rounding,amplitude});
}
export function rk4Trajectory(field, initial, start, end, steps) {
  if(!Number.isInteger(steps)||steps<1||!Number.isFinite(start)||!Number.isFinite(end)||!initial.length)throw new RangeError("invalid RK4 trajectory");
  finite(initial,"initial state");
  const add=(x,k,s)=>x.map((v,i)=>v+s*k[i]);
  const derivative=(x,t)=>{const k=field(x.slice(),t);if(!Array.isArray(k)||k.length!==x.length)throw new RangeError("vector field dimension mismatch");finite(k,"vector field");return k;};
  const dt=(end-start)/steps,points=[initial.slice()];let y=initial.slice(),t=start;
  for(let i=0;i<steps;i++){
    const k1=derivative(y,t),k2=derivative(add(y,k1,dt/2),t+dt/2),k3=derivative(add(y,k2,dt/2),t+dt/2),k4=derivative(add(y,k3,dt),t+dt);
    y=y.map((v,j)=>v+dt*(k1[j]+2*k2[j]+2*k3[j]+k4[j])/6);finite(y,"RK4 state");points.push(y.slice());t=start+(i+1)*dt;
  }
  return points;
}
export function greedyMeshVoxels({data,size,empty=0,mergeKey=v=>v}={}) {
  if(!Array.isArray(size)||size.length!==3||size.some(n=>!Number.isInteger(n)||n<1)||!ArrayBuffer.isView(data)&&!Array.isArray(data))throw new RangeError("3D voxel data and positive size required");
  const [nx,ny,nz]=size;if(data.length!==nx*ny*nz)throw new RangeError("voxel data length mismatch");
  const at=(x,y,z)=>data[x+nx*(y+ny*z)];
  const quads=[];
  // Sweep each principal axis and both signs. A 2D mask is formed at every
  // slice; rectangles merge only when the face material key is identical.
  for(let axis=0;axis<3;axis++)for(const sign of [-1,1]){
    const u=(axis+1)%3,v=(axis+2)%3,dims=[nx,ny,nz],nu=dims[u],nv=dims[v],nd=dims[axis];
    for(let slice=0;slice<nd;slice++){
      const mask=Array(nu*nv).fill(null);
      for(let j=0;j<nv;j++)for(let i=0;i<nu;i++){
        const p=[0,0,0];p[axis]=slice;p[u]=i;p[v]=j;
        const q=p.slice();q[axis]+=sign;
        const a=at(...p),b=q[axis]>=0&&q[axis]<nd?at(...q):empty;
        if(a!==empty&&(b===empty||!Object.is(mergeKey(a),mergeKey(b))))mask[i+nu*j]={material:a,key:mergeKey(a),normal:sign};
      }
      for(let j=0;j<nv;j++)for(let i=0;i<nu;i++){
        const face=mask[i+nu*j];if(!face)continue;
        let w=1;while(i+w<nu&&mask[i+w+nu*j]?.key===face.key)w++;
        let h=1,ok=true;while(j+h<nv&&ok){for(let x=0;x<w;x++)if(mask[i+x+nu*(j+h)]?.key!==face.key){ok=false;break;}if(ok)h++;}
        for(let y=0;y<h;y++)for(let x=0;x<w;x++)mask[i+x+nu*(j+y)]=null;
        const lo=[0,0,0],hi=[0,0,0];lo[axis]=slice+(sign>0?1:0);hi[axis]=lo[axis];lo[u]=i;hi[u]=i+w;lo[v]=j;hi[v]=j+h;
        quads.push({axis,sign,lo,hi,material:face.material,key:face.key});
      }
    }
  }
  return quads;
}
