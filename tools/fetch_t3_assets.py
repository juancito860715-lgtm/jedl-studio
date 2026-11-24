#!/usr/bin/env python3
"""Fetch pinned CC0 T3 models and generate original offline WAV cues.

The build runs this before Godot's import scan, so all fetched models and audio
are embedded in the exported APK. No network access is required at app runtime.
"""
from __future__ import annotations

import math
import random
import struct
import urllib.request
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CITY_REVISION = "d9de7e25d476d8b8572971840b129c28a68e9cf7"
CITY_BASE = f"https://raw.githubusercontent.com/kayquer/kit-cidade-lowpoly/{CITY_REVISION}/"
MODEL_SOURCES = {
    "casual_walker.glb": "https://tevy.dev/models/casual-walker/v1/lod1.glb",
    "crosswalk.glb": CITY_BASE + "models/ruas/asfalto_faixa_pedestre.glb",
    "road_straight.glb": CITY_BASE + "models/ruas/asfalto_reta.glb",
    "sidewalk.glb": CITY_BASE + "models/ruas/calcada.glb",
    "house_simple.glb": CITY_BASE + "models/residencial/casa_simples.glb",
    "carro.glb": CITY_BASE + "models/veiculos/carro.glb",
    "traffic_light.glb": CITY_BASE + "models/mobiliario/semaforo.glb",
    "street_light.glb": CITY_BASE + "models/mobiliario/poste_luz.glb",
}
SAMPLE_RATE = 22050


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "JEDL-Studio/1.0 asset-fetch"})
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = response.read()
    if len(payload) < 20 or payload[:4] != b"glTF":
        raise RuntimeError(f"Downloaded model is not a valid GLB: {url}")
    destination.write_bytes(payload)
    print(f"ASSET_OK {destination.relative_to(ROOT)} {len(payload)} bytes")


def write_wav(path: Path, samples: list[float], loop: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    peak = max((abs(v) for v in samples), default=1.0) or 1.0
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(SAMPLE_RATE)
        out.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, v / peak * 0.82)) * 32767)) for v in samples))
    print(f"AUDIO_OK {path.relative_to(ROOT)} {path.stat().st_size} bytes loop={loop}")


def make_footsteps() -> list[float]:
    duration = 4.0
    count = int(SAMPLE_RATE * duration)
    samples = [0.0] * count
    rng = random.Random(2711)
    for step in range(7):
        start = int((0.12 + step * 0.58) * SAMPLE_RATE)
        length = int(0.19 * SAMPLE_RATE)
        for i in range(length):
            t = i / SAMPLE_RATE
            envelope = math.exp(-22.0 * t) * min(1.0, t * 90.0)
            noise = rng.uniform(-1.0, 1.0)
            thump = math.sin(2.0 * math.pi * (78.0 - 35.0 * t) * t)
            grit = math.sin(2.0 * math.pi * 1150.0 * t) * 0.18
            if start + i < count:
                samples[start + i] += envelope * (0.62 * thump + 0.22 * noise + grit)
    return samples


def make_door() -> list[float]:
    duration = 0.82
    count = int(SAMPLE_RATE * duration)
    rng = random.Random(882)
    samples = [0.0] * count
    for i in range(count):
        t = i / SAMPLE_RATE
        creak_env = math.exp(-7.0 * t) * min(1.0, t * 35.0)
        creak = math.sin(2.0 * math.pi * (310.0 + 80.0 * math.sin(t * 7.0)) * t) * 0.18
        noise = rng.uniform(-1.0, 1.0) * math.exp(-48.0 * max(0.0, t - 0.12))
        slam_t = t - 0.56
        slam = 0.0
        if slam_t >= 0.0:
            slam = math.exp(-42.0 * slam_t) * (0.85 * math.sin(2.0 * math.pi * 92.0 * slam_t) + 0.25 * rng.uniform(-1.0, 1.0))
        samples[i] = creak_env * creak + 0.24 * noise + slam
    return samples


def make_engine() -> list[float]:
    duration = 5.0
    count = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(count):
        t = i / SAMPLE_RATE
        phase = 2.0 * math.pi * 54.0 * t
        idle = math.sin(phase) * 0.40 + math.sin(2.0 * phase + 0.2) * 0.19 + math.sin(3.0 * phase + 0.6) * 0.08
        rev = 1.0 + 0.24 * (0.5 + 0.5 * math.sin(2.0 * math.pi * 0.24 * t))
        harmonics = math.sin(phase * rev) * 0.36 + math.sin(2.0 * phase * rev) * 0.17 + math.sin(4.0 * phase * rev) * 0.06
        road = math.sin(2.0 * math.pi * 36.0 * t) * 0.08
        samples.append((idle + harmonics + road) * 0.55)
    return samples


def main() -> None:
    model_root = ROOT / "assets/gallery/3d/t3"
    audio_root = ROOT / "assets/audio/t3"
    for filename, url in MODEL_SOURCES.items():
        download(url, model_root / filename)
    write_wav(audio_root / "footsteps.wav", make_footsteps())
    write_wav(audio_root / "car_door.wav", make_door())
    write_wav(audio_root / "car_engine_loop.wav", make_engine(), loop=True)
    print(f"T3_ASSETS_OK models={len(MODEL_SOURCES)} audio=3 city_revision={CITY_REVISION}")


if __name__ == "__main__":
    main()
