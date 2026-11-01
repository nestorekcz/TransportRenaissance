# Finite expansion proposal — not in production

Existing replacement scope is the 8,492 world raster slots in `asset-manifest.json`, spanning all climates, economic chains and all 256 default vehicle records. Preserve the 2,314 interface/font/face/logo slots. Existing non-raster palette actions and gameplay definitions stay intact. Do not drop an inherited asset when its replacement is unfinished.

In addition, propose **48 numbered families** below. Counts are explicit deliverable families, not promises that a model has only one sprite. Before exporting each approved family, enumerate required directions, stages, load states and parent/child parts as child IDs (`E01.front.complete`, etc.). No unbounded procedural variants. The initial variant cap is listed; expanding it requires an updated catalog.

| ID | Family | Class | Initial cap |
|---|---|---|---|
| E01 | Gabled rural cottage | Diversity | 4 façade/roof variants |
| E02 | Farmstead dwelling | Diversity | 4 |
| E03 | Garden villa | Diversity | 4 |
| E04 | Narrow historic terrace | Diversity | 4 |
| E05 | Historic corner building | Diversity | 4 street orientations |
| E06 | Courtyard apartment | Diversity | 4 |
| E07 | Post-war slab apartment | Diversity | 4 |
| E08 | Contemporary stepped apartment | Diversity | 4 |
| E09 | Brick commercial frontage | Diversity | 4 |
| E10 | Hotel and restaurant frontage | Diversity | 4 |
| E11 | Civic hall | Diversity | 2 |
| E12 | Regional school | Diversity | 2 |
| E13 | Bench and bin set | Decoration | 4 orientations |
| E14 | Streetlamp family | Decoration | 3 heights |
| E15 | Planted verge | Decoration | 4 shapes |
| E16 | Hedge and garden boundary | Decoration | 4 corners/ends |
| E17 | Bicycle rack | Decoration | 4 orientations |
| E18 | Platform clock and wayfinding | Decoration | 4 orientations, no baked language |
| E19 | Café furniture | Decoration | 4 arrangements |
| E20 | Loading pallets/crates | Decoration | 4 arrangements |
| E21 | Warehouse service clutter | Decoration | 4 arrangements |
| E22 | Retaining-wall surface kit | Decoration | 4 surfaces |
| E23 | Flower/plaza planters | Decoration | 4 arrangements |
| E24 | Small urban green | Decoration | 4 tile layouts |
| E25 | Regional station frontage | Diversity | 2 track axes |
| E26 | Covered platform | Diversity | 2 axes, 3 parts per axis |
| E27 | Freight platform | Diversity | 2 axes |
| E28 | Bus terminal frontage | Diversity | 4 orientations |
| E29 | Truck loading court | Diversity | 4 orientations |
| E30 | Rail depot façade | Diversity | 4 orientations |
| E31 | Road depot façade | Diversity | 4 orientations |
| E32 | Concrete bridge detail kit | Diversity | 2 axes, inherited part inventory |
| E33 | Masonry viaduct detail kit | Diversity | 2 axes, inherited part inventory |
| E34 | Tunnel portal masonry kit | Diversity | 4 orientations |
| E35 | Dock-side warehouse frontage | Diversity | 4 orientations |
| E36 | Airport terminal frontage | Diversity | 2 layouts |
| E37 | Early regional rail livery | Diversity | 2 liveries, existing vehicles |
| E38 | Later regional rail livery | Diversity | 2 liveries, existing vehicles |
| E39 | Passenger coach interior/window variants | Diversity | 2 |
| E40 | Hopper cargo presentation | Diversity | empty/half/full |
| E41 | Regional bus livery | Diversity | 2 liveries |
| E42 | Delivery truck body | Diversity | 2 bodies |
| E43 | Ferry deck equipment | Diversity | 2 arrangements |
| E44 | Regional aircraft livery | Diversity | 2 liveries |
| E45 | Electric tram roster addition | New functional | 1 vehicle; tracks/power/cost/era rules required |
| E46 | Articulated regional bus | New functional | 1 vehicle; joint/capacity/path tests required |
| E47 | Intermodal cargo terminal | New functional | 1 facility; cargo acceptance and economy design required |
| E48 | Passenger interchange facility | New functional | 1 facility; catchment/transfer design required |

Decorations should be embedded in existing lot/station sprites unless independently placeable objects are approved. Diversity families must use valid NewGRF house/station/object definitions when their variants cannot be selected through existing base slots. E45–E48 are separate functional design proposals; art approval alone must not silently change the simulation.

After explicit approval, work in dependency order: (1) terrain/road/rail foundations, (2) residential families, (3) commercial/civic, (4) stations/logistics, (5) rail vehicles, (6) road vehicles, (7) ships/aircraft, (8) industries, (9) decoration/climate/season variants supported by the engine, (10) final coverage audit. Each batch requires sources, exported frames/masks, actual camera review, density/performance checks and manifest updates. Unverified slots stay inherited and visibly marked pending.
