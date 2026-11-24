# JEDL Studio

JEDL Studio is migrating to Godot Engine 4.4.1 as its primary 3D/2.5D runtime. The Godot project lives at the repository root (project.godot, Main.tscn) and is exported to Android by GitHub Actions.

## Godot project

- Main.tscn: 3D stage, camera, lighting and runtime UI.
- scripts/CatalogManager.gd: validates the offline root manifest, resolves stable asset IDs, and discovers packaged GLB/glTF/TSCN resources.
- scripts/SceneParser.gd: loads JSON scenes, instances assets, plays named animations and schedules subtitles/audio.
- MediaPipe: the native Android plugin and camera/video capture bridge are not implemented in the current Godot runtime.
- assets/characters, assets/objects, assets/audio: offline asset-bank locations.
- .github/workflows/build_godot.yml: headless validation and Android debug APK artifact.

CI downloads the Khronos Fox animated GLB as a test fixture. The model uses CC0-1.0 and CC-BY-4.0 components; its attribution/license file is downloaded beside it. Credits: PixelMannen (model), tomkranis (rig/animation), AsoboStudio and scurest (glTF conversion). This fixture does not mean a complete character gallery or native MediaPipe plugin is finished.

## Build without a local computer

GitHub Actions installs Godot 4.4.1, matching Android export templates and Android SDK, validates the sample JSON/GLB, exports an ARM64 Android debug APK, and uploads it as jedl-studio-godot-android-debug-apk.

## Scene JSON

See scenes/scene.example.json. Supported fields:
- characters and objects: stable assetId, position, rotation_degrees, scale, optional animation. Legacy path-only entries remain supported.
- subtitles: time, duration, text.
- sounds: time, path, optional volume_db.

## Offline asset identity

The Godot build generates `assets/gallery/manifest.json` after downloading the curated build-time asset set. The root manifest records stable asset IDs, file sizes, SHA-256 hashes, source/license metadata and the catalog hash. Scene JSON should use `assetId`; `CatalogManager.gd` resolves it to the packaged resource. The app does not download assets at runtime.

The current catalog contains four photographic 2D backgrounds, six 3D environment props and one animated Fox sample. The Fox is a test character, not a complete human 3D avatar. The separate 42-piece Kotlin-era avatar generator is not yet connected to the Godot gallery as a rigged 2D character.

## MediaPipe boundary

The current main branch does not contain `scripts/MocapReceiver.gd`, a native MediaPipe Android plugin, or a working camera/video-to-Skeleton3D capture path. Therefore no functional MediaPipe capture option is available in this Godot build yet. The legacy Kotlin implementation under `app/` is retained for reference and is not part of the primary Godot runtime.

## Legacy Android implementation

The previous Kotlin implementation remains in app/ for reference during migration. The former Android CI is retained as a manually dispatchable legacy workflow.
