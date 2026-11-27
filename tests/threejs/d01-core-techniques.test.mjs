import test from "node:test";
import assert from "node:assert/strict";
import * as THREE from "three";
import {
  attachSceneNode, createInstancedBatch, createSharedGeometryMeshes,
  createDistanceLOD, isBoxVisibleInCamera, createFixedStepAccumulator
} from "../../src/threejs/d01-core-techniques.mjs";

test("scene graph composes parent and local transforms", () => {
  const parent = new THREE.Group(), child = new THREE.Object3D();
  parent.position.set(2, 0, 0);
  attachSceneNode(parent, child, { position: [0, 3, 0] });
  const world = new THREE.Vector3().setFromMatrixPosition(child.matrixWorld);
  assert.deepEqual(world.toArray(), [2, 3, 0]);
  assert.equal(child.parent, parent);
});
test("instancing stores one independent matrix per instance", () => {
  const geometry = new THREE.BoxGeometry(1, 1, 1);
  const material = new THREE.MeshBasicMaterial();
  const matrices = [new THREE.Matrix4().makeTranslation(1, 0, 0), new THREE.Matrix4().makeTranslation(4, 0, 0)];
  const batch = createInstancedBatch(geometry, material, matrices);
  assert.equal(batch.count, 2);
  const actual = new THREE.Matrix4(); batch.getMatrixAt(1, actual);
  assert.ok(actual.equals(matrices[1]));
  assert.ok(batch.boundingSphere.radius > 0);
});
test("shared geometry remains the same resource across independent meshes", () => {
  const geometry = new THREE.SphereGeometry(1), material = new THREE.MeshBasicMaterial();
  const meshes = createSharedGeometryMeshes(geometry, material, [{ position: [1, 0, 0] }, { position: [-1, 0, 0] }]);
  assert.equal(meshes.length, 2);
  assert.equal(meshes[0].geometry, geometry);
  assert.equal(meshes[1].geometry, geometry);
  assert.notEqual(meshes[0].position.x, meshes[1].position.x);
});
test("LOD selects the level whose distance threshold is reached", () => {
  const high = new THREE.Object3D(), low = new THREE.Object3D();
  const lod = createDistanceLOD([{ object: low, distance: 20 }, { object: high, distance: 0 }]);
  const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
  camera.position.z = 30; camera.updateMatrixWorld(true);
  lod.update(camera);
  assert.equal(high.visible, false);
  assert.equal(low.visible, true);
});
test("frustum test rejects a box outside camera view and accepts a centered box", () => {
  const camera = new THREE.PerspectiveCamera(60, 1, 0.1, 100);
  camera.position.set(0, 0, 5); camera.lookAt(0, 0, 0); camera.updateMatrixWorld(true);
  assert.equal(isBoxVisibleInCamera(new THREE.Box3(new THREE.Vector3(-.5,-.5,-.5),new THREE.Vector3(.5,.5,.5)),camera), true);
  assert.equal(isBoxVisibleInCamera(new THREE.Box3(new THREE.Vector3(100,100,100),new THREE.Vector3(101,101,101)),camera), false);
});
test("fixed-step accumulator advances in stable quanta and bounds catch-up work", () => {
  const clock = createFixedStepAccumulator({ stepSeconds: .1, maxSubSteps: 2, maxFrameDelta: .5 });
  const calls = [];
  const result = clock.advance(.45, dt => calls.push(dt));
  assert.equal(calls.length, 2);
  assert.ok(calls.every(dt => Math.abs(dt - .1) < 1e-12));
  assert.equal(result.steps, 2);
  assert.ok(result.droppedTime > .2);
  clock.reset();
  assert.equal(clock.remainderSeconds, 0);
});
