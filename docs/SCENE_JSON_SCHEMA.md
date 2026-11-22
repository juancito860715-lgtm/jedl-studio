# JEDL Studio scene JSON v2

The JSON is the scene interchange contract. External assistants may author it, but the app validates resource IDs and paths against the packaged offline catalog before loading.

## Root fields

- `version`: currently 2; version 1 scenes remain supported.
- `title`: human-readable scene title.
- `background`: optional full-frame 2D background object: `id`, `path`, `fit`.
- `characters`: rigged character instances; `id`, `path`, `position`, `rotation_degrees`, `scale`, optional `animation`, `animation_loop`, `depth`, `layer`.
- `objects`: 3D props and environment objects with the same transform fields.
- `elements`: optional 2D/3D individual composition elements, separate from the full background.
- `subtitles`: timed text entries with `time`, `duration`, `text`.
- `sounds`: timed audio entries with `time`, `path`.

## Composition rules

1. The full background is attached to the active camera at a fixed far-plane distance. It follows camera movement and is rendered behind scene objects.
2. Characters, objects and elements are independent scene instances. Their 3D depth is controlled by their world transform; `depth` overrides the Z component of `position`.
3. `layer` is a semantic grouping label for the editor and diagnostics. It does not bypass 3D depth testing.
4. A foreground cutout or prop must be an individual catalog asset, never baked into the full background.
5. Resource paths must refer to packaged `res://` assets. The app does not fetch scene resources from external URLs at runtime.

## Example

See `scenes/scene.example.json`. It places the animated Fox in front of the Mossy Forest photographic background.

## Validation status

The parser accepts version 1 and version 2 roots. The `elements` collection is optional. Entries may reference a 3D PackedScene/glTF model or a transparent 2D PNG/JPEG/WebP cutout. 2D cutouts are rendered as camera-facing Sprite3D elements with alpha transparency; full-frame photographs belong only in `background`. The current curated catalog still needs its first transparent cutout bank, and the dedicated placement/editor controls remain subsequent work.
