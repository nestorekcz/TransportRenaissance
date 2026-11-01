# Regional development playable

Transport Renaissance now includes an opt-in native regional economy. This is an engine extension to the existing OpenTTD fork, not a separate game or GameScript prototype. The original transport systems, company accounts, landscape, vehicles, and station windows remain in use.

## Play

Run the normal `Launch-TransportRenaissance.cmd`. Regional development is part of the same executable and is **disabled by default**; no separate launcher or add-on is required.

Choose **Load Game → regional-builder.sav** to try **New Haven**, a saved, operating example with four trucks, a farm, food processor, shops, six housing lots, renewable power, groundwater pumping/treatment, and public services. The first chain was built with zero seeded cargo and allowed to run for two years before saving.

Open **Towns toolbar → Regional development**. Click a developed regional building to inspect it. Use **Go to lot** or **Next constraint** to find the affected location. Original road, rail, depot, station, bridge and tunnel tools work as before.

For a new world, open the main menu's **Settings → Environment → Towns → Regional development**, select **Enabled (Regional Builder)**, and generate a **temperate** map with default gameplay content. Static visual packs are supported. Search Settings for `Regional development` to find it quickly. **Disabled (Transport Classic)** is the default: regional tools, upkeep and development simulation remain inactive, and the regional Towns-menu entry is hidden. **Enabled (sandbox)** makes regional construction/maintenance free and enables infinite money for transport construction and operation.

The setting is chosen **before creating the world** and saved with it. Its disabled control in a running game is intentional: existing saves cannot be converted by toggling it. Regional saves restore Builder even when the main-menu setting is Disabled; pre-expansion saves load in Classic. No separate installation is needed for either mode.

1. Choose **Found settlement**, enter a unique name, and select a flat empty 9 × 5 area. The preview is the initial development area. The town centre must be 32 tiles from other towns. Founding costs £5,000 plus an optional nine-tile starter street. The first click quotes the complete cost; click the same site again to confirm. Choose manual roads if you prefer.
2. Zone housing and shops on clear flat land within 48 Manhattan tiles of the centre. Choose housing density 1–3 and a 1 × 1, 3 × 3 or 5 × 5 brush. Density applies to housing; use facility upgrades for other buildings. Invalid tiles are skipped with an explanation. Brushes never silently clear trees, structures or existing reservations.
3. Build renewable power and a water pump alongside connected roads. A pump includes treatment and uses groundwater; separate underground pipes/cables are unnecessary. Services take three economic cycles to finish. Housing starts construction once road access and some power/water are available.
4. Build a farm and a food processor. Put truck stations in their catchments. Carry **Grain** (the existing produce cargo) to the processor. Refit a default goods truck to **Food** and deliver food from the processor to shops.
5. Keep the processor's inbound stop accessible. Full-load vehicles waiting for its output can obstruct inbound deliveries on a short shared stop. The example uses ordinary loading for food trucks.
6. Inspect housing to see actual residents, capacity, aggregate road-accessible jobs, consumed food, services, and environmental quality. Population approaches supported occupancy gradually. Food improves growth; shortages do not instantly empty a city.

Empty reservations can be removed free. Developed buildings require **Demolish**: select a lot, review its contents, then click again. Demolition costs 10% of actual investment, minimum £20, destroys remaining inventories and never refunds money. For an upgrade, inspect a finished lot, click an upgrade to quote its cost, and click it again to apply it.

## What the numbers mean

- An economic **cycle is 2,048 game ticks**, approximately 55 seconds at normal speed, about 27.7 economy days. It is not exactly a calendar month. Vehicles keep their normal cadence.
- Cargo amounts are whole native cargo units. Recipes are explicit conversions, not monetary value creation. Food and new dry freight use tons; existing grain, timber, ore, steel, oil and goods retain their original identifiers and units.
- Housing capacity is 24 / 64 / 160 by density, multiplied by capacity upgrades. Residents are separately simulated and saved. Neighborhoods can move up one density after eight consecutive cycles with good jobs, power, water and food. They do not oscillate between building types.
- Power/water are abstract capacity units per cycle. Each connected road component shares supply fairly in proportion to demand. Reciprocal road connections, crossings, drive-through stops, bridges and tunnels participate. Adjacent unconnected roads do not share supply. Public services additionally require a location within 12 Manhattan tiles.
- Public-service coverage and capacity differ: a nearby clinic can cover a lot while having insufficient capacity for the surrounding population. Five service categories contribute at most one fifth each; five fire stations cannot substitute for healthcare, education, waste and parks.
- Accessibility is **recent station service** and aggregate jobs in the road component. There are no individual citizens or measured congestion statistics.
- Housing both generates and accepts passengers/mail through native stations. Arrivals use bounded queues that clear at economic cycles; arrivals are never recycled into additional departing passengers.
- Village / Small town / Town / City / Metropolitan centre thresholds are 0 / 100 / 500 / 2,000 / 10,000 actual residents. Growth conditions, not time alone, determine whether population reaches those thresholds.

