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


## Additional sources identified in expanded search

| Source | Reported scale / content | License and redistribution screen | JEDL decision |
|---|---|---|---|
| CodeLove 3D Models | Site reports 6,792 GLB models, 91 collections, 275 rigged characters/animals and 20 animation clips | Each file/ZIP reportedly carries MIT, CC0, public-domain or CC BY terms; preserve MIT notices and CC BY attribution | CANDIDATE; per-model license gate |
| Grab3D | Site reports 2,565 3D models and 75 kits | Validate exact 3D pack, formats, source provenance and original license | CANDIDATE; validate per pack |
| OmniMod 3D Library | Repository reports 5,952 OBJ models, including nature, buildings, props, vehicles, furniture and characters | Repository claims CC0; validate repository license and original Kenney/Kay Lousberg provenance | CANDIDATE; useful mostly for low-poly/static scene props |
| Tevy Assets | Specific Casual Walker GLB | Model page states CC0; 56-bone rig and four looping clips | CANDIDATE; one model, not a character library |
| Innerscene 3D Parts | Specific rigged human base meshes | Individual pages state CC0 and redistribution; inspect source derivation and mesh suitability | CANDIDATE; base meshes for character editor, not finished wardrobe |
| Art Institute of Chicago API | API reports 187,487 image records; public-domain artworks can be filtered | Only public-domain artworks/images qualify; API also contains copyrighted content | APPROVED per public-domain item only |
| Rijksmuseum | Large high-resolution digitized collection | Most collection images are PD/CC0; some CC BY and restricted items exist | APPROVED PD/CC0 only in default lane; CC BY requires attribution |
| StockSnap | High-resolution photography across nature, architecture, travel and backgrounds | Provider states all photos are CC0; still check people, trademarks, property and per-image provenance | CANDIDATE per image |
| British Library Flickr Commons | More than one million digitized images | Only images explicitly marked public domain; British Library's CC-licensed content is limited to non-commercial use under its terms | APPROVED public-domain-marked files only |
| Free Game Dev Assets index | Searchable catalog of 3D sources | Index is discovery metadata, not a license grant | DISCOVERY ONLY; verify original publisher |
| Pexels | Large photo/video catalog | Current terms prohibit standalone redistribution and bulk/systematic collection for stock-library use | EXCLUDED from JEDL's bundled editable catalog |
| Unsplash | Large photography catalog | Commercial use allowed, but terms prohibit compiling images to create a similar/competing service | EXCLUDED from JEDL's bundled editable catalog |

The provider counts above are claims displayed by the respective sources at research time, not counts already downloaded, rights-cleared or integrated into JEDL Studio. Counts must never be treated as imported inventory.

## Required metadata for every imported file

- asset_id (stable, namespaced)
- title, description, category, tags
- kind (photographic_background, prop_3d, character_3d, material, texture). Individual 2D cutouts, sprites and illustrations are excluded; photographic backgrounds remain JPEG backplates.
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
- CodeLove 3D Models: https://models.codelove.in/
- Grab3D: https://grab3d.com/
- OmniMod 3D Library: https://github.com/Mcamento8/omnimod-3d-library
- Tevy Casual Walker: https://tevy.dev/models/casual-walker
- Innerscene 3D Parts: https://www.innerscene.com/tools/library/3d-parts/
- Art Institute of Chicago API: https://api.artic.edu/docs/
- Rijksmuseum data policy: https://data.rijksmuseum.nl/policy/
- StockSnap CC0 statement: https://stocksnap.io/free-stock-photos
- British Library Flickr Commons: https://commons.flickr.org/members/britishlibrary/
- British Library terms: https://www.bl.uk/terms
- Pexels terms: https://www.pexels.com/terms-of-service/
- Unsplash license: https://unsplash.com/license

This is a technical rights-screening register, not a legal opinion. Re-check provider terms and per-file evidence at each acquisition/release.
