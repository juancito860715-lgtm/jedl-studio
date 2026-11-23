# JEDL Studio

JEDL Studio is a local-first Android production workspace built on Godot 4.4.1 and the GL Compatibility renderer.

## Godot project

- `Main.tscn`: 3D stage, camera, lighting and runtime UI.
- `scripts/CatalogManager.gd`: validates the checked-in offline catalog and manifest.
- `scripts/SceneParser.gd`: validates scene JSON, resolves local asset IDs, places Sprite2D resources on an independent 2D canvas and 3D resources on the stage, and schedules subtitle/audio events.
- `scripts/TimelineEngine.gd`: one keyframe engine for JSON actions and manually created keys on Node2D and Node3D targets.
- `scripts/ProjectStore.gd`: versioned JSON project persistence, backup restore and duplication under `user://projects`.
- `assets/gallery/catalog.json` and `manifest.json`: checked-in starter catalog and integrity inventory.
- `.github/workflows/build_godot.yml`: Godot 4.4.1 headless validation and Android debug APK export.

## Offline starter content

The starter catalog contains original CC0-1.0 transparent PNG sprites and an original primitive 3D character scene. These resources are included in the repository; the app does not download gallery resources at runtime or during the Hito 1 validation job.

Every future catalog addition must include stable asset identity, exact license evidence, a local license notice where applicable, SHA-256 and offline dependencies.

## Scene JSON

See `scenes/scene.example.json`. Root fields include `characters`, `objects`, `elements`, `subtitles`, `sounds` and `actions`. An action has `target`, `property`, `time`, `duration` and `to`. Supported transform properties are `position`, `rotation_degrees` and `scale`.

## Current scope

Hito 1 covers the offline starter catalog, independent 2D/3D galleries, JSON actions and a shared editable keyframe timeline, plus versioned local project persistence. Touch manipulation, character rig editing, global styles, audio mixing/MP4 export and MediaPipe retargeting remain later milestones and are not claimed as implemented.
