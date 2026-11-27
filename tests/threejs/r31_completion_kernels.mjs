// Matching implementation of the scoped R31 completion kernels.
const finite=(xs,name)=>{if(xs.some(v=>!Number.isFinite(v)))throw new RangeError(name+" must be finite");};
const norm=v=>Math.hypot(...v);
const unit=(v,name="vector")=>{const n=norm(v);if(n<=1e-15)throw new RangeError(name+" must be nonzero");return v.map(x=>x/n);};
export function pointSegmentDistance2d(p,a,b){
  if(p.length!==2||a.length!==2||b.length!==2)throw new RangeError("2-vectors required");
  finite([...p,...a,...b],"coordinates");
  const dx=b[0]-a[0],dy=b[1]-a[1],den=dx*dx+dy*dy;
  if(den<=1e-30)return Math.hypot(p[0]-a[0],p[1]-a[1]);
  const t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den));
  return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy);
}
export function impastoHeight(p,strokes){
  if(p.length!==2)throw new RangeError("point must be 2D");finite(p,"point");
  let h=0;
  for(const s of strokes){if(s.length!==6)throw new RangeError("stroke needs six values");finite(s,"stroke");
    const [x0,y0,x1,y1,r,a]=s;if(!(r>0))throw new RangeError("radius must be positive");
    const d=pointSegmentDistance2d(p,[x0,y0],[x1,y1]),q=Math.max(0,1-(d/r)**2);h+=a*q*q;
  }return h;
}
export function heightGradient(fn,p,step=1e-4){
  finite([...p,step],"gradient inputs");if(p.length!==2||!(step>0))throw new RangeError("2D point and positive step required");
  const [x,y]=p;return [(fn([x+step,y])-fn([x-step,y]))/(2*step),(fn([x,y+step])-fn([x,y-step]))/(2*step)];
}
export function impastoNormal(g,strength=1){
  if(g.length!==2)throw new RangeError("gradient must be 2D");finite([...g,strength],"normal inputs");
  return unit([-strength*g[0],1,-strength*g[1]],"normal");
}
export function orientedPeriodicDetail(p,flow,frequency,anisotropy=.8,phase=0){
  if(p.length!==2||flow.length!==2)throw new RangeError("2D vectors required");
  finite([...p,...flow,frequency,anisotropy,phase],"noise inputs");
  if(!(frequency>0)||anisotropy<0||anisotropy>1)throw new RangeError("invalid frequency/anisotropy");
  const f=unit(flow,"flow"),n=[-f[1],f[0]],along=p[0]*f[0]+p[1]*f[1],across=p[0]*n[0]+p[1]*n[1];
  return anisotropy*Math.sin(2*Math.PI*frequency*along+phase)+(1-anisotropy)*Math.sin(2*Math.PI*frequency*4*across+phase*.5);
}
export function erodedHeight(base,p,flow,amplitude,slope,frequency,anisotropy=.8,phase=0){
  finite([base,amplitude,slope,frequency,anisotropy,phase],"erosion inputs");
  if(amplitude<0||slope<0)throw new RangeError("amplitude/slope must be nonnegative");
  return base+amplitude*Math.min(1,slope)*orientedPeriodicDetail(p,flow,frequency,anisotropy,phase);
}
export function rk4Step(field,state,time,dt){
  finite([...state,time,dt],"RK4 inputs");if(dt===0)return [...state];
  const add=(x,k,s)=>x.map((v,i)=>v+s*k[i]);
  const deriv=(x,t)=>{const k=field(x,t);if(k.length!==state.length)throw new RangeError("field dimension mismatch");finite(k,"field derivative");return k;};
  const k1=deriv(state,time),k2=deriv(add(state,k1,dt/2),time+dt/2),k3=deriv(add(state,k2,dt/2),time+dt/2),k4=deriv(add(state,k3,dt),time+dt);
  const out=state.map((v,i)=>v+dt*(k1[i]+2*k2[i]+2*k3[i]+k4[i])/6);finite(out,"RK4 result");return out;
}
export function integrateRk4(field,initial,start,end,steps){
  if(!Number.isInteger(steps)||steps<=0||!Number.isFinite(start)||!Number.isFinite(end))throw new RangeError("positive integer steps and finite times required");
  let state=[...initial];finite(state,"initial state");const dt=(end-start)/steps;let t=start;
  for(let i=0;i<steps;i++){state=rk4Step(field,state,t,dt);t+=dt;}return state;
}
export function greedyRectangles(mask){
  if(!Array.isArray(mask)||!mask.length||!mask[0].length||mask.some(r=>r.length!==mask[0].length))throw new RangeError("nonempty rectangular mask required");
  const grid=mask.map(r=>[...r]),h=grid.length,w=grid[0].length,rects=[];
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){const key=grid[y][x];if(key===null)continue;
    let x2=x+1;while(x2<w&&Object.is(grid[y][x2],key))x2++;
    let y2=y+1;while(y2<h&&grid[y2].slice(x,x2).every(v=>Object.is(v,key)))y2++;
    for(let yy=y;yy<y2;yy++)for(let xx=x;xx<x2;xx++)grid[yy][xx]=null;
    rects.push([x,y,x2,y2,key]);
  }return rects;
}
