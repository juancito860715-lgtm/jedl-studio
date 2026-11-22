#!/usr/bin/env python3
"""Exercise Godot's real importer with a structurally valid GLB requiring meshopt."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path


IMPORT_GATE_PATTERN = re.compile(
    r"ERROR:|SCRIPT ERROR:|Parse Error:|Failed to load|Failed importing"
)
MESHOPT_UNSUPPORTED_PATTERN = re.compile(
    r"EXT_meshopt_compression.{0,200}(?:not supported|unsupported|does not support)|"
    r"(?:not supported|unsupported|does not support).{0,200}EXT_meshopt_compression",
    re.IGNORECASE,
)


def ci_import_gate_would_fail(return_code: int, output: str) -> bool:
    """Mirror the workflow's nonzero-exit/log-error condition."""
    return return_code != 0 or bool(IMPORT_GATE_PATTERN.search(output))


def meshopt_extension_was_rejected(
    return_code: int, output: str, filename: str = "incompatible.glb"
) -> bool:
    """Require this fixture and an explicit unsupported-meshopt importer diagnostic."""
    lines = output.splitlines()
    positions = [i for i, line in enumerate(lines) if filename.lower() in line.lower()]
    if not positions or not ci_import_gate_would_fail(return_code, output):
        return False
    for position in positions:
        nearby = "\n".join(lines[max(0, position - 12):min(len(lines), position + 21)])
        if MESHOPT_UNSUPPORTED_PATTERN.search(nearby) and IMPORT_GATE_PATTERN.search(nearby):
            return True
    return False


def make_meshopt_glb(path: Path) -> None:
    """Write a valid GLB v2 with a mesh and required meshopt-compressed POSITION bufferView."""
    document = {
        "asset": {"version": "2.0", "generator": "JEDL CI meshopt negative fixture"},
        "extensionsUsed": ["EXT_meshopt_compression"],
        "extensionsRequired": ["EXT_meshopt_compression"],
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
        "buffers": [{"byteLength": 12}],
        "bufferViews": [{
            "buffer": 0,
            "byteOffset": 0,
            "byteLength": 12,
            "extensions": {
                "EXT_meshopt_compression": {
                    "buffer": 0,
                    "byteOffset": 0,
                    "byteLength": 12,
                    "byteStride": 12,
                    "count": 1,
                    "mode": "ATTRIBUTES",
                    "filter": "NONE",
                }
            },
        }],
        "accessors": [{
            "bufferView": 0,
            "componentType": 5126,
            "count": 1,
            "type": "VEC3",
            "min": [0.0, 0.0, 0.0],
            "max": [0.0, 0.0, 0.0],
        }],
    }
    json_payload = json.dumps(document, separators=(",", ":")).encode("utf-8")
    json_payload += b" " * ((4 - len(json_payload) % 4) % 4)
    binary_payload = bytes(12)
    if len(binary_payload) % 4:
        binary_payload += bytes(4 - len(binary_payload) % 4)
    json_chunk = struct.pack("<II", len(json_payload), 0x4E4F534A) + json_payload
    bin_chunk = struct.pack("<II", len(binary_payload), 0x004E4942) + binary_payload
    total_length = 12 + len(json_chunk) + len(bin_chunk)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, total_length) + json_chunk + bin_chunk)


def run_negative_import(godot_binary: Path) -> dict:
    if not godot_binary.is_file():
        raise FileNotFoundError(f"Godot editor binary does not exist: {godot_binary}")
    with tempfile.TemporaryDirectory(prefix="jedl-godot-negative-meshopt-") as temp:
        project = Path(temp)
        (project / "tests/negative").mkdir(parents=True)
        (project / "project.godot").write_text(
            '[application]\nconfig/name="JEDL Negative meshopt GLB Fixture"\n'
            '[rendering]\nrenderer/rendering_method="gl_compatibility"\n',
            encoding="utf-8",
        )
        fixture = project / "tests/negative/incompatible.glb"
        make_meshopt_glb(fixture)
        command = [
            str(godot_binary), "--headless", "--editor", "--import",
            "--path", str(project), "--verbose",
        ]
        completed = subprocess.run(
            command, cwd=project, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=180, check=False,
        )
        output = completed.stdout or ""
        if not meshopt_extension_was_rejected(completed.returncode, output):
            raise RuntimeError(
                "Godot did not explicitly reject the valid GLB fixture because of "
                "EXT_meshopt_compression, or the workflow error gate did not trip. "
                f"exit={completed.returncode}\n{output[-10000:]}"
            )
        return {
            "fixture": "tests/negative/incompatible.glb",
            "fixtureSha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
            "fixtureBytes": fixture.stat().st_size,
            "requiredExtension": "EXT_meshopt_compression",
            "godotExitCode": completed.returncode,
            "importerRejectedForUnsupportedExtension": True,
            "ciGateWouldFail": True,
            "errorLines": [
                line.strip() for line in output.splitlines()
                if "incompatible.glb" in line.lower()
                or "EXT_meshopt_compression" in line
                or IMPORT_GATE_PATTERN.search(line)
            ][-20:],
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", type=Path, required=True)
    args = parser.parse_args()
    result = run_negative_import(args.godot.resolve())
    print(
        "GODOT_NEGATIVE_IMPORT_OK: "
        f"fixture={result['fixture']} bytes={result['fixtureBytes']} "
        f"sha256={result['fixtureSha256']} "
        "requiredExtension=EXT_meshopt_compression "
        "importerRejectedForUnsupportedExtension=true ciGateWouldFail=true"
    )
    for line in result["errorLines"]:
        print("GODOT_NEGATIVE_IMPORT_EVIDENCE: " + line)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"GODOT_NEGATIVE_IMPORT_FAILED: {error}", file=sys.stderr)
        raise
