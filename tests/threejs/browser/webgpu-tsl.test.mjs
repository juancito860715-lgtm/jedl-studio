import test from "node:test";
import assert from "node:assert/strict";
import { chromium } from "playwright";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { PNG } from "pngjs";
const root=process.cwd();
const mime={".html":"text/html",".js":"text/javascript",".mjs":"text/javascript"};
function serve(){
  return http.createServer((req,res)=>{
    const pathname=decodeURIComponent(new URL(req.url,"http://127.0.0.1").pathname);
    const target=path.resolve(root,"."+pathname);
    if(!target.startsWith(root+path.sep)){res.writeHead(403).end();return;}
    fs.readFile(target,(err,data)=>{
      if(err){res.writeHead(404).end(String(err));return;}
      res.writeHead(200,{"content-type":mime[path.extname(target)]||"application/octet-stream","cache-control":"no-store"});res.end(data);
    });
  });
}
test("Three.js WebGPURenderer uses native WebGPU, compiles TSL and matches rendered pixel",async()=>{
  const server=serve();await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
  const address=server.address();
  const browser=await chromium.launch({headless:true,args:[
    "--enable-unsafe-webgpu","--enable-webgpu-developer-features",
    "--enable-features=Vulkan","--use-vulkan","--use-angle=vulkan",
    "--ignore-gpu-blocklist","--disable-vulkan-surface"
  ]});
  try{
    const page=await browser.newPage({viewport:{width:64,height:64}});
    const errors=[];page.on("pageerror",e=>errors.push(e.message));
    await page.goto(`http://127.0.0.1:${address.port}/tests/threejs/browser/webgpu-tsl.html`);
    await page.waitForFunction(()=>window.webgpuTslResult!==undefined,{timeout:30000});
    const result=await page.evaluate(()=>window.webgpuTslResult);
    assert.deepEqual(errors,[]);
    assert.equal(result.threeRevision,"180");
    assert.equal(result.isWebGPUBackend,true,"A WebGL2 fallback is not a WebGPU pass");
    assert.equal(result.rendered,true);
    const image=PNG.sync.read(await page.locator("#probe").screenshot());
    const offset=(2*image.width+2)*4;
    const pixel=[image.data[offset],image.data[offset+1],image.data[offset+2],image.data[offset+3]];
    assert.ok(Math.abs(pixel[0]-96)<=3,`TSL SDF output channel: ${pixel[0]}`);
    assert.ok(Math.abs(pixel[1]-255)<=3,`TSL Fresnel output channel: ${pixel[1]}`);
    assert.ok(Math.abs(pixel[2]-94)<=3,`TSL Beer-Lambert output channel: ${pixel[2]}`);
  }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
});
