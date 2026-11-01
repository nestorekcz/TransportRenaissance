# Measured native performance

Measured on 2026-11-01: AMD Ryzen 5 5600X (6 cores / 12 threads), 31.93 GiB usable physical RAM, NVIDIA GeForce RTX 3070, Windows 11 Pro Insider Preview 10.0.26340. Win32 native **software 32bpp-anim** blitter, hardware acceleration disabled, 1600 × 1000 window, full detail, 60 Hz output target. The GPU is identified for reproducibility, not presented as a measured acceleration path. GPU memory was not measured; the Windows CIM AdapterRAM field is a legacy 32-bit value and is not treated as VRAM capacity.

Same executable, config, save and camera for each pair; before = OpenGFX + existing Meadow, after = those plus Atelier. Each process runs the same saved February 1962 scene until the next calendar month, then executes the engine's `fps` profiler and exits. Windows process peak working set is polled at 100 ms. This includes startup and sprite loading; it is not GPU memory or exclusively asset memory. Timings are the first of the profiler's rolling 64/128/512-sample columns, not full-run averages. Raw logs retain all three columns.

| Graphics | Zoom | Run | Simulation updates/s | Video output frames/s | Drawing ms (64 samples) | Peak working set MiB |
|---|---:|---:|---:|---:|---:|---:|
| before | 2 | 1 | 37.04 | 59.97 | 0.09 | 90.63 |
| after | 2 | 1 | 37.04 | 59.99 | 0.10 | 90.96 |
| before | 0 | 1 | 37.08 | 59.99 | 0.04 | 86.88 |
| after | 0 | 1 | 37.10 | 59.95 | 0.04 | 86.74 |

Zoom 2 is normal (64-pixel tiles); zoom 0 is 4×. The test district has 56 placed houses, 55 planted mature trees, four rail stations, four road stops, two industries, seven powered vehicles and four wagons. All seven powered vehicles changed tile positions in every completed run. The fixture is moderately built up, not a production megacity stress benchmark. Measurements are a small sample on an active development desktop; differences below a millisecond should not be interpreted as statistically significant.

The new GRF is 8,268,322 bytes (7.89 MiB), with 322 logical replacement slots / 1,288 encoded alternatives. Its SHA-256 is `09b1856e0e6a3bd3c227ef695277ba72d435a0340b1af9d8821d85c948771854`. Source atlases are 1536 × 3456 at 1×, with 2× and 4× pages. The compiler packages cropped sprite rectangles, not the entire sparse atlas as a runtime texture. Source meshes total 30,664 base triangles across 35 collections before render modifiers; shared materials total 25. Mesh triangles, GPU draw calls and LOD costs do not apply to this sprite runtime. Actual sprite cache/GPU allocation was not instrumented separately.

Target interpretation: this fixture should sustain the engine's approximately 37.04 updates/s and 60 video frames/s without excessive memory growth. These runs test that target only on this machine. Large-city/1,000-vehicle tests, slower hardware and other platforms remain required before a full-library performance claim.

Raw evidence: `artifacts/atelier/verification-final/performance.json`, per-run `metrics.log` and `stderr.log`, plus `artifacts/atelier/hardware.json`. Do not use preliminary logs under `verification` as final-build measurements.
