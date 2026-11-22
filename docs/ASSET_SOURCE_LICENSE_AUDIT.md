# JEDL Studio — Asset source and redistribution audit

Audit date: 2026-11-22

This register is a source-selection policy, not a declaration that every file from a provider is approved. Each imported file must retain its own source URL, author/creator when supplied, exact license identifier, license evidence URL, retrieval date, SHA-256, format, dimensions/polycount, and package ID.

## Import policy

A resource is eligible for inclusion in JEDL Studio's redistributable offline library only when the exact file's terms permit:
1. commercial use;
2. redistribution of the original file inside a distributed application/library;
3. modification/conversion when the pipeline needs it;
4. inclusion in offline packages without a runtime call to the provider.

Reject or quarantine assets with non-commercial, editorial-only, no-derivatives, standalone-redistribution bans, unclear rights, third-party rights flags, or missing per-file evidence. Do not infer rights from a provider's general marketing page when the individual asset has a different notice.

## Sources cleared at provider-license level

| Provider | Content useful to JEDL | Verified terms | Decision |
|---|---|---|---|
| Poly Haven | HDRIs, PBR textures, scanned 3D models | CC0; provider explicitly permits commercial use and redistribution, including in a product sold | APPROVED source; still validate every download, file integrity and technical suitability |
| ambientCG | PBR materials, textures, models and preview renders | CC0 1.0; provider explicitly permits copying, modification, commercial distribution and including raw files in projects | APPROVED source; validate each file and mobile suitability |
| Smithsonian Open Access | 3D collection objects and image media | Only items marked CC0 qualify. Smithsonian states CC0 content can be used commercially; API documentation says media files are provided for public-domain objects, while records with other restrictions may have no media | APPROVED per-item only; require CC0/rights metadata and screen third-party, publicity and privacy flags |
| Godot demo projects | Example project assets, textures, meshes and UI references | Official demo repository states MIT for the demo projects | APPROVED per repository/file; retain MIT copyright and license notice, inspect any separately attributed third-party asset |
| Library of Congress Free to Use and Reuse | Historical photographs, architecture, landscapes, interiors and cultural imagery | Curated rights-free sets exist, but LoC warns rights must be checked at item level and it does not own all collection rights | CONDITIONAL per item; import only records explicitly marked public domain/no known restrictions and with no third-party or privacy restrictions |

## Conditional sources — do not bulk-import blindly

- Wikimedia Commons: rights and attribution differ per file. Only CC0/Public Domain Mark items should enter the no-attribution lane. CC BY/SA assets require a separate attribution and downstream-distribution compatibility review.
- NASA 3D Resources: many US-government works are public domain, but NASA's own guidelines warn that third-party material may appear and commercial use must not imply NASA endorsement. Require per-file rights checks.
- Godot Asset Library: it is a catalogue, not one blanket license. Each project has its own license; verify the repository's LICENSE file and every included third-party asset.

## Excluded from JEDL's redistributable asset catalogue under currently reviewed terms

- Quaternius assets under the current Quaternius Asset License (QAL): commercial use inside a finished product is allowed, but standalone asset redistribution/republishing is prohibited. That conflicts with JEDL's user-facing editable asset library.
- ShareTextures: its custom CC0 wording adds restrictions against redistribution as collections/plugins and against automated bulk downloading. Not eligible for JEDL's bundled catalogue without written permission.
- AutoSprite free library: CC0 permits shipping assets inside an app, but its terms prohibit redistributing them as a stock/asset pack. Since JEDL exposes editable source assets as a library, exclude unless a separate written grant explicitly covers this use.
- Sketchfab Standard/Editorial licensed content: the reviewed terms prohibit making the asset available as a standalone file. Editorial content also has commercial-use restrictions. Do not import into JEDL's editable library. A separately downloadable Creative Commons item would need a fresh per-file review and API terms review.

## Required metadata for every imported file

- asset_id (stable, namespaced)
- title, description, category, tags
- kind (background_2d, cutout_2d, prop_3d, character_3d, material, texture)
- format, dimensions, alpha/transparency, resolution, polycount, rigged flag and animation clip names where applicable
- source_provider, source_url, creator
- license_id, license_url, commercial_use=true, redistribution=true, modification_allowed
- attribution text and share-alike obligations when applicable
- retrieved_at, sha256, file_size_bytes
- preview_path, resource_path, package_id, offline=true

## Packaging policy

Do not put hundreds of large files into every small APK update by default. Keep the catalogue and previews lightweight, and distribute complete thematic asset packs as versioned offline packages that can be installed once and used without network access. The APK must still contain a useful starter pack. Every package needs its own manifest, license notices, checksums and compatibility metadata.

## Primary evidence

- Poly Haven license: https://polyhaven.com/license
- ambientCG license: https://docs.ambientcg.com/license/
- Smithsonian Open Access terms: https://www.si.edu/termsofuse
- Smithsonian Open Access developer tools/API: https://www.si.edu/openaccess/devtools
- Godot demo projects repository: https://github.com/godotengine/godot-demo-projects
- Godot Asset Library licensing overview: https://docs.godotengine.org/en/stable/community/asset_library/what_is_assetlib.html
- Library of Congress Free to Use and Reuse: https://www.loc.gov/free-to-use/
- Library of Congress rights guidance: https://www.loc.gov/legal/
- Wikimedia Commons reuse guidance: https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia/en
- NASA media usage guidance: https://www.nasa.gov/nasa-brand-center/images-and-media/
- Quaternius current license: https://quaternius.com/license.html
- ShareTextures license and terms: https://www.sharetextures.com/p/license and https://www.sharetextures.com/p/terms
- AutoSprite free asset license: https://www.autosprite.io/free/license
- Sketchfab license agreement: https://sketchfab.com/licenses

This is a technical rights-screening register, not a legal opinion. Re-check provider terms and per-file evidence at each acquisition/release.
