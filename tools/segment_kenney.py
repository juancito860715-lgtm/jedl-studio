#!/usr/bin/env python3
"""Split Kenney limb sprites along their alpha-mask principal axis.

Geometric pre-segmentation only: it does not infer elbow/knee anatomy.
The split is perpendicular to the principal axis and includes a small overlap.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image


def split_limb(image: Image.Image, overlap: int = 3):
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    rgba = image.convert("RGBA")
    alpha = np.asarray(rgba.getchannel("A"))
    ys, xs = np.nonzero(alpha > 8)
    if len(xs) < 16:
        raise ValueError("limb has insufficient non-transparent pixels")
    points = np.column_stack((xs, ys)).astype(float)
    center = points.mean(axis=0)
    covariance = np.cov((points - center).T)
    values, vectors = np.linalg.eigh(covariance)
    axis = vectors[:, int(np.argmax(values))]
    if axis[0] < 0:
        axis = -axis
    projections = (points - center) @ axis
    lo, hi = float(projections.min()), float(projections.max())
    if hi - lo < 8:
        raise ValueError("limb principal axis is too short")
    cut = (lo + hi) / 2
    gy, gx = np.indices(alpha.shape)
    projected = ((np.column_stack((gx.ravel(), gy.ravel())) - center) @ axis).reshape(alpha.shape)
    upper_mask = projected <= cut + overlap
    lower_mask = projected >= cut - overlap
    upper, lower = rgba.copy(), rgba.copy()
    ua, la = alpha.copy(), alpha.copy()
    ua[~upper_mask] = 0
    la[~lower_mask] = 0
    upper.putalpha(Image.fromarray(ua))
    lower.putalpha(Image.fromarray(la))
    pivot = center + axis * cut
    return upper, lower, {
        "axis": [float(axis[0]), float(axis[1])],
        "cutXY": [float(pivot[0]), float(pivot[1])],
        "pivotX": float(pivot[0] / rgba.width),
        "pivotY": float(pivot[1] / rgba.height),
        "overlapPx": int(overlap),
        "method": "alpha-mask-pca-midpoint-provisional",
    }


def process(source: Path, output: Path, overlap: int = 3):
    output.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        upper, lower, metadata = split_limb(image, overlap)
        upper.save(output / "segment_upper.png", optimize=True)
        lower.save(output / "segment_lower.png", optimize=True)
    (output / "segment.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    return metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--overlap", type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(process(Path(args.source), Path(args.out), args.overlap), indent=2))


if __name__ == "__main__":
    main()
