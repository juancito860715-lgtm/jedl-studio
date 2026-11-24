#!/usr/bin/env node
/**
 * Normalize pinned GLB assets for the stock Godot 4.5.1 glTF importer.
 * Meshopt is decoded on the build host; KHR_mesh_quantization is converted
 * back to core glTF vertex formats. Runtime/APK needs no decoder or network.
 */
import { readdir, readFile, rename } from "node:fs/promises";
import { join } from "node:path";
import { NodeIO } from "@gltf-transform/core";
import { EXTMeshoptCompression, KHRONOS_EXTENSIONS } from "@gltf-transform/extensions";
import { dequantize } from "@gltf-transform/functions";
import { MeshoptDecoder } from "meshoptimizer";

const root = "assets/gallery/3d/t3";
const files = (await readdir(root)).filter((name) => name.endsWith(".glb")).sort();
if (files.length !== 8) throw new Error(`Expected 8 pinned T3 GLBs, found ${files.length}`);
await MeshoptDecoder.ready;
const io = new NodeIO()
  .registerExtensions([...KHRONOS_EXTENSIONS, EXTMeshoptCompression])
  .registerDependencies({ "meshopt.decoder": MeshoptDecoder });

function glbJson(buffer) {
  if (buffer.toString("ascii", 0, 4) !== "glTF") throw new Error("Invalid GLB magic");
  let offset = 12;
  while (offset + 8 <= buffer.length) {
    const length = buffer.readUInt32LE(offset);
    const type = buffer.readUInt32LE(offset + 4);
    offset += 8;
    if (type === 0x4e4f534a) return JSON.parse(buffer.toString("utf8", offset, offset + length).replace(/\\0+$/g, "").trim());
    offset += length;
  }
  throw new Error("GLB JSON chunk missing");
}

for (const name of files) {
  const input = join(root, name);
  const temporary = input + ".normalized";
  const document = await io.read(input);
  await document.transform(dequantize());
  await io.write(temporary, document);
  const normalized = await readFile(temporary);
  const json = glbJson(normalized);
  const required = json.extensionsRequired ?? [];
  const unsupported = required.filter((ext) =>
    ["EXT_meshopt_compression", "KHR_mesh_quantization", "KHR_draco_mesh_compression"].includes(ext)
  );
  if (unsupported.length) throw new Error(`${name}: unsupported required extensions remain: ${unsupported.join(", ")}`);
  if (name === "casual_walker.glb" && (!(json.skins?.length) || !(json.animations?.length) || !(json.meshes?.length))) {
    throw new Error("Pedestrian GLB must contain a mesh, skin and animation clips");
  }
  await rename(temporary, input);
  console.log(`GLB_GODOT_COMPAT_OK ${name} bytes=${normalized.length} animations=${json.animations?.length ?? 0} skins=${json.skins?.length ?? 0}`);
}
console.log("T3_GLB_NORMALIZATION_OK");
