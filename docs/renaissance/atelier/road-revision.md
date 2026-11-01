# Road revision 2 — demo review

The house direction is approved. The requested revision replaces the flat road strips with an editable modular street kit and presents the existing train and road-vehicle models at useful review scale. A conventional railway kit is proposed alongside them.

## Review and play

- [Before/after visual review and all model boards](../../../../artifacts/atelier-r2/review.html)
- [Launch revised demo](../../../../artifacts/atelier-r2/runtime/Launch-Atelier-Demo.cmd)
- [Road models](../../../../artifacts/atelier-r2/road-models.png)
- [Train models](../../../../artifacts/atelier-r2/train-models.png)
- [Bus and truck models](../../../../artifacts/atelier-r2/vehicle-models.png)
- [Railway proposal](../../../../artifacts/atelier-r2/railway-proposal.png)
- [Editable Blender library](../../../../artifacts/atelier-r2/source/atelier-library.blend)
- [Validation, measurements, limitations and rebuild commands](../../../../artifacts/atelier-r2/README.md)

## Street design

All 15 flat road topologies have matching carriageway widths and tile anchors. The 11 multi-connection layouts also have the city variant expected by the engine: 26 logical road replacements in total. The village version has an outer green margin; the city version uses paving to the tile edge.

Raised pale stone kerbs separate asphalt from pedestrian paving. Regular centre dashes continue through straight tile runs and stop before junction centres. Corners use actual curved geometry, with rounded paving islands at junctions. Drain grilles, gutter channels and restrained paving joints add detail at close zoom. The compiler extrapolates opaque edge colours before applying the exact native diamond mask, preventing grass from leaking through antialiased tile boundaries.

## Railway direction

Proposed materials: subdued grey ballast with angular aggregate, dark timber sleepers, rusty rail feet/webs and lighter steel running surfaces. Rail fixings and consistent sleeper spacing provide close-view detail. Six track directions, crossing and paired-curve sprites, and transparent junction overlays are exported from source meshes. Junction overlays omit ballast so a later route does not paint over an earlier route.

The larger turnout study uses a single ballast foundation and shared long bearers. It shows the intended check-rail and point-motor treatment. It is a source proposal: the native tiled junction continues to use its existing track logic and curve overlays; no animated points or new long turnout game feature is claimed.

## Preserved work and remaining scope

The house render PNGs are preserved byte-for-byte. All non-road/rail demo atlas crops remain pixel-identical at 1x, 2x and 4x. The same engine executable and saved map are used. The train, bus, truck and ferry boards show the existing source geometry in larger studio views.

Sloped roads, crossings, bridge ramps, depot and stop ground, rail slopes, fences, signals and station tracks still inherit earlier art. They need a matching infrastructure pass after this direction is approved. The mixed demo is not a completed world replacement. The original complete inventory and finite expansion proposal remain the production scope reference.

No full production approval is inferred from the positive response to the houses.
