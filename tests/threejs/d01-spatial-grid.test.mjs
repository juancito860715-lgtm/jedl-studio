import test from "node:test";
import assert from "node:assert/strict";
import { UniformGrid3D } from "../../src/threejs/spatial-grid.mjs";

test("uniform grid maps negative coordinates with floor, not truncation", () => {
  const grid = new UniformGrid3D({ cellSize: 2, origin: [0, 0, 0] });
  assert.deepEqual(grid.cellOf([-0.1, 0, 2.1]), [-1, 0, 1]);
});
test("AABB insertion spans cells and query returns each intersecting entry once", () => {
  const grid = new UniformGrid3D({ cellSize: 1 });
  grid.insert("wide", [0.2, 0.2, 0.2], [2.2, 1.2, 1.2], { id: "wide" });
  grid.insert("far", [5, 5, 5], [5.5, 5.5, 5.5], { id: "far" });
  assert.deepEqual(grid.queryAABB([1.5, 0, 0], [2.5, 2, 2]).map(x => x.id), ["wide"]);
});
test("updates and removals clear old cell membership", () => {
  const grid = new UniformGrid3D({ cellSize: 1 });
  grid.insert("item", [0, 0, 0], [0.2, 0.2, 0.2], "old");
  grid.insert("item", [4, 4, 4], [4.2, 4.2, 4.2], "new");
  assert.deepEqual(grid.queryAABB([-1, -1, -1], [1, 1, 1]), []);
  assert.deepEqual(grid.queryAABB([4, 4, 4], [5, 5, 5]), ["new"]);
  assert.equal(grid.remove("item"), true);
  assert.equal(grid.size, 0);
  assert.deepEqual(grid.queryAABB([4, 4, 4], [5, 5, 5]), []);
});
test("invalid cell sizes and bounds are rejected", () => {
  assert.throws(() => new UniformGrid3D({ cellSize: 0 }), RangeError);
  const grid = new UniformGrid3D();
  assert.throws(() => grid.insert("bad", [2, 0, 0], [1, 1, 1]), RangeError);
  assert.throws(() => grid.queryAABB([0, 0], [1, 1]), RangeError);
});
