# Approval-demo verification

**Demo only. Full production remains unapproved.**

| Check | Result / limit |
|---|---|
| Native build | Isolated project checkpoint plus three offline art helpers; release build with assertions |
| Engine tests | 98 / 98 passed, including both regressions; native Windows font access required |
| Asset compilation | 322 unique stable slots, 1,288 encoded alternatives, no duplicate IDs; required PNG/render/mask references resolve |
| Source | 35 editable Blender collections, 87 actual directional renders, shared procedural material nodes and separate company masks |
| Playback | Seven powered vehicles changed map tiles in every final benchmark: two trains, three buses, one truck, one ferry |
| District placement | 56 successful authored house placements and 55 mature trees. Six initially requested lots were already town roads; those connections were preserved and excluded from the final fixture plan. See scene-validation.json and fixture-final.log. |
| Comparison | Same paused save/camera/config; native 1600 × 1000 viewport captures with original game UI |
| Visual review | Normal and 4× buildings, roads/rail, platforms, bus stop, concrete bridge, vehicles, trees and shore; indexed fallback captured |
| Export geometry | Corrected screen-axis mapping, tree table selection, junction X/Y overlays, bridge front origins and repeatable pillar height after actual-engine review |
| Save compatibility | New scene loaded and saved with pinned stock OpenTTD; resulting stock save reloaded in art fork. No required functional NewGRF dependency or save schema change |
| Construction/selection | Existing bounds/commands/overlays preserved by design; hands-on interaction NOT verified because desktop adapter denied access |
| Full direction/state coverage | Encoded for mapped slots; exhaustive visual review of every slope, construction stage, orientation and death state remains pending |
| Large-city performance | Not established by this 56-house fixture; no 1,000-vehicle claim |
| Other climates/platforms/multiplayer | Not validated in this checkpoint; inherited assets retained |

The bridge sample upgrades its middle segments/fronts/pillars. Existing ramp sprites remain pixel art. Rail fences, reserved-track overlay art, signals and depots remain inherited. These are explicit boundaries, not missing references. The dead-tree state is a desaturated crown and needs a leafless source refinement before full-production acceptance. The new water surface does not reproduce palette-water animation.

The scene includes a cosmetic warehouse, an actual inherited coal mine/power-station route, passenger routes, a truck with a route but no goods supplier, and a ferry travelling between buoys. It demonstrates movement and asset coherence, not a complete new logistics economy. Existing capacity, cargo, date and ownership behavior is unchanged.

Day/night, free camera rotation and temperate seasonal rendering are not supported. No fake night/season images or concept-as-game screenshots are supplied. No video was recorded; native still captures are supplied because desktop capture access was unavailable.

Raw evidence is retained in `artifacts/atelier/verification-final`, `traffic-generation.log`, `runtime/fixture.log`, `build.json`, `demo-coverage.json`, and `artifacts/atelier-tests-final.log`. The full raster manifest distinguishes inherited, compiled/integrated and still-unverified coverage. Passing compilation is not treated as exhaustive visual validation.

Production expectation: 8,492 existing world raster slots; 322 demo replacements; 8,170 pending Atelier replacement. Preserve 2,314 interface/font/face/logo raster slots. The 256 stock vehicle roster records are a different counting unit. The proposed 48 expansion families have **zero approved production entries**. No full-overhaul completion claim is made.
