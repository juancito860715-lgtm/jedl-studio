#!/usr/bin/env python3
"""Exercise the real Godot GLB importer and prove the CI import gate would reject it."""
from __future__ import annotations

import argparse
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path


IMPORT_GATE_PATTERN = re.compile(
    r"ERROR:|SCRIPT ERROR:|Parse Error:|Failed to load|Failed importing",
    re.IGNORECASE,
)
IMPORTER_ERROR_PATTERN = re.compile(
    r"ERROR:|SCRIPT ERROR:|Parse Error:|Failed to load|Failed importing|"
    r"ERR_FILE_CORRUPT|invalid glTF|invalid GLB|corrupt",
    re.IGNORECASE,
)


def ci_import_gate_would_fail(return_code: int, output: str) -> bool:
    """Mirror the exact nonzero-exit/log-error condition used by the workflow."""
    return return_code != 0 or bool(IMPORT_GATE_PATTERN.search(output))


def negative_import_was_rejected(return_code: int, output: str, filename: str = "incompatible.glb") -> bool:
    """Require fixture-specific importer rejection and proof the workflow gate trips."""
    lines = output.splitlines()
    matching_positions = [index for index, line in enumerate(lines) if filename.lower() in line.lower()]
    if not matching_positions or not ci_import_gate_would_fail(return_code, output):
        return False
    for position in matching_positions:
        start = max(0, position - 8)
        end = min(len(lines), position + 9)
        if any(IMPORTER_ERROR_PATTERN.search(line) for line in lines[start:end]):
            return True
    return return_code != 0 and bool(IMPORTER_ERROR_PATTERN.search(output))


def make_invalid_glb(path: Path) -> None:
    # Valid GLB v2 container header, but an empty JSON chunk: the real importer
    # must reject the resource rather than treating it as a valid scene.
    json_chunk_type = 0x4E4F534A
    path.write_bytes(
        struct.pack("<4sII", b"glTF", 2, 20)
        + struct.pack("<II", 0, json_chunk_type)
    )


def run_negative_import(godot_binary: Path) -> dict:
    if not godot_binary.is_file():
        raise FileNotFoundError(f"Godot editor binary does not exist: {godot_binary}")
    with tempfile.TemporaryDirectory(prefix="jedl-godot-negative-import-") as temp:
        project = Path(temp)
        (project / "tests/negative").mkdir(parents=True)
        (project / "project.godot").write_text(
            '[application]\nconfig/name="JEDL Negative GLB Import Fixture"\n'
            '[rendering]\nrenderer/rendering_method="gl_compatibility"\n',
            encoding="utf-8",
        )
        fixture = project / "tests/negative/incompatible.glb"
        make_invalid_glb(fixture)
        command = [
            str(godot_binary),
            "--headless",
            "--editor",
            "--import",
            "--path",
            str(project),
            "--verbose",
        ]
        completed = subprocess.run(
            command,
            cwd=project,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=180,
            check=False,
        )
        output = completed.stdout or ""
        if not negative_import_was_rejected(completed.returncode, output):
            raise RuntimeError(
                "Godot did not emit a fixture-specific import error that trips the workflow's CI gate "
                "for tests/negative/incompatible.glb. "
                f"exit={completed.returncode}\n{output[-8000:]}"
            )
        return {
            "fixture": "tests/negative/incompatible.glb",
            "godotExitCode": completed.returncode,
            "importerRejectedFixture": True,
            "ciGateWouldFail": True,
            "errorLines": [
                line.strip() for line in output.splitlines()
                if "incompatible.glb" in line.lower() or IMPORT_GATE_PATTERN.search(line)
            ][-12:],
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", type=Path, required=True)
    args = parser.parse_args()
    result = run_negative_import(args.godot.resolve())
    print(
        "GODOT_NEGATIVE_IMPORT_OK: "
        f"fixture={result['fixture']} exit={result['godotExitCode']} "
        f"importerRejectedFixture=true ciGateWouldFail={str(result['ciGateWouldFail']).lower()}"
    )
    for line in result["errorLines"]:
        print("GODOT_NEGATIVE_IMPORT_EVIDENCE: " + line)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"GODOT_NEGATIVE_IMPORT_FAILED: {error}", file=sys.stderr)
        raise
