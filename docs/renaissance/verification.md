# Verification record — 2026-11-01

This is a playable Windows checkpoint, not certification of a full graphics overhaul or a production multiplayer release. All images in `evidence/` are from the actual compiled game. The ImageGen source material is separately labelled and is not used as gameplay evidence.

## Builds and tests

| Check | Result / boundary |
|---|---|
| Pristine upstream baseline | Built and launched from tag 15.3, SHA `14ec60f248547d4d062a1160f0fc26d742319888`, before engine edits. 863 build steps, approximately 243 seconds at eight jobs. |
| Baseline checks | 94 unit checks passed in the sandbox; the two font-dependent regression checks passed when rerun with normal host access: 96/96 overall. Initial sandbox font failures are retained in raw logs, not counted as game defects. |
| Native fork | Release build with assertions; 98/98 CTest checks passed, including attention threshold/empty-cargo cases and cyclic palette/alpha boundaries. |
| Dedicated server | Compiled successfully; 98/98 CTest checks passed. |
| Bootstrap | Full documented bootstrap rerun completed successfully using pinned/checksummed inputs. |
| Asset reproducibility | Independent repeated compilations produced the same 10,046,587-byte GRF, SHA-256 `490585bdf9c3de8e4a21774398d23d8907758b672d6d5faad3b132a5266ddec8`. 168 logical sprites / 672 encoded variants. |
| Startup and baseline save | Both builds launched; fork loaded the unmodified baseline save without missing content. Static graphics were accepted. |
| Save and reload | Fork saved `renaissance-fork-reload.sav`; isolated fork runs reloaded it and produced the normal, 2×, 4× and indexed screenshots. Native save dialog also produced the underserved-station fixture. |
| Route operation | The GameScript built stations, depot, rail, road, road depot and industries. The train moved, loaded/delivered coal and earned revenue in the actual game. A real train stop command created the attention fixture. |
| UI management | Healthy scene: attention filter reduced 2 stations to 0. Underserved fixture: 2 to 1, retaining Aurelia Colliery. Tooltip and button readable at both host-default and explicit 200% UI scale. Cargo/facility filtering is preserved by implementation; exhaustive combinations/localizations remain unverified. |
| Graphics | Actual near zooms 0/1/2 and overview zoom 3 captured and inspected. Soft steam and terrain visible; transparent ground footprints and track placement look correct in the coastal scene. Indexed fallback launched and rendered. This does not verify every slope, crossing, bridge, direction or custom NewGRF. |
| Animation | Water palette interpolation runs in the actual client; steam replacements retain the upstream five-frame lifetime. Train/steam movement and changing water presentation observed in the running game and network client. No vehicle-position interpolation added. |
| Matching-build network | Real Windows client connected to the dedicated fork server on `127.0.0.1:39791`, remained present through a 60-second run, and visibly simulated the operating train. No reported desync. The client was then intentionally terminated. |
| Upstream network boundary | Actual upstream 15.3 client rejected by the fork server with `wrong revision`, as intended. Upstream servers are not supported for this fork build. |
| CI | Windows workflow supplied; hosted execution is not assumed from a successful local build. Check the fork's Actions run for its actual status. |

The first network probe used the unpaced null video driver and missed sync frames, timing out during join. The verification harness was corrected to use the real Windows driver. The passing result is from that real driver; no simulation/network code was altered to hide the probe failure. A separate initial probe collided on identical server/client names; the harness now uses distinct names.

The first hosted CI run exposed NML 0.7.5's undeclared wheel-build dependency on `ply`. Bootstrap now installs a pinned build environment and uses `--no-build-isolation`. This fix was verified by successfully building NML in a fresh local virtual environment with its wheel cache disabled. The hosted run's current status remains independently visible in GitHub Actions.

## Comparable evidence

| Pair / image | Conditions |
|---|---|
| `baseline-overview.png`, `after-overview.png` | Same pristine save, paused 5 April 1950, 1280×800, camera tile (50,43), zoom 3. Water palette phase can differ because it is local presentation state. |
| `baseline-detail.png`, `after-detail.png` | Same saved world and camera, zoom 1 (2×). Fork image uses the round-trip save; date, vehicles and funds agree. |
| `after-4x.png`, `after-normal.png`, `after-indexed.png` | Zoom 0, zoom 2 and indexed zoom 2 respectively. Shows fallback and the deliberately inherited structure pixels. |
| `station-attention.png` | Healthy route produces an empty attention list. |
| `station-attention-200.png` | Train deliberately stopped and time advanced to 17 September; one poor-service station remains, UI at 200%. |
| `multiplayer.png` | Real client and local server visible, operating train, 2 May 1950. |

