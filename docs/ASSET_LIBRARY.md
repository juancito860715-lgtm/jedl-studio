# JEDL Studio — offline asset library intake

## Scope of this pipeline

This pipeline expands the downloadable content library without placing every source archive inside the Android APK. GitHub Actions downloads source archives, checks their published license evidence, validates ZIP integrity and paths, computes SHA-256 digests, and publishes a versioned artifact.

The current Android `ContentLibrary` reads PNG manifests from APK assets. It does not yet import arbitrary external ZIPs or render GLB/FBX models. Therefore this phase publishes offline-ready archives separately; it must not be described as full in-editor integration.

## Initial source batches

### Existing banks already built by the main workflow

- Kenney modular character source bank
- Kenney Tiny Town objects
- Kenney Foliage objects

These existing banks must not be downloaded a second time under a duplicate ID.

### Additional Kenney CC0 packs

The intake catalog currently checks these official asset pages at build time:

- Animal Pack
- Animal Pack Remastered
- Fish Pack
- Furniture Kit
- Mini Characters
- City Kit Suburban
- Nature Kit
- Food Kit
- Toy Car Kit
- Building Kit
- Music Jingles
- Interface Sounds

Each pack is accepted only when its official page explicitly identifies CC0 and the linked download is an HTTPS ZIP that passes path, symlink, CRC, file-count and expanded-size checks. The generated manifest records the final download URL, source page, license evidence, archive SHA-256, file formats and file inventory.

### Community 2D source

GitHub Actions checks out only the `modern-urban` and `nature` directories from `Tiddybub/2d-assets`. Each included pack must contain its own `SOURCE.md` with explicit CC0 evidence. Original source notes are preserved in the resulting ZIP.

## Licensing rules

- No assumption that "free" means redistributable.
- No asset is accepted without explicit license evidence.
- The exact license and source are preserved beside every archive.
- CC0 packs may be modified and redistributed; other licenses require separate review and any required notices.
- If a page no longer confirms the license or the download changes to an unexpected format, the CI job fails closed.

## Device and packaging policy

- Keep the APK lean; source packs are uploaded as a separate GitHub Actions artifact.
- Do not load the full catalog into RAM.
- The future Android installer must unpack only selected packs into app-private local storage, verify their manifests and hashes, and expose them offline.
- 2D PNG packs can be connected to the current content library after their manifests are normalized.
- GLB/FBX packs remain staged until the corresponding 3D renderer/importer is implemented and tested.

## Status vocabulary

- `downloaded-and-verified`: archive fetched and its integrity/license evidence validated.
- `staged-offline-pack`: available as a CI artifact, not yet installed in the Android app.
- `integrated-in-editor`: only after the app imports it, lists it, loads it, and passes runtime tests on the target device.

A successful APK build alone does not promote a staged pack to editor-integrated status.
