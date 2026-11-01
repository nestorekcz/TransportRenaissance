# Renaissance Atelier — art bible, approval draft

**Beautiful miniature transport world.** A temperate European river town with warm plaster, slate and terracotta roofs, pale limestone, restrained brick, blue-green transport liveries and quiet olive terrain. Architecture provides a calm backdrop; transport routes, vehicles and company colours carry the strongest small-scale contrast. The demo is an art-direction proposal, not completed production quality for the entire game.

## Scale and composition

The runtime is a sprite engine. Preserve its 16 × 16 world-unit tiles, 8-unit terrain steps, 2:1 projection and existing sorting boxes. Author one Blender unit per runtime world unit. This is a visual convention, not a claim that an OpenTTD tile represents 16 real metres: economic distances and train capacities remain abstract.

Use roughly 2.7–3.2 units per floor. Detached homes occupy 10–12 units within a tile; apartments and commercial frontages occupy 13–15. The demo caps occupied roofs at four storeys so platforms and road junctions stay visible. Place low buildings between transport corridors and taller blocks. Use two distinct detached silhouettes, pitched historic roofs, a flat apartment roof and a glazed office mass; avoid applying one roof to every building.

Vehicles are 9–11 units long and 2.5–2.9 wide; the ferry is longer. Exaggerate windows, cab mass, wheel contrast, lamps and livery bands so they survive 64-pixel tiles. Important edges should remain about one pixel at normal zoom. Model both vehicle sides. Render eight directions; legacy symmetric rail slots use four according to the engine's direction mask. Preserve all vehicle properties, capacities, speeds, ownership and order logic.

## Architecture and era

The approval district uses Central European plaster and masonry without copying a named building. Historic terraces establish continuous frontage; detached homes have setbacks and small garden details; mid-rise blocks have cornices and balconies; warehouses have loading canopies and boxes. Street props belong to platforms and lots, avoiding independent decorative simulation objects.

The scene starts in 1962 because the selected stock diesel, bus, truck and ferry are available then. The office glazing and rooftop solar panels demonstrate the proposed contemporary material language; they are deliberately anachronistic art samples in this fixture. Before full production, map historical, post-war and contemporary families to actual introduction dates. Static sprite replacement alone cannot give a shared base sprite an independent era schedule.

## Colour and materials

| Role | Working colour / response | Rule |
|---|---|---|
| Terrain | grass approximately RGB 104,125,76; soil 133,112,84 | Low contrast, fine grain, no photographic grass blades |
| Water | approximately 66,112,129 | Cool and restrained; shoreline warmer than water |
| Roads | 70,76,75; markings 203,197,168 | Dark enough for pale buses and track connections to read |
| Paving | warm grey / limestone | Quiet borders and entrances, not bright white outlines |
| Buildings | ivory, ochre plaster, muted brick | Largest surfaces generally below 0.55 HSV saturation |
| Roofs | slate blue-grey and subdued terracotta | Distinct large masses, no glossy roof glare |
| Vehicles | cream with company-colour bands | Company remapping is allowed to be more saturated |

Source materials use Principled BSDF, shared across the library. Most roughness is 0.6–0.9. Glass uses approximately 0.28–0.36 roughness and subdued blue reflection colour; it is rendered as legible glazing rather than physically transparent windows exposing empty interiors. Metallic response is restricted to steel, iron, zinc and vehicle paint accents. Fine noise modifies colour and bump modestly. The demo has light surface variation, not a finished library of aged façades.

Roof seams, chimneys, gutters, cornices, awnings, loading doors and rooftop equipment reward close zoom. Keep texture contrast below the contrast of doors and window frames. Do not paint text into storefronts or route displays. No bloom, depth of field, lens effects or fog is used in gameplay screenshots.

## Nature and terrain

Oak: broad clustered crown; lime: lighter, taller clusters; pine: dark tapered silhouette. Shrubs repeat as low planters. Seeded clustering is stable across exports. Growth states scale the trees; dying/dead variants currently desaturate the crown. A truly leafless death silhouette is a recorded refinement, not claimed as finished botany.

Grass, bare soil/regrowth, rough ground and exposed rocks retain all 19 inherited slope masks. Gravel is demonstrated in rail ballast and industrial/platform surfaces; sand appears in shore transitions. Exact opaque terrain silhouettes avoid alpha seams. Water and shoreline use nine base slots. River banks, canal structures, snow, desert and other climates outside those slots remain inherited.

## Camera, lighting and export

Use an orthographic camera 30 degrees above the ground, azimuth 45 degrees, matching the 2:1 tile. Source camera positions and projected origins are recorded by `atelier_models.py`; camera local X projects world Y minus world X, matching OpenTTD without mirroring. Use the same camera and rig for every source asset. Soft key/fill lighting is baked into sprite RGBA, with restrained contact shading. No long ground-cast shadows obscure rails. This renderer does not dynamically relight meshes.

Source rendering uses Blender 4.5 LTS Cycles, 24 samples, fixed seed 3107, denoising, Standard view transform, exposure 0 and gamma 1. It writes 576 × 576 RGBA renders and a separate material-index mask. PNG colour is sRGB; alpha and palette masks are data. Output uses straight RGBA and index 0 for transparent indexed pixels. Company-colour pixels use DOS remap index 202. No runtime normal, roughness, metallic, emissive, height or packed PBR texture is produced: the engine cannot consume them. There is consequently no normal-map handedness or channel packing to configure.

The export includes separately sampled 1×, 2× and 4× 32-bit sprites and a normal 8-bit fallback. Zoom-out uses the engine's existing sprite reduction path. Keep offsets consistent at every scale. There are no runtime mesh LODs, UV unwraps, collision meshes, skeletal rigs or material instances. Editable meshes use procedural object-space materials; they are source for sprites, not a falsely labelled real-time mesh package.

## Composition and performance rules

Keep small districts coherent through deterministic placement, restricted building families, setbacks and green gaps. Existing town growth is not rewritten. The fixture uses protected houses and frozen town growth solely to make comparison repeatable. Full production should use NewGRF town/house rules for era, zone and frontage variants; functional changes require separate review.

Source targets: detached buildings under 5,000 base triangles, mid-rise buildings under 15,000, vehicles under 8,000, tree species under 15,000. Modifier-evaluated render topology may exceed base counts; `source/catalog.json` records base mesh counts. These are authoring limits, not runtime draw-call budgets. Shared source materials may number more than a real-time mobile mesh would allow because only baked sprites enter the game.

Runtime targets for this demo: under 16 MiB compressed GRF; at most 128 × 128 normal pixels per replacement sprite; 1×/2×/4× alternatives; preserve 37.04 simulation updates/s and target 60 rendered frames/s on the measured desktop. Report actual measurements separately. A 56-house, 11-vehicle fixture is not proof of performance in a 1,000-vehicle city. Dense production stress testing remains an approval-following batch gate. Source PNG atlas pages are sparse authoring intermediates; the GRF stores specified sprite rectangles, not one giant GPU texture per prop.

## Unsupported and deferred presentation

No free camera rotation, arbitrary 3D renderer, dynamic PBR, day/night lighting or temperate seasonal simulation is available. No renderer changes are proposed for this approval demo. Snowline/climate swaps and existing palette animation can support later authored variants. The new 32-bit water surface is static; inherited palette-animated water is not silently advertised as animated new water. Night and winter concept images would not demonstrate this runtime and are not supplied as gameplay evidence.
