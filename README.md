# JEDL Studio

JEDL Studio is migrating to Godot Engine 4.4.1 as its primary 3D/2.5D runtime. The Godot project lives at the repository root (project.godot, Main.tscn) and is exported to Android by GitHub Actions.

## Godot project

- Main.tscn: 3D stage, camera, lighting and runtime UI.
- scripts/CatalogManager.gd: discovers GLB/glTF/TSCN characters and objects.
- scripts/SceneParser.gd: loads JSON scenes, instances assets, plays named animations and schedules subtitles/audio.
- scripts/MocapReceiver.gd: Godot-side integration contract for a native MediaPipe bridge and Skeleton3D bone rotations.
- assets/characters, assets/objects, assets/audio: offline asset-bank locations.
- .github/workflows/build_godot.yml: headless validation and Android debug APK artifact.

CI downloads the Khronos Fox animated GLB as a test fixture. The model uses CC0-1.0 and CC-BY-4.0 components; its attribution/license file is downloaded beside it. Credits: PixelMannen (model), tomkranis (rig/animation), AsoboStudio and scurest (glTF conversion). This fixture does not mean a complete character gallery or native MediaPipe plugin is finished.

## Build without a local computer

GitHub Actions installs Godot 4.4.1, matching Android export templates and Android SDK, validates the sample JSON/GLB, exports an ARM64 Android debug APK, and uploads it as jedl-studio-godot-android-debug-apk.

## Scene JSON

See scenes/scene.example.json. Supported fields:
- characters and objects: path, position, rotation_degrees, scale, optional animation.
- subtitles: time, duration, text.
- sounds: time, path, optional volume_db.

## MediaPipe boundary

MocapReceiver.gd defines the expected method for the native bridge. The repository does not yet contain the native MediaPipe Android plugin or a proven end-to-end camera/video-to-Skeleton3D pipeline. The receiver is an integration point only.

## Legacy Android implementation

The previous Kotlin implementation remains in app/ for reference during migration. The former Android CI is retained as a manually dispatchable legacy workflow.
