# Regional economy engineering notes

## Inspection and extension boundary

This repository is OpenTTD 15.3 with native C++ simulation and nested-widget UI. `StateGameLoop` drives authoritative ticks; industry tile loops normally emit cargo, and `economy.cpp` receives native packet deliveries. Towns have native spatial indexes and derived population caches. Roads/rail, station catchments, orders, pathfinders, vehicle payments, terrain generation, land clearing and company ownership are established engine systems. Saves use table chunks; multiplayer replays typed commands with deterministic RNG. NewGRFs change supported content and callbacks, and GameScripts expose a constrained API. Arbitrary municipal networks and occupancy require engine code, not an asset pack or script assertion.

The previous visual modernization changes terrain, water colour sampling and steam, while buildings remain largely inherited. This extension reuses that renderer and its existing static pack. It does not approve new final art or replace the projection, collisions, vehicle simulation or UI framework.

## Module map

| File | Responsibility |
|---|---|
| `src/regional_economy.h` | Data definitions and pure integer production/occupancy rules; compile-time recipe validation |
| `src/regional.h`, `src/regional.cpp` | Authoritative lots/towns, synchronized command, road connectivity, service capacity, fixed-cycle updates, diagnostics |
| `src/regional_gui.cpp` | Native planner, build filters, brushes, inspection, cost quotes, demolition/upgrade review |
| `src/regional_demo.cpp` | Offline reproducible example/stress builders using native commands; audit output |
| `src/saveload/regional_sl.cpp` | `RGLT` and `RGTW` versioned table chunks |
| `src/tests/regional_economy.cpp` | Recipe conservation, utility/input/storage limits, recovery, growth and deterministic stress tests |
| `tools/renaissance/verify_regional.py` | Real vehicle deliveries, seeded replay, roundtrip, old-save migration |
| `tools/renaissance/verify_regional_network.py` | Native serialized regional upgrade, matching client and old-fork rejection |
| `tools/renaissance/build.ps1`, `package.py` | Main game runtime/package, including the optional example and corresponding source |

Native integration hooks live in town/industry/station commands, cargo initialization, vehicle refit setup, economy delivery, cache rebuilding, toolbar, settings, viewport selection, network dispatch and save initialization. The changes leave Classic's production, town growth and cargo definitions unchanged.

## State and commands

`CMD_REGIONAL_ACTION` carries tile, action, kind, density and optional name. Test mode validates without mutation or RNG. Top-level native command handling checks funds and charges once; nested road creation contributes its cost to the enclosing founding command. Do not separately debit a top-level `Command::Do` result. Invalid actions, bounds, owners and upgrade levels are rejected.

Empty zones are map reservations. When construction starts, a lot receives a native Industry pool item, a one-tile footprint, and native accepted/produced slots. Population and capacity are regional state; population is reflected in the native town cache. `RebuildTownCaches` includes managed residents, and managed towns bypass autonomous building growth. The rest of the map remains autonomous. Each regional industry bypasses vanilla production and production-change callbacks, preventing double processing or spontaneous closure.

New native cargo labels occupy initially empty slots 12–17 only in Builder worlds: FOOD, BMNR, WDPR, BDMT, MACH, RCYC. Existing IDs remain unchanged. Default goods trucks receive refit capability for regional freight; NewGRF vehicle definitions are not rewritten. Regional gameplay rejects active non-static NewGRFs to avoid silently colliding with arbitrary industry/cargo definitions.

## Logistics invariants

Deliveries use `DeliverGoodsToIndustry`, native station catchment lists and existing source identity. Regional acceptance is limited by input capacity. `TriggerIndustryProduction` defers regional recipes to their economic cycle. Required inputs are consumed once; output is bounded before processing.

`MoveRegionalGoodsToStation` chooses the highest-rated eligible catchment station in stable order and uses the native packet/linkgraph insertion path with **whole units**. Output inventory decreases by the exact amount inserted. Do not replace this with repeated calls to fractional `MoveGoodsToStation` while retaining rejected output: accumulated fractions across multiple stations can otherwise over-promise inventory. Original industries retain their original distribution behavior.

Transfers never become new regional output or earn new final delivery revenue. Urban food/goods are consumed only after a real unload into the market's inventory; only the benefit of a final local sale is shared over a connected road component. Utility capacity is the only distributed resource. Recycling converts at most one fourth of consumption to recyclables and one fourth of those to minerals; it cannot self-feed.

Housing accepts passengers and mail through native industry arrival slots as well as producing departures. Accepted arrivals are consumed at the next funded economic cycle and do not increase departure production. This preserves inbound passenger/mail destinations without requiring individual citizen agents.

## Cadence and determinism

- Vehicles remain at native cadence.
- Regional updates run every 2,048 authoritative ticks.
- Connectivity is rebuilt once per regional cycle from reserved-lot frontages through reciprocal road bits and real tunnel/bridge endpoints. It is sparse; there is no every-frame map scan. Changes can take up to one regional cycle to affect displayed services.
- Nearby service/pollution queries use bounded map-row ranges (12-tile radius), not all-pairs lot scans. Command placement checks can scan the bounded lot collection; the cap is 8,192 lots.
- Pool IDs and `std::map` ordering determine processing and billing order. New randomness is not introduced outside deterministic native construction routines. No floating-point arithmetic controls the economy.
- New authoritative fields are saved. Derived road components are rebuilt, not serialized. UI selection/overlays and performance clocks are local presentation state.

Fuel power capacity is limited by both fuel inventory and water availability, matching the batches it can consume that cycle. Public-service contributions sum capacity by category before applying diminishing coverage benefit, so duplicate buildings in one category cannot masquerade as other services.

## Save and network compatibility

The save version advances from 362 to 363. Missing regional chunks leave an empty region; pre-363 saves explicitly reset regional mode to Classic before cargo initialization. Native inventory serialization remains in `INDY`; new chunks reference industry/town IDs. Loading validates indices, bounds, kind, stage, density, upgrade levels and map/industry associations. Never reuse numeric kind/cargo values for a different semantic meaning.

Network commands are in both native dispatch tables. The `rg1-` revision marker is checked before the normal git-hash compatibility fallback, preventing the old fork from joining based only on a common git revision. Increment this marker and save schema when introducing incompatible simulation changes. Identical source/build/content is the supported multiplayer boundary.

## Extending the economy

Add or edit a `Definition` and tests first. Keep one or two inputs, one primary output, and bounded optional machinery. Set explicit per-cycle rates, cost, upkeep, jobs, utility use, pollution and optional service capacity. Check processing mass/yield and the recycling graph. Extend cargo setup, names, refits, save validation and compatibility markers when adding a new label. Reuse an existing compatible label whenever possible.

`RegionalDrawHouse` and `RegionalDrawTile` provide kind/density/construction-state hooks. Final assets must preserve one-tile footprints or introduce an explicit versioned footprint migration, plus road access and native catchment/collision consistency. Current art is provisional, not an approved finished regional asset set.

Use the established Windows build script. Then run CTest and `verify_regional.py` using the bundled `tools/python` environment. On this host, font-dependent runtime tests require normal host access; font-denial output is retained rather than normalized away. Do not treat a null-driver speed measurement as GUI frame-rate evidence.

`economy.regional_mode` is a Basic, NewgameOnly world setting with default 0. The ordinary runtime uses `media/renaissance/openttd.cfg`, with region mode explicitly disabled and native town/industry generation defaults. The coastal generator uses its separate demonstration configuration. Both modes ship in one executable; the Towns-menu planner appears only when the current world enables it. Tests also attempt a live mode change and reload a Builder save while the ambient config is Classic.
