# Kenney Modular Character Pack -> JEDL

## Source and rights

- Source listing: https://opengameart.org/content/modular-character-pack
- Publisher: Kenney
- License shown by the source listing: CC0
- License terms: https://creativecommons.org/publicdomain/zero/1.0/
- Commercial use and modification: permitted by CC0
- Attribution: optional; courtesy credit Kenney.nl is welcome

The original archive is not committed to this repository. Keep the original ZIP, source listing and license evidence with the release records.

## Why import is explicit

The source page describes hundreds of separate PNG sprites, six spritesheets and six vector files. Those files are not automatically rigged. The importer intentionally refuses to guess which image is a head, hand, sleeve, etc.

A reviewed mapping file must identify each source PNG and provide:
- stable JEDL part ID;
- one CharacterLayerSlot;
- the canonical bone for that slot;
- normalized pivot coordinates;
- design-space width and height;
- Z index;
- one default part for every default slot required by the master character.

Use the schema exercised by test_import_kenney_pack.py. The mapping must use rigId: jedl_humanoid_v1 and the complete ten-bone list. If a source part cannot be mapped cleanly, do not force it into the rig; leave it out or design a separately tested adapter.

## Import

After obtaining the original ZIP from the source listing and completing the reviewed mapping:

```bash
python tools/avatar_bank/import_kenney_pack.py \
  --zip /path/to/Kenney_characterPack_1.zip \
  --mapping tools/avatar_bank/external_packs/kenney_modular_character_pack.mapping.json \
  --out app/src/main/assets/styles/kenney_modular_character_pack
```

The importer validates CC0-1.0 evidence, rejects unsafe archive paths and symbolic links, checks slot-to-bone mappings and pivots, copies only explicitly mapped PNGs, and emits a JEDL manifest plus SOURCE.json and LICENSE.txt.

## Editor and rig gate

The Android loader accepts different art part IDs and counts, but requires the same jedl_humanoid_v1 bones and the same default slot contract as the master pack. Style switching filters obsolete selected-part IDs while preserving the project pose and animation.

A pack is not considered integrated until importer tests, manifest and license registry tests, Android unit tests, APK asset-presence checks, and manual editor verification on a physical device all pass. Manual verification must cover alternate piece selection, style switching, all ten bone rotations, pivots, Z order, and save/reopen.

Current status: importer and shared-rig contract implemented; actual Kenney ZIP segmentation/mapping and physical-device editor validation remain pending. The source archive could not be retrieved in this development session, so no Kenney art is falsely represented as bundled.