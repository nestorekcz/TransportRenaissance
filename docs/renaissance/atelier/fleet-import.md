# Future Heritage fleet import

The user requested importing `TTD_Future_Heritage_Full_Fleet.zip`. The archive's delivery receipt located the original in the local temporary release folder; its SHA-256 was verified before extraction. A preserved copy is now part of the import bundle.

## Open the result

- [Fleet integration review](../../../../artifacts/atelier-future-heritage/review.html)
- [Launch fleet-enabled demo](../../../../artifacts/atelier-future-heritage/runtime/Launch-Atelier-Demo.cmd)
- [Complete supplied model browser](../../../../artifacts/atelier-future-heritage/source/fleet/START_HERE.html)
- Editable Blender libraries: [trains](../../../../artifacts/atelier-future-heritage/source/blender/train.blend), [carriages](../../../../artifacts/atelier-future-heritage/source/blender/carriage.blend), [road vehicles](../../../../artifacts/atelier-future-heritage/source/blender/road.blend), [ships](../../../../artifacts/atelier-future-heritage/source/blender/ship.blend), [aircraft](../../../../artifacts/atelier-future-heritage/source/blender/aircraft.blend).
- [Game graphics pack](../../../../artifacts/atelier-future-heritage/game/future-heritage/future-heritage.grf)
- [Verification and rebuild notes](../../../../artifacts/atelier-future-heritage/README.md)

All 256 base models and 88 empty-cargo variants are imported as supplied. Mesh geometry, material nodes and original GLBs are preserved. The five Blender libraries contain marked collection assets and arranged instances. Empty variants remain available but hidden in the overview.

The game integration assigns eight-direction sprites to each existing vehicle ID through a regular NewGRF, rather than reusing shared base sprite slots. This retains distinct supplied models even where the original game shares artwork between vehicle IDs. It changes only the sprite selection property. Runtime audit data compares all 256 IDs with the prior demo and checks prices, capacities, speed, power, weight, cargo, running costs, introduction dates, lifetimes, climates and refit masks.

All 344 cargo/model states are packed at normal, 2x and 4x zoom, with indexed fallback and company-colour masks. The demo company uses dark blue. The renderer still uses sprites; Blender and GLB geometry are authoring assets. The helicopter rotor is present in the supplied body images; the duplicate native rotor overlay is suppressed. Independent rotor, wheel and rod animation remains future work, not an imported animation feature.

The prior house, road and railway GRF is byte-identical to revision 2. The original demo saves remain intact; this pack has a separate new demo save with its regular NewGRF dependency. Full world-art production is still outside this import request.
