# Renaissance Atelier â€” approval checkpoint

**Latest: temperate world production pass.** The user approved finishing temperate first. Connected bridges, depots, cargo buildings and the surrounding world assets are integrated. Open the [new review](../../../../artifacts/atelier-temperate/review.html), [play the updated scene](../../../../artifacts/atelier-temperate/runtime/Launch-Atelier-Demo.cmd), or read [temperate-world.md](temperate-world.md). Earlier approval-gate statements below describe their historical checkpoints.

**Latest: Future Heritage fleet import.** All 256 supplied vehicle models and 88 empty variants are imported into editable libraries and a fleet-enabled demo. Open the [integration review](../../../../artifacts/atelier-future-heritage/review.html), [play the demo](../../../../artifacts/atelier-future-heritage/runtime/Launch-Atelier-Demo.cmd), or read [fleet-import.md](fleet-import.md). House and road artwork is preserved. Earlier checkpoints below remain historical records.

**Previous: road revision 2.** The user approved the house direction and requested better roads, clear train/vehicle model views and a railway proposal. Open the [revised visual review](../../../../artifacts/atelier-r2/review.html), [play revised demo](../../../../artifacts/atelier-r2/runtime/Launch-Atelier-Demo.cmd), or inspect the [editable models](../../../../artifacts/atelier-r2/source/atelier-library.blend). Details and remaining boundaries are in [road-revision.md](road-revision.md). Full production remains unapproved. The original checkpoint below is retained as the v1 record.

This is a playable **demo asset library** for the existing OpenTTD-compatible runtime. The direction is a quiet European miniature world: warm plaster and brick, varied roof silhouettes, matte materials, blue-green transport accents and soft baked light. Detailed geometry is rendered to the game's exact sprite views; no 3D renderer conversion is claimed.

**Full production is not approved and has not begun.** The scope is seven building designs, station/platform and bus-stop parts, six vehicle designs with a hopper load variant, three tree species, shrubs/street furniture, terrain/shore samples, roads/rail/junctions and a concrete bridge segment. There are 35 editable collections including component parts and load states, 87 source render views, and 322 integrated base sprite slots with 1,288 encoded colour/zoom alternatives.

## Open the work

- [Launch the isolated Windows demo](../../../../artifacts/atelier/runtime/Launch-Atelier-Demo.cmd). It opens paused; press the pause button or F1 to run traffic. It uses its own saves/settings and leaves other installed releases alone.
- [Visual review with before/after and close-ups](../../../../artifacts/atelier/review.html).
- [Normal gameplay view](../../../../artifacts/atelier/after-overview.png) and [equivalent before view](../../../../artifacts/atelier/before-overview.png).
- [Labeled model contact sheet](../../../../artifacts/atelier/contact-sheet.png). This is explicitly a source-render sheet, not an engine screenshot.
- [Editable Blender project](../../../../artifacts/atelier/source/atelier-library.blend).
- [Game-ready static GRF](../../../../artifacts/atelier/game/renaissance-atelier.grf), [NML source](../../../../artifacts/atelier/game/renaissance-atelier.nml), and [sprite coverage](../../../../artifacts/atelier/demo-coverage.json).
- [Full existing inventory](../../../../artifacts/atelier/inventory/asset-manifest.csv) and [vehicle roster](../../../../artifacts/atelier/inventory/vehicle-roster.json).

## Review summary

| Decision | Demo position |
|---|---|
| Art style | Original miniature European district; clear masses and restrained stylization |
| Scale | Original tile/world geometry; 2â€“4 storey buildings, exaggerated readable vehicle features |
| Detail | Roof courses, chimneys, windows, balconies, awnings, loading doors, streetlights and platform furniture; high-resolution sprite alternatives |
| Materials | Matte plaster/brick/stone; subdued glazing and metal; light weathering only |
| Colour/light | Olive ground, warm buildings, cool roofs/water, company-colour bands; fixed soft baked daylight |
| Gameplay readability | Routes, vehicle types and station edges are distinct; existing UI and sprite sorting retained |
| Performance | Actual native paired results and limitations are in [performance.md](performance.md); no invented frame or memory figures |
| Full library | 8,492 existing world raster slots, spanning 256 stock vehicle records, plus a proposed [48-family expansion](production-catalog.md). Preserve 2,314 interface/font/face/logo slots. |

The scene contains 56 placed houses, 55 deliberately placed mature trees, four rail platforms, bus and truck stops, a coal mine/power station edge, a river, hills and two bridges. Two three-part trains, three buses, a truck and a ferry are dispatched: seven powered vehicles, 11 vehicle objects total. Native position logs confirm movement. The truck has a demonstration route but no goods-producing industry; the ferry travels between buoys without a passenger service. The warehouse model is a cosmetic replacement on an existing town-building ID, not a new functional industry.

Most full-library content remains visibly inherited: depots, fences, signals, mine/power-station art, the red river bridge, other bridges, tunnels, airports and other climates. Only the pale short overpass demonstrates new bridge art. This staged mixture is intentional coverage accounting, not a claim that the overhaul is complete.

The engine has no dynamic day/night, free camera rotation or temperate seasons, so no such gameplay images are supplied. Desktop computer-use access was denied; native screenshots and profiler output were used. No fly-through video is claimed. Manual selection/construction-overlay testing and large-city stress testing remain open review checks.

Read the [art bible](art-bible.md), [inspection and inventory interpretation](inspection.md), [export/rebuild instructions and provenance](pipeline.md), and [verification record](verification.md) before approving production. Save compatibility is scoped to the isolated art checkpoint; unrelated regional-economy work in the main checkout was not included or overwritten.

Do you approve this visual direction and demo asset set for full production, or what would you like changed?
