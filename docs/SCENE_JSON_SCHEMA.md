# JEDL Studio scene JSON v2

The JSON is the scene interchange contract. External assistants may author it, but the app validates resource IDs and paths against the packaged offline catalog before loading.

## Root fields

- `version`: currently 2; version 1 scenes remain supported.
- `title`: human-readable scene title.
- `characters`: character instances with stable `id`, `assetId`, transforms and optional animation.
- `objects`: 3D props and environment objects.
- `elements`: optional individual 2D/3D composition elements.
- `subtitles`: timed text entries with `time`, `duration`, `text`.
- `sounds`: timed audio entries with `time`, `path`.
- `actions`: timed transform actions. Each action uses `target`, `property`, `time`, `duration` and `to`; optional `from` defines an explicit starting transform.

## Composition rules

1. 2D PNG/WebP cutouts remain independent catalog assets and are rendered as alpha-transparent Sprite3D elements in the stage.
2. 3D models are local PackedScene resources with a Node3D root.
3. Every element has a stable entry `id`; actions target that ID.
4. JSON actions and manually authored keyframes are compiled into the same TimelineEngine.
5. Missing assets are not replaced silently. The UI offers an explicit same-category alternative or cancellation.
6. Resource paths must refer to packaged `res://` assets. No runtime network fetch is supported.

See `scenes/scene.example.json` for a complete offline sample.
