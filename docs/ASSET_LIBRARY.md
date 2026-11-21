# JEDL Studio — offline asset library intake

## Scope of this pipeline

This pipeline expands the downloadable content library without placing every source archive inside the Android APK. GitHub Actions downloads source archives, checks their published license evidence, validates ZIP integrity and paths, computes SHA-256 digests, and publishes a versioned artifact.

The Android `ContentLibrary` reads verified PNG manifests from APK assets and from installed packages in app-private storage. The ZIP installer validates the root manifest, CC0 permissions, safe paths, file inventory, sizes and SHA-256 values before atomically activating a package. The installable ZIP contains only the community CC0 collection and the original instrument/clothing PNG banks that the Android catalog can load; raw source archives are excluded. GLB/FBX files remain staged because the current editor does not render them.

## Initial source batches

### Existing banks already built by the main workflow

- Kenney modular character source bank
- Kenney Tiny Town objects
- Kenney Foliage objects
- Original CC0 instrument illustrations (11 PNGs)
- Original CC0 clothing illustrations (6 PNGs)

These existing banks must not be downloaded a second time under a duplicate ID.

### Additional Kenney CC0 packs

The intake catalog currently checks these official asset pages at build time:

- Animal Pack
- Animal Pack Remastered
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
- The Android installer unpacks verified packages into app-private local storage. Community CC0 packs and PNG banks under `banks/` are discovered by the offline catalog.
- The compact package root manifest lists every payload file with byte size and SHA-256, and inventories each installable PNG bank separately.
- 2D PNG packs can be connected to the current content library after their manifests are normalized.
- GLB/FBX packs remain staged until the corresponding 3D renderer/importer is implemented and tested.

## Status vocabulary

- `downloaded-and-verified`: archive fetched and its integrity/license evidence validated.
- `staged-offline-pack`: available as a CI artifact, not yet installed in the Android app.
- `integrated-in-editor`: only after the app imports it, lists it, loads it, and passes runtime tests on the target device.

A successful APK build alone does not promote a staged pack to editor-integrated status.


## Bundled offline library and MediaPipe

The Android build now bundles the generated library bundle at
`assets/offline_library/jedl-library-bundle.zip`. This is a one-time offline
payload; the app installer must unpack selected packs into app-private storage.
The build also bundles the verified Pose Landmarker Lite model at
`assets/models/pose_landmarker_lite.task` and includes the MediaPipe Tasks
Vision Android runtime. Full and Heavy models remain separate CI artifacts to
avoid adding unnecessary weight to the Redmi-targeted APK.

Community intake records each pack's original source URL, the CC0 statement
from its upstream SOURCE.md, and whether a separate license file exists.
Packs with a non-neutral theme are excluded from the bundled library. A missing
standalone license file remains a review flag, not a claim that the original
license text was preserved.


## Scene props and motion capture

The built-in library has separate **Instrumentos** and **Vestuario** filters. The original CC0 instrument and clothing banks are copied into the installable ZIP under `banks/`, so the same manifests and PNG hashes are available after local installation.

MediaPipe Pose Landmarker Lite runs in VIDEO mode. The capture action samples a selected video at 500 ms intervals for up to 12 seconds, converts visible shoulder, elbow, wrist, hip, knee and ankle landmarks into `PoseHierarchy` angles, and creates editable `StudioKeyframe` entries. Frames below the landmark-confidence threshold are rejected rather than filled with guessed poses.

Scene objects persist their bank ID, package version and asset SHA-256. On reopen, the catalog resolves only the matching revision; a missing or changed resource is shown as unavailable instead of silently substituting another image.
