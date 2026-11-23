# JEDL Studio scene JSON v2

The JSON is the scene interchange contract. The app validates resource IDs and paths against the packaged offline catalog before loading.

## Root fields

- `version`: currently 2; version 1 scenes remain supported.
- `title`: human-readable scene title.
- `background`: optional full-frame 2D background object with `assetId` (preferred), or a packaged `path`; it is never inserted automatically.
- `characters`: rigged character instances; `id`, `path`, `position`, `rotation_degrees`, `scale`, optional `animation`, `animation_loop`, `depth`, `layer`.
- `objects`: 3D props and environment objects with the same transform fields.
- `elements`: optional 2D/3D individual composition elements.
- `subtitles`: timed text entries with `time`, `duration`, `text`.
- `sounds`: timed audio entries with `time`, `path`.

## Composition rules

1. New compositions start empty. A background is added only when the user selects one or the JSON explicitly declares it.
2. A selected full-frame background is attached to the active camera, follows camera movement and renders behind ordinary scene objects.
3. Characters, objects and elements are independent scene instances. Their 3D depth is controlled by their world transform; `depth` overrides the Z component of `position`.
4. `layer` is a semantic grouping label for the editor and diagnostics. It does not bypass 3D depth testing.
5. Transparent 2D cutouts are independent foreground elements; they are not treated as full-frame backgrounds.
6. Resource paths must refer to packaged `res://` assets. The app does not fetch scene resources from external URLs at runtime.

## Example

See `scenes/scene.example.json`. It remains a character-only demonstration; no background is preselected.

## Validation status

The parser accepts version 1 and version 2 roots. The `elements` collection is optional. Entries may reference a 3D PackedScene/glTF model or a transparent 2D PNG/WebP cutout. Full-frame photographic backgrounds are optional JPEG catalog assets referenced through the separate `background` field. The curated transparent cutout bank and dedicated 2D placement controls remain subsequent work.
