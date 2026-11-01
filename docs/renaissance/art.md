# Art direction and production specification

Target: an elegant miniature transport world, warm natural colours, crisp isometric forms, convincing materials, restrained motion and readable networks. This checkpoint establishes the ground material and effect pipeline. It does not establish finished art for the entire world.

## Rules

- Keep OpenTTD's original 2:1 ground projection and world geometry. A normal ground tile is 64 pixels wide; slope height and sprite origins come from the exact inherited layout. Never change tile dimensions to accommodate painting.
- Grass uses muted olive/sage values and low local contrast. Track, roads, vehicles, signs and UI must remain stronger visual signals. Match rough ground and infrastructure substrates to the same palette. Preserve cool water and warm built materials as readable accents.
- Future elevated forms use consistent upper-left illumination. Flat source textures use diffuse lighting, with slope shading applied in the compiler. No baked horizon or directional cast shadow in the meadow texture.
- Provide independent 32-bit RGBA alternatives at normal, 2× and 4× sprite resolution. This is genuinely more texture samples at close zoom, not merely a colour-depth change. Inherited structures in infrastructure sprites are nearest-scaled and are explicitly **not** newly detailed 4× art.
- Preserve offsets/anchors and transparent footprints from OpenGFX. Terrain slope sprites retain their original varied heights and offsets. Multiply the complete rectangle and offset by the zoom scale. Keep parent/child sprite bounds and world sorting unchanged.
- PNGs use straight RGBA and exact zero alpha outside silhouettes. Terrain alpha footprints are replicated from licensed upstream masks; edge stair-stepping is inherited. Steam has soft alpha. The normal indexed fallback uses the DOS palette, reserves index 0 for transparency, and avoids animated and company-remap slots.
- No company-colour mask is added to terrain or steam. Existing vehicle company colours remain upstream. Future vehicle art must provide all required directions, remap masks, load states and lights consistently; one attractive direction is not accepted as coverage.
- Steam retains five engine frames, sizes 8/10/12/14/16 at normal zoom and original timing. Alpha decreases over the lifetime. Water interpolation keeps existing cycles and rates. Do not alter simulation or add effect objects to achieve smoother visuals.
- Other climates fall back to their base terrain; temperate replacements are conditional. Steam replacement is cosmetic in every climate. 8-bit rendering gets an indexed fallback with necessarily coarser transparency. Existing Full animation can freeze palette movement; smooth-water can be switched off separately.
- Source assets live under `media/renaissance/source`; generated `meadow-{scale}x.png`, `surfaces-{scale}x.png`, `steam-{scale}x.png`, fallback PNGs, NML and GRF live outside source. Deterministic names and manifests are required. Export with no embedded text, UI, watermark or unrelated scene details.

## Coverage inventory

The generated `asset-build.json` is the machine-readable, per-sprite inventory. Version 1 replaces **168 logical sprites**, with normal indexed fallback and three RGBA zoom alternatives each (672 encoded variants).

| Category | Sprite IDs | Coverage |
|---|---|---|
| Temperate grass and regrowth | 3924–3999 | 19 inherited slopes × 4 growth/ground stages, new projected meadow material |
| Rough terrain | 4000–4022 | 23 variants, matched material with inherited tuft/shape cues |
| Rocky terrain | 4023–4041 | 19 slopes, matched grass substrate; rocks inherited |
| Rail ground substrates | 1011–1036 | 26 variants; rail geometry/ballast/structural pixels inherited |
| Road ground substrates | 1332–1350 | 19 variants; road markings/pavement/structural pixels inherited |
| Steam | 3079–3083 | Five original procedural alpha frames, original engine timing |
| Water | Existing base sprites | Local smooth palette sampling; no new water/shore sprite set |
| Vehicles, buildings, stations, depots, trees, bridges, tunnels, industry art, icons/cursors | Inherited | Not upgraded in this slice; no placeholders represented as finished replacements |

Terrain beside every possible rail/road variant, crossings, station foundations, snow/desert, fences and custom NewGRF infrastructure is not covered. The flat coastal scene exercises the ordinary rail and road substrate. Expanded terrain and slope/bridge scenes are required before broader art approval.

## Provenance

| File/source | Author / origin | License and modifications |
|---|---|---|
| `meadow-source.png` | OpenAI built-in ImageGen, generated 2026-11-01 for this project | No reference artwork supplied. Exact prompt and origin recorded in `IMAGEGEN-PROMPT.txt`. Project distributes its interest in the source/output under GPL-2.0-only; no claim of exclusive copyright over generated material. Compiler performs projection, resampling and palette matching. |
| `opengfx-ground-mask.png` | OpenGFX 8.0 `grass-temperate.gimp.png`, Richard Wheeler (Zephyris) | GPL-2.0-only. Copied source; compiler uses transparency, shapes, growth and slope cues. |
| `opengfx-rough.png`, `opengfx-rocks.png`, `opengfx-infrastructure.png` | OpenGFX 8.0 contributors, per retained `authoroverview.csv` | GPL-2.0-only. Copied source; green substrate pixels replaced, other structure retained. Exact rectangles in `ground-surfaces.json`. |
| Steam atlas | Project's AI-assisted procedural Python code | GPL-2.0-only. No external smoke image. |
| Demo heightmap, GameScript and saved scene | Project-generated layout using OpenTTD/OpenGFX | GPL-2.0-only project contribution; inherited engine/content licenses retained. |

OpenGFX is pinned to `e68bd9b7cb60305aa98c687b6836e0e0b08e2847`. Full original notices and author inventory accompany the editable masks. Do not copy proprietary Transport Tycoon graphics into this pipeline.

## Review gates

Check normal/2×/4× and zoomed-out silhouettes, all 19 slopes, transparent edges, roads/rails, sorting behind structures, all directional vehicle overlays, day-independent colours and indexed fallback. Capture output from the actual game. Compare identical save/camera/UI settings. A concept texture or atlas preview is not evidence of an integrated game asset.

The first visual pass exposed overly light grass and dark inherited rough diamonds; the material was darkened and substrate coverage expanded before this checkpoint. Remaining limitations include repeated meadow pattern over broad empty areas, inherited pixel edges and structures, and incomplete steep-slope/custom-content visual QA.