The canonical demo save is 12,308 bytes, SHA-256 `b901e59bf7cceef42127320f9be00b66a33c0e1266acacb8810428676793d6ca`. It is a simple flat coastal test map, not a polished campaign. The main saved world remains healthy; the separate attention fixture intentionally stops the train.

## Performance

Host: AMD Ryzen 5 5600X, 6 cores / 12 threads, approximately 32 GiB RAM, Windows 11 Pro Insider Preview 10.0.26340. Portable Clang 23.1.4, CMake 3.31.6, Ninja 1.11.1.4. Rendering test: Win32 software presentation, 32bpp-anim, 1280×800, 60 Hz request, identical coastal save/camera/zoom 3. Smooth water and the custom pack enabled only in the fork. Other test windows may be present; this is a short interactive-host comparison, not a controlled lab benchmark.

`verify_runtime.py --mode gui --repeats 1` loads the same save, unpauses and samples `fps` at the next calendar-month boundary. The table uses the profiler's 512-sample columns, not an FPS-derived estimate of simulation work.

| Metric | Pristine 15.3 | Fork | Interpretation |
|---|---:|---:|---|
| Game loop rate | 37.04/s | 37.03/s | Expected 37.04/s |
| Draw/output rate | 60.07/s | 59.92/s | Both near requested 60 Hz |
| Game loop time | 0.02 ms | 0.02 ms | No measurable change at this precision |
| Drawing time | 0.03 ms | 0.03 ms | Same small static scene cost |
| Viewport draw time | 0.02 ms | 0.02 ms | Dirty-region averages, not full-map redraw time |
| Video output time | 0.49 ms | 0.71 ms | +0.22 ms; single-run output variance and palette updates need broader profiling |
| Peak working set | 84,459,520 B | 84,324,352 B | Similar; lazy sprite loading means this is not full-pack memory cost |
| Load-to-month-exit wall time | 52.395 s | 52.698 s | Mostly paced simulation, not a loading-time metric |
| Added asset package | — | 10,046,587 B | 9.58 MiB, three RGBA zooms and indexed fallback |

The console's drawing-rate “expected 33.33” label differs from actual output pacing; the output explicitly reports the 60 Hz video target. No simulation speed change was made to achieve animation.

Separate null-driver runs execute 10,000 loops including process startup and exit, with no renderer. Three alternating runs: coastal median 1.061 s baseline / 1.054 s fork. The busier upstream `opntitle.dat` scene (reported 41 trains, 111 road vehicles, 64 ships, 18 aircraft) measured median 2.897 s / 3.023 s, +4.3%; fork range 2.799–3.136 s overlaps/borders baseline 2.883–2.900 s. The 0.1 s polling cadence and startup costs limit precision; these numbers do not establish a speedup or renderer performance. The title scene is Toyland, so temperate terrain replacements are intentionally inactive there.

Budgets for the next iteration, established after this baseline: keep the coastal game loop within +0.05 ms or +10% (whichever is larger), draw work within +0.10 ms, output work below 1.0 ms on this host, no missed target simulation rate, additional observed working set below 32 MiB, and this terrain pack below 12 MiB. Investigate a repeatable >10% regression on fixed-loop busy-scene runs. These are checkpoint gates, not promises for other hardware or large maps. A large, heavily congested map and thousands-of-stations filter benchmark remain unverified.

## Compatibility and remaining verification

Save format remains version 362. The baseline save loads; the local setting and static graphics introduce no serialized fields or game-content dependency. Arbitrary older saves, LZO-compressed early saves, all base sets and mixed NewGRF stacks are not certified. Other packs replacing the same sprite IDs can conflict visually. Non-temperate terrain deliberately falls back.

Matching commit builds are the network boundary. The one-minute loopback test is not long-duration, cross-platform, command-load or reconnect certification. No upstream-client interoperability claim is made. Dedicated mode keeps the upstream simulation path and was actually built and exercised.

Still unverified: Linux/macOS binaries, high-latency and long-session networking, exhaustive company-colour/directional/occlusion cases, all steep slopes/foundations/bridges, extreme UI scales and translated overflow, very large/busy maps, and audio audibility through physical speakers. OpenSFX/OpenMSX were installed and accepted, but audio quality is not claimed from visual testing. Hosted CI results are separate evidence and must be read from the actual Actions run.

Raw local logs are kept in sibling `artifacts/`. Selected result JSON and test summaries accompany `evidence/`. Final package version, exact fork commit, executable hash and file checksums are in `BUILD-MANIFEST.json`; source is bundled with that exact committed revision.
