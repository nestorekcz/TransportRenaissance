# Source and extension audit

Inspected baseline: OpenTTD 15.3 / `14ec60f248547d4d062a1160f0fc26d742319888`. Paths below are actual checked-out implementation references, not assumptions about a modern 3D engine.

| System | Verified implementation | Consequence for this fork |
|---|---|---|
| Projection and draw ordering | `src/viewport.cpp`: `ViewportAddLandscape`, `ViewportSortParentSprites`, `ViewportDoDraw`, `DrawGroundSpriteAt` | Preserve the tile projection, sprite origins, parent/child bounds, and sorting. Ground art is replaced without changing geometry. |
| Blitters and colour | `src/blitter/32bpp_anim.cpp`: `PaletteAnimate`; `32bpp_base.cpp`, `8bpp_base.cpp`; `src/palette.cpp` | 32-bit RGBA is distinct from higher resolution. Palette animation and indexed fallback remain supported. No new shader or material system is introduced. |
| Sprite storage and zoom | `src/spriteloader/grf.cpp`: `LoadSpriteV1`, `LoadSpriteV2`, `SpriteLoaderGrf::LoadSprite`; `src/spritecache.cpp`; `src/zoom_type.h` | GRF v2 supports separate zoom and colour-depth alternatives. Supply 1×, 2×, 4× texture sprites and a normal indexed fallback; farther zooms use the existing resampling path. |
| Viewport updates | `src/viewport.cpp`, `src/gfx.cpp`, `src/video/video_driver.cpp` | Dirty-region updates and draw timing remain upstream. Vehicle interpolation would require render positions, dirty bounds, sorting, selection and camera invariants to agree; it is not included. |
| Simulation and time | `src/openttd.cpp`: `StateGameLoop`, `GameLoop`; `src/timer/timer_game_tick.h`; `src/video/video_driver.cpp` | Preserve authoritative ticks and commands. The measured target on this baseline is about 37.04 game loops/s, not an assumed 60 Hz simulation. |
| Effects and animation | `src/effectvehicle.cpp`: `SteamSmokeTick`; `src/animated_tile.cpp`: `AnimateAnimatedTiles`; `src/palette.cpp`: `DoPaletteAnimations` | Existing effects are game objects. Replace only their sprites; do not alter spawning, RNG, tick timing or pools. New water interpolation samples the local palette only. |
| Windows and scaling | `src/widget.cpp`, `src/window.cpp`, `src/widgets/station_widget.h`, `src/station_gui.cpp`, `src/settings_gui.cpp`, `src/fontcache.h` | Existing nested widgets calculate size from text and font metrics. Add one filter to the existing station list, preserving sorting, cargo/facility filters and information density. |
| Localization | `src/lang/english.txt`, `src/strgen`, `src/strings.cpp` | Add master English strings; other languages use the normal fallback until translated. No text baked into artwork. |
| Base sets and NewGRF | `src/gfxinit.cpp`, `src/newgrf.cpp`, `src/newgrf_config.cpp`, `docs/obg_format.txt` | OpenGFX remains the base set. A static NewGRF replaces a bounded sprite set and is absent from savegame content requirements. Other replacement packs can override the same sprites; mixed stacks require separate review. |
| Vehicles and structures | `src/vehicle.cpp`, `src/train_cmd.cpp`, `src/station_cmd.cpp`, `src/town_cmd.cpp:DrawTile_Town`, `src/industry_cmd.cpp:DrawTile_Industry`; `src/newgrf_*` | Directional vehicle sprites, station layouts, building stages and industry callbacks already exist. Use NewGRF for future structures/vehicles where possible; no new vehicle logic in this slice. |
| Serialization | `src/saveload/saveload.cpp`: `SAVEGAME_VERSION`, `DoSave`, `DoLoad`; `src/saveload/saveload.h`; `docs/savegame_format.md` | Baseline save version 362 is unchanged. Smooth-water setting is `NotInSave` and `NoNetworkSync`; attention filtering lives in window state. No migration required. |
| Multiplayer | `src/network/network.cpp:NetworkGameLoop`; `src/network/network_client.cpp:GameLoop`; `src/network/network_server.cpp` revision checks; `src/network/core/network_game_info.cpp` | Authoritative commands and RNG sync checks remain intact. Matching fork revisions are the supported boundary. Preserve revision mismatch rejection; do not masquerade as upstream 15.3. |
| Diagnostics and verification | `src/tests`, `regression`, `CTest`, `src/framerate_type.h`, console `fps`, `gamelog`, `screenshot`, `schedule`; `.github/workflows` | Use real native builds, upstream tests, two focused helper tests, in-game images and profiler output. A null driver benchmark measures simulation-loop workload, not renderer performance. |

## Implemented scope and alternatives

| Improvement | Class | Decision |
|---|---|---|
| Temperate meadow, regrowth, rough/rock ground, grass substrate beside rail/road, soft steam | B: supported static NewGRF, derived asset work A | Implemented. Preserves offsets, transparent footprints, structural pixels and simulation. |
| Smooth water colour transitions | C: focused palette/UI change | Implemented behind a local setting. Adjacent colours interpolate on the existing animation schedule; no new game state or day/night simulation. |
| Station service attention filter | C: existing station UI | Implemented. Waiting available cargo + displayed rating below 50%, restricted to selected cargoes. Existing station ratings are reused rather than invented occupancy estimates. |
| Fleet profitability/search replacement | C | Deferred: vehicle lists already expose grouping, sorting, filters, profit and orders. A replacement would duplicate mature functionality without a precise player problem. |
| Stations, buildings, trees, vehicle sets | B | Next art production. Need matching directional/layout coverage, bounding boxes and authoring budgets. |
| Water geometry, animated industrial activity | A/B | Further sprite work can reuse palette indices and supported animation callbacks. Not included beyond the colour interpolation. |
| Vehicle render interpolation | D | Separate prototype required; must test occlusion, selection and dirty regions against authoritative positions at all zooms. |
| Weather/day-night, dynamic lights, rotation, skeletal animation/PBR | D | Not promised. The existing sprite renderer does not establish these capabilities. Cosmetic prototypes must not affect simulation. Rotation would also require extensive art and projection work. |

## Changes and maintainability

`renaissance_gui.h` holds pure presentation predicates/sampling helpers with targeted edge and wrap tests. The station-list changes reuse the existing rebuild/resort and invalidation paths. Cargo-choice counts are computed before the attention predicate so temporarily empty filtered results do not disable cargo choices. The palette counter is unsigned to make wrapping defined. Both original and new water paths remain available.

No authoritative simulation, command format, save descriptor, NewGRF feature definition or network packet has been changed. There is no new service, database, web frontend, telemetry or account system. Keep future presentation work in supported content packages; isolate any simulation additions into separate compatibility milestones.
