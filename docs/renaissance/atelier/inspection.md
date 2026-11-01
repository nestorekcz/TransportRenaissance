# Repository and runtime inspection

Classification: **B — an OpenTTD-compatible sprite game**, with existing targeted presentation changes. This is the OpenTTD 15.3-derived Transport Renaissance repository, not an arbitrary-mesh 3D engine. The art demo executable is built from project commit `f1fa0af276` plus three offline authoring/capture console helpers. The main worktree has concurrent regional-economy work; it was deliberately excluded from this art build. The full frozen source is retained at `artifacts/atelier-engine-source` in the workspace.

| Subject | Evidence in repository | Production consequence |
|---|---|---|
| Rendering / platform | `src/blitter`, `src/video/win32_v.cpp`, `src/spriteloader/grf.cpp`, `src/spritecache.cpp` | Windows native software blitter for measured demo; GRF v2 sprite data. Other upstream video backends/platforms exist but were not tested here. |
| Camera | `src/viewport.cpp`, `src/zoom_type.h` | Fixed 2:1 isometric; 64 × 31 base tile raster. Zoom 0/1/2 = 4×/2×/normal; 3–5 are zoom-out. No rotation. |
| Scale/elevation | `src/tile_type.h`, `src/slope_type.h`, drawing tables | 16-unit tile, 8-unit height step. Sprite dimensions can exceed a tile; existing footprints and sorting remain authoritative. |
| Loading / IDs | `src/gfxinit.cpp`, `src/newgrf.cpp`, OpenGFX PNML | OpenGFX remains the base set. Static GRF replaces bounded base slots; all other content survives. No migration mapping is required because IDs are preserved. |
| Existing project art | `tools/renaissance/build_assets.py`, `media/renaissance/source`, `artifacts/assets/asset-build.json` | Earlier Meadow package replaces 168 slots. Before views include Meadow; Atelier is layered after it. Manifest records both. |
| Buildings | `src/table/town_land.h`, `src/town_cmd.cpp` | Four construction stages and tile-hash variations; stable house IDs, bounding boxes and population behavior preserved. Shared sprites can represent more than one stage. |
| Vehicles | `src/table/engines.h`, `train_sprites.h`, `roadveh_cmd.cpp`, `ship_cmd.cpp` | 256 default roster entries. Directions, company remap, wagon load additions and articulated callbacks are engine-specific. Demo preserves the exact selected vehicle IDs. |
| Routes / structures | `rail_cmd.cpp`, `road_cmd.cpp`, `station_cmd.cpp`, `tunnelbridge_cmd.cpp` | Existing construction, slopes, junctions, bridges, depots, signals, tunnels and station logic. Demo supplies selected art, not new network rules. |
| Climate/era/economy | engine and industry tables, `landscape_type.h`, `newgrf_industries.cpp` | Temperate, sub-arctic, subtropical and toyland rosters; date availability and existing cargo chains. Demo shows coal mine → power works, passenger rail/bus and a demonstration delivery truck/ferry. |
| Materials/shadows | blitters and palettes | RGBA, indexed fallback, remapping and palette animation; baked model shading. No runtime meshes, PBR lights, freeform shadows or instancing API. Sprite cache and sorting do the runtime work. |
| Save/network | `src/saveload`, network revision handling | Art build retains save version 362 and functional IDs. Helpers reject network mode. Broader concurrent regional changes are outside this executable and compatibility claim. |
| Tools | local Python/Pillow/NML, clang/MinGW/CMake/Ninja, official portable Blender | Genuine editable Blender geometry, deterministic renders, PNG masks, NML/GRF exports. No copied proprietary models or generated concepts presented as models. |

The existing desktop game windows were inventoried. The computer-use adapter then denied access to `openttd`, so hands-on UI inspection and desktop video capture were unavailable. Native executable launches, console screenshots, profiler logs and GameScript traffic observations provided direct runtime evidence. This does not establish mouse-selection, construction-overlay or live multiplayer validation; those remain explicit manual checks.

Blender 4.5.15 LTS was obtained from the official [release directory](https://download.blender.org/release/Blender4.5/) and its published SHA-256 verified. The sprite format follows the official [NML real-sprite specification](https://newgrf-specs.tt-wiki.net/wiki/NML:Realsprites) and [alternative-sprite specification](https://newgrf-specs.tt-wiki.net/wiki/NML:Alternative_sprites).

## Inventory interpretation

The inventory expands every PNG rectangle in all six pinned OpenGFX sets, rather than counting contact-sheet thumbnails. There are **10,806 raster slots: 8,492 world slots and 2,314 retained interface/font/face/logo slots**. One view, load stage or animation frame is a slot, not a whole model. 256 engine records are a separate roster count and must not be added to the sprite count.

The 322-slot approval package covers about 3.79% of world slots. 8,170 world slots have no Atelier replacement. Existing graphics remain visible for them. This includes most industries, other bridges, depots, tunnels, fences, signals, aircraft, other vehicles, all other climates and numerous infrastructure slope/transition variants. The red river bridge is inherited; the pale concrete rail overpass is the new bridge sample.

Stable manifest keys are `opengfx:<set>:<compiled-slot>`, pinned to OpenGFX revision `e68bd9b7cb60305aa98c687b6836e0e0b08e2847`. Each row stores source path/hash, PNML references, pixel rectangle and offsets, replacement, integration and validation. Direction/state relationships remain in the cited PNML and engine drawing tables; unresolved world footprint semantics are explicitly identified rather than guessed. Base-slot IDs are valid ActionA replacement IDs. Extra-set compiled slot IDs are inventory keys only, not usable ActionA IDs.

The installed NML 0.7.5 predates three Action5 feature names in this source checkout. Inventory-only preprocessing substitutes their block labels to expand their raster rectangles; exact names are retained in `inventory-only-feature-normalization.json`. These inventory NFOs are not runtime exports. The count describes the pinned source library, including source-only extras; release work must resolve each extra to the target engine's Action5 feature rather than claim all 10,806 are simultaneously loaded by one climate.

No full-library generation has been authorized. The numbered expansion catalog is a proposal and every entry remains unapproved.
