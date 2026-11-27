// Uniform 3D spatial hash grid for point or AABB scene queries.
// Each entry is inserted into every cell overlapped by its world-space bounds.
function vector3(value, label) {
  if (!Array.isArray(value) || value.length !== 3 || !value.every(Number.isFinite)) {
    throw new RangeError(label + " must be a finite 3D vector");
  }
  return value;
}
function validBounds(min, max) {
  vector3(min, "min");
  vector3(max, "max");
  if (min.some((v, axis) => v > max[axis])) throw new RangeError("min must not exceed max");
}
function intersects(a, b) {
  return a.min.every((v, axis) => v <= b.max[axis] && a.max[axis] >= b.min[axis]);
}
export class UniformGrid3D {
  constructor({ cellSize = 1, origin = [0, 0, 0] } = {}) {
    if (!(Number.isFinite(cellSize) && cellSize > 0)) throw new RangeError("cellSize must be positive and finite");
    this.cellSize = cellSize;
    this.origin = vector3(origin, "origin").slice();
    this.cells = new Map();
    this.entries = new Map();
  }
  cellOf(point) {
    vector3(point, "point");
    return point.map((v, axis) => Math.floor((v - this.origin[axis]) / this.cellSize));
  }
  key(x, y, z) { return x + "," + y + "," + z; }
  keysFor(min, max) {
    validBounds(min, max);
    const lo = this.cellOf(min), hi = this.cellOf(max), keys = [];
    for (let x = lo[0]; x <= hi[0]; x++)
      for (let y = lo[1]; y <= hi[1]; y++)
        for (let z = lo[2]; z <= hi[2]; z++) keys.push(this.key(x, y, z));
    return keys;
  }
  insert(id, min, max = min, value = id) {
    if (id === undefined || id === null) throw new TypeError("id is required");
    this.remove(id);
    validBounds(min, max);
    const bounds = { min: min.slice(), max: max.slice() };
    const keys = this.keysFor(bounds.min, bounds.max);
    this.entries.set(id, { bounds, value, keys });
    for (const key of keys) {
      if (!this.cells.has(key)) this.cells.set(key, new Set());
      this.cells.get(key).add(id);
    }
    return this;
  }
  remove(id) {
    const entry = this.entries.get(id);
    if (!entry) return false;
    for (const key of entry.keys) {
      const bucket = this.cells.get(key);
      bucket.delete(id);
      if (bucket.size === 0) this.cells.delete(key);
    }
    this.entries.delete(id);
    return true;
  }
  queryAABB(min, max) {
    const query = { min: min.slice(), max: max.slice() };
    validBounds(query.min, query.max);
    const candidates = new Set();
    for (const key of this.keysFor(query.min, query.max)) {
      for (const id of this.cells.get(key) || []) candidates.add(id);
    }
    const result = [];
    for (const id of candidates) {
      const entry = this.entries.get(id);
      if (entry && intersects(entry.bounds, query)) result.push(entry.value);
    }
    return result;
  }
  clear() { this.cells.clear(); this.entries.clear(); }
  get size() { return this.entries.size; }
}
