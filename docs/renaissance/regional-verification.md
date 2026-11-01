# Regional development verification — 2026-11-01

This records measured results for the Windows x64 regional implementation, based on OpenTTD 15.3. The build uses the pinned LLVM MinGW 23.1.4 toolchain, Release configuration with assertions enabled. These are local measurements; CI separately verifies the proposed commit. This is an independent fork, not an upstream OpenTTD release.

## Automated results

| Check | Result |
|---|---|
| CTest: existing engine tests, regional rules, native regressions | **106/106 passed**, isolated PR build run 15.42 seconds |
| Native command/utility integration fixture | **20 checks passed** |
| Optional main-game setting | Normal new worlds keep it disabled; GUI setting is editable before creation; the native command rejects mid-game changes |
| Saved option | A Builder save restores its mode even when the ambient main-menu config is Classic |
| Real farm → processor → shops route | Four trucks, zero seeded freight; **480 grain and 180 food units delivered** in the two-year fixture |
| City growth | Six housing lots reach **254 actual residents**, starting empty |
| Identically seeded native runs | Every monthly regional audit matches across both runs |
| Save/load | Final audit exactly preserved: ticks, lots, population, inventories, upgrade/service/financial fields and digest |
| Older save | Version 362 coastal railway loads successfully and explicitly migrates to Classic |
| Large region | **1,000 lots, 22,070 residents**, 36 calendar months, no inventory-limit violations |
| Multiplayer smoke | Matching client remains connected for 65 seconds; a serialized storage upgrade executes; old fork is rejected; no reported desync |

The 20 native checks cover setting availability before world creation and rejection of live changes, bounded passenger/mail arrival acceptance, side-effect-free price queries, one-time construction charges, empty reservations, occupied-site rejection, invalid map edges, pollution separation, conflicting town founding, no refunds on removing reservations, protected developed sites, a one-time construction-material discount, upgrade caps, actual road disconnection/reconnection, utility loss/recovery, unfunded-operation pause/recovery, and paid demolition with inventory removal. These run in a disposable copy; deliberately injected funds/materials are **test setup**, not part of the example save. The Classic new-world fixture uses the ordinary runtime's configuration, not the coastal-demo defaults.

The eight pure rule cases cover required-input conservation, output/storage limits, proportional utility shortages and recovery, disconnected/unfunded operations, two-input factories, bounded machinery bonuses, lossy recycling and smooth occupancy. The long rule case runs each definition for 2,000 cycles with alternating shortages, full stores, disconnections and unavailable operating funds, twice, comparing deterministic outcomes.

## Measured performance

`verify_regional.py` used a 128 × 128 flat temperate world with seed **20261101** and the native null video/sound/music drivers. Native vehicles, station transfers, payments, regional cycles and saves still execute; the null driver removes wall-clock pacing.

- Two-year example on the isolated PR build: **1.7480 s** and **1.4056 s**, each including startup, construction, simulation, saving and exit.
- Three-year 1,000-lot sandbox: **6.6672 s**, including startup, road/lot construction, simulation, saving and exit. Final tick 82,383; four live trucks and 22,070 residents.
- Example final tick 55,373; audit digest `3645620572514024687`. Stress digest `3449069637536679761`.

These are single-host elapsed observations with other applications running, not isolated microbenchmarks, renderer FPS measurements or a maximum-map scalability claim. Delivery counters sum native cargo acceptance history (current plus up to 24 preceding months); the three-year fixture's counters are therefore a rolling history, not lifetime deliveries. Native GUI captures were reviewed for the planner and the operating town. The automated Windows input helper could not reliably target the game window; no direct mouse-interaction acceptance result is claimed.

## Multiplayer scope

The test binds only `127.0.0.1:39793`, disables advertisement, stages isolated runtimes, loads the regional save and connects a matching Windows client using the real Windows video driver. The server queues `CMD_REGIONAL_ACTION` through the normal serialized network command path; the farm's storage changes from 256 to 512. A previous fork lacking the `rg1-` marker is then rejected as the wrong revision.

`regional netverify TILE` is a dedicated-server-only developer fixture that queues this owner-scoped storage upgrade. Do not use it against an important live world. It exists to exercise the real command wire format/dispatch, not to bypass simulation checks. Direct client UI submission, long-duration sessions, adverse latency, mixed architectures and cross-platform desync testing remain unverified.

## Reproduce

From the repository, after the normal build script:

```powershell
ctest --test-dir ..\artifacts\fork-build --output-on-failure
..\tools\python\Scripts\python.exe tools\renaissance\verify_regional.py
..\tools\python\Scripts\python.exe tools\renaissance\verify_regional_network.py --incompatible-runtime ..\artifacts\pinned-baseline-runtime
..\tools\python\Scripts\python.exe tools\renaissance\capture_regional.py
..\tools\python\Scripts\python.exe tools\renaissance\package.py
```

Python needs Pillow. The network check requires a separately built upstream or pre-regional executable and matching languages; `build.ps1 -Baseline` supplies the path above. Native runtime tests need ordinary Windows font access; this host's restricted sandbox denies font access and causes unrelated font-output regressions. Final reported checks ran with normal host access, without filtering the failures away. Packaging requires a clean committed and rebuilt tree.

Evidence lives beside the repository in `artifacts/regional-verification/`: `results.json`, `command-checks/checks.log`, `stress/results.json`, `network/results.json` and native stdout/stderr logs. The first local development package included a `verification/` folder; normal releases retain this guide, and CI uploads the regional evidence separately. The example and flat source heightmap are also stored under `media/renaissance/regional/`.

See [current feature boundaries](regional-development.md#current-boundaries). Remaining work includes final approved art, full localization, a graphical chain browser, dedicated warehouse buildings, broader gameplay-content compatibility, avenue/congestion simulation and wider multiplayer/performance coverage.
