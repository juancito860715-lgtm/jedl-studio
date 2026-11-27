import * as THREE from "three";

function applyTransform(object, transform = {}) {
  if (transform.position) object.position.fromArray(transform.position);
  if (transform.rotation) object.rotation.fromArray(transform.rotation);
  if (transform.scale) object.scale.fromArray(transform.scale);
  return object;
}

export function attachSceneNode(parent, child, transform = {}) {
  if (!(parent instanceof THREE.Object3D) || !(child instanceof THREE.Object3D)) {
    throw new TypeError("parent and child must be THREE.Object3D instances");
  }
  applyTransform(child, transform);
  parent.add(child);
  parent.updateMatrixWorld(true);
  return child;
}

export function createInstancedBatch(geometry, material, matrices) {
  if (!(geometry instanceof THREE.BufferGeometry) || !Array.isArray(matrices) ||
      matrices.some(matrix => !(matrix instanceof THREE.Matrix4))) {
    throw new TypeError("BufferGeometry and an array of Matrix4 transforms are required");
  }
  const mesh = new THREE.InstancedMesh(geometry, material, matrices.length);
  matrices.forEach((matrix, index) => mesh.setMatrixAt(index, matrix));
  mesh.instanceMatrix.needsUpdate = true;
  mesh.computeBoundingSphere();
  return mesh;
}

export function createSharedGeometryMeshes(geometry, material, transforms) {
  if (!(geometry instanceof THREE.BufferGeometry) || !Array.isArray(transforms)) {
    throw new TypeError("BufferGeometry and transforms array are required");
  }
  return transforms.map(transform => applyTransform(new THREE.Mesh(geometry, material), transform));
}

export function createDistanceLOD(levels, { hysteresis = 0 } = {}) {
  if (!Array.isArray(levels) || levels.length === 0 || !(hysteresis >= 0 && hysteresis < 1)) {
    throw new RangeError("levels and hysteresis are invalid");
  }
  const sorted = levels.slice().sort((a, b) => a.distance - b.distance);
  if (sorted.some((level, index) => !(level.object instanceof THREE.Object3D) ||
      !Number.isFinite(level.distance) || level.distance < 0 ||
      (index > 0 && level.distance === sorted[index - 1].distance))) {
    throw new RangeError("each LOD level needs a unique nonnegative distance and Object3D");
  }
  const lod = new THREE.LOD();
  for (const level of sorted) lod.addLevel(level.object, level.distance, hysteresis);
  return lod;
}

export function isBoxVisibleInCamera(box, camera) {
  if (!(box instanceof THREE.Box3) || !(camera instanceof THREE.Camera)) {
    throw new TypeError("Box3 and Camera are required");
  }
  camera.updateMatrixWorld(true);
  const projectionView = new THREE.Matrix4().multiplyMatrices(
    camera.projectionMatrix, camera.matrixWorldInverse
  );
  return new THREE.Frustum().setFromProjectionMatrix(projectionView).intersectsBox(box);
}

export function createFixedStepAccumulator({
  stepSeconds = 1 / 60,
  maxSubSteps = 5,
  maxFrameDelta = 0.25
} = {}) {
  if (!(stepSeconds > 0) || !Number.isFinite(stepSeconds) ||
      !Number.isInteger(maxSubSteps) || maxSubSteps < 1 ||
      !(maxFrameDelta > 0) || !Number.isFinite(maxFrameDelta)) {
    throw new RangeError("fixed-step configuration is invalid");
  }
  let accumulator = 0;
  return {
    advance(deltaSeconds, step) {
      if (!Number.isFinite(deltaSeconds) || deltaSeconds < 0 || typeof step !== "function") {
        throw new RangeError("deltaSeconds and step callback are invalid");
      }
      const accepted = Math.min(deltaSeconds, maxFrameDelta);
      let droppedTime = deltaSeconds - accepted;
      accumulator += accepted;
      let steps = 0;
      while (accumulator >= stepSeconds && steps < maxSubSteps) {
        step(stepSeconds);
        accumulator -= stepSeconds;
        steps++;
      }
      if (accumulator >= stepSeconds) {
        const retained = accumulator % stepSeconds;
        droppedTime += accumulator - retained;
        accumulator = retained;
      }
      return { steps, interpolationAlpha: accumulator / stepSeconds, droppedTime };
    },
    reset() { accumulator = 0; },
    get remainderSeconds() { return accumulator; }
  };
}
