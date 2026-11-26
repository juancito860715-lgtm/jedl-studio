import test from "node:test";
import assert from "node:assert/strict";
import { chromium } from "playwright";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
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
test("Three.js creates WebGL2, compiles GLSL ES 3.00 and matches numeric pixel probes",async()=>{
  const server=serve(); await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
  const address=server.address();
  const browser=await chromium.launch({headless:true,args:["--enable-webgl","--ignore-gpu-blocklist","--use-angle=swiftshader","--enable-unsafe-swiftshader"]});
  try{
    const page=await browser.newPage();
    const errors=[];page.on("pageerror",e=>errors.push(e.message));
    await page.goto(`http://127.0.0.1:${address.port}/tests/threejs/browser/webgl2.html`);
    await page.waitForFunction(()=>window.webgl2Result!==undefined,{timeout:15000});
    const result=await page.evaluate(()=>window.webgl2Result);
    assert.deepEqual(errors,[]);
    assert.match(result.contextVersion,/WebGL 2/);
    assert.equal(result.shaderCompile,true);
    assert.equal(result.threeRendererCompile,true);
    assert.equal(result.threeRevision,"180");
    assert.ok(Math.abs(result.pixel[0]-96)<=1,`SDF probe pixel ${result.pixel[0]}`);
    assert.ok(Math.abs(result.pixel[1]-255)<=1,`Fresnel probe pixel ${result.pixel[1]}`);
    assert.ok(Math.abs(result.pixel[2]-94)<=1,`Beer-Lambert probe pixel ${result.pixel[2]}`);
  }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
});