## Economy and ownership

There is one player/company budget. The founding company owns its regional lots and inventories. Only that company can upgrade or demolish them. Construction appears under construction expenditure; ongoing regional costs appear under property expenses. The planner reports regional investment and maintenance in the selected display currency.

There is **no extra sale payment, rent, tax, or industrial revenue**. Transport earns the existing distance/time/cargo payment when a native cargo packet reaches a final accepting destination. Native Transfer orders retain feeder accounting. Producing or buffering cargo does not pay a second reward. City development therefore needs a transport business able to support its upkeep.

Basic construction needs money, never delivered materials, so there is no bootstrap deadlock. Every developed lot can receive construction materials through a station. An upgrade consumes up to 20 locally stored units for up to a 20% price reduction. The same stock cannot discount another upgrade. Optional machinery is consumed for a capped 25% throughput bonus after an efficiency upgrade, with normal recipe inputs still consumed for the additional batches.

Unaffordable upkeep pauses the affected operation. Restoring funds lets it recover. A disconnected road pauses development/production. Utility shortages reduce output smoothly. Missing inputs and full output stores stop the relevant recipe without creating negative inventories. Regional input/output stores hold 256 units per cargo, or 512 / 768 after storage upgrades.

## Industrial content

The expansion uses 12 freight categories: existing grain, wood, iron ore, oil, steel and goods; plus food, bulk minerals, wood products, construction materials, machinery and recyclables. Existing passengers/mail and legacy freight are retained. Consequently the temperate world contains more than 12 total freight labels; this avoids deleting or renumbering inherited cargo.

| Operation | Required input per batch | Output per batch | Base batches/cycle |
|---|---|---|---:|
| Farm | — | 2 grain | 32 |
| Food processor | 2 grain | 1 food | 24 |
| Forest operation | — | 2 wood | 24 |
| Sawmill | 2 wood | 1 wood products | 20 |
| Furniture workshop | 2 wood products | 1 goods | 16 |
| Ore mine | — | 2 iron ore | 24 |
| Quarry | — | 2 bulk minerals | 28 |
| Metalworks | 2 iron ore | 1 steel | 20 |
| Building-material plant | 2 bulk minerals | 1 construction materials | 24 |
| Factory | 1 steel + 1 wood products | 1 goods | 20 |
| Machinery works | 2 steel | 1 machinery | 12 |
| Fuel supplier | — | 1 oil | 24 |
| Fuel power plant | 1 oil | utility capacity | 8 |
| Recycling plant | 4 recyclables | 1 bulk minerals | 16 |
| Shops / distribution centre | delivered food and optional goods | 1 recyclable per 4 consumed units | demand limited |
| Renewable generation | — | utility capacity | 160 units |

The 17 operating definitions counting shops, distribution and both generation types share the same simulation. Most recipes require one input; the factory requires two. Extractors model renewable/available regional resources, without geological reserves or depletion. Polluting facilities and housing require at least five tiles of separation. Pollution diminishes with distance; cleanup upgrades reduce its effect.

Light/heavy industrial zoning develops into a furniture workshop/metalworks; civic zoning develops into a school. Their reservation price includes the eventual building. Broader regional demand does not automatically choose among many industry types: use the industry picker when you want a specific chain.

**Warehousing and freight terminals use native stations, station cargo buffers, and Transfer orders.** Distribution centres are final urban markets, not teleporting warehouses. There is no new dedicated warehouse building or expanded freight catchment.

## Current boundaries

- New regional worlds support temperate default gameplay content and static visual packs. Gameplay-changing NewGRFs, other climates and live conversion of old Classic towns are not supported by the regional tools. Classic retains the existing content systems.
- Roads use existing road types and capacities. No invented avenue speed/congestion system was added.
- Regional buildings use explicitly provisional inherited one-tile base-set artwork and native construction stages. Density changes are visible; a complete modern civic/industrial sprite set, unique facility-upgrade artwork, stockpile sprites and activity effects await separate art approval.
- The native planner is English-first. The regular controls have translation keys; explanatory dynamic text is not yet fully localized. Zoning uses click brushes, rather than drag painting.
- Service vehicles, individual commuting, resource depletion, dedicated warehouses and multiple municipal bank accounts are deliberately absent.
- Regional UI provides lot-level inspections and constraint navigation, not a full graphical multi-industry chain browser. Default native industry filters group regional lots under their underlying factory pool type; the regional planner supplies their actual operation names.
- Commands are synchronized and new state is saved. Matching-build loopback verification is recorded separately; this does not certify high-latency, cross-platform or long-duration multiplayer.
- New saves use fork save version **363**. Upstream and the previous fork cannot load them. Version 362 saves remain readable by this build and migrate to Classic without overwriting their originals.

## Developer entry points

See [regional engineering notes](regional-engineering.md) and [verification evidence](regional-verification.md). The compile-time definitions in `src/regional_economy.h` are the source of truth for recipes, costs, service capacities, growth thresholds and upgrade bounds.
