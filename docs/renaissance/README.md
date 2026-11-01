# Transport Renaissance — first playable

Transport Renaissance is a provisional name for an independent OpenTTD fork. It is not an official OpenTTD release and is not affiliated with or endorsed by the OpenTTD project. This is a native game, using the upstream simulation and renderer.

This checkpoint delivers a deliberately limited terrain, water, steam, and station-management slice. It is **not a complete graphics overhaul**. Most structures, vehicles, icons, and windows still use OpenTTD/OpenGFX presentation.

## Play

On Windows x64, extract the portable distribution and double-click `Launch-TransportRenaissance.cmd`. The coastal demonstration opens paused. Click the pause button to run the coal train. The scene includes Port Aurelia, a coal mine and power station, a working freight railway, two rail stations, rail and road depots, a connecting road, and shoreline.

The station-list toolbar opens the company menu. Select the company, then **Needs attention** to show stations with available waiting cargo and a displayed service rating below 50%, respecting the existing cargo/facility filters. A healthy route may correctly produce an empty list. This is not a platform-occupancy detector.

For an immediate positive example, load `renaissance-attention.sav` from the game's Load menu. The train was deliberately stopped in this derivative fixture; the filter retains Aurelia Colliery and removes the power-station destination. Resume the train through its status bar to restore service. The main coastal demo remains the healthy, operating route.

In Settings → Interface → Viewports, **Smooth water palette animation** controls the new cosmetic interpolation. The staged configuration enables it; the engine default remains off. Existing **Full animation** controls palette animation. `Launch-TransportRenaissance.ps1 -ReducedMotion` disables full palette animation; vehicles and simulation-driven effects still move. Existing transparency controls can hide effects.

## Build and maintain

The verified baseline is upstream tag **15.3**, commit **14ec60f248547d4d062a1160f0fc26d742319888**. It was the current stable release when inspected on 2026-11-01. The 16.0 release candidates were avoided for the first compatibility checkpoint. Upstream history and notices are preserved.

```powershell
git clone https://github.com/nestorekcz/TransportRenaissance.git TransportRenaissance
cd TransportRenaissance
git checkout codex/renaissance-first-playable
git remote add upstream https://github.com/OpenTTD/OpenTTD.git
.\tools\renaissance\bootstrap.ps1
.\tools\renaissance\build.ps1
..\artifacts\fork-runtime\Launch-TransportRenaissance.cmd
```

Prerequisites: Windows x64, Git, Python 3.9–3.13 (CI selects 3.11), PowerShell, internet access, and several GB of free space. The local build used Python 3.9.6. Use a workspace you own. The scripts install a pinned portable compiler and Python tools beside the repository, not system-wide. `dependencies.json` records exact source revisions and download hashes. Source stays in the repository; compiler downloads, builds, generated atlases, packages, and test logs live in sibling `tools/` and `artifacts/` directories. Close the staged test game before rebuilding it.

`build.ps1 -Baseline` creates a pristine detached worktree at the pinned commit and builds it. `build.ps1 -Dedicated` builds the dedicated server. Both run CTest unless explicitly passed `-SkipTests`. On this host, regression tests require normal access to installed Windows fonts; a restricted sandbox produced false font failures. The normal host run passed.

The portable LLVM 23.1.4 compiler needed `-include stdlib.h` to make C allocation declarations available to upstream's bundled fmt. This is a build flag, not a baseline source patch. Assertions remain enabled. PNG, zlib, liblzma, and OpenGL were found; LZO, Breakpad, XAudio2, Ogg, and Opus were not included. The Windows build retains WinMM/DirectMusic. Very old LZO-compressed saves are outside this package's verified support.

Upstream build guidance remains in [COMPILING.md](../../COMPILING.md). No Linux/macOS executable is claimed to have been tested here. Changes use portable C++; the supplied bootstrap is Windows-specific.

## Reproduce the content and scene

```powershell
..\tools\python\Scripts\python.exe tools\renaissance\build_assets.py --output ..\artifacts\assets
..\artifacts\fork-runtime\Launch-TransportRenaissance.ps1 -Generate
```

The asset compiler emits editable NML, 8-bit fallback and 32-bit 1×/2×/4× atlases, the GRF, and a per-sprite coverage manifest. `media/renaissance/source` holds the source artwork, masks, exact infrastructure rectangles, provenance, and generation prompt. The source image alone is not a game-ready sprite.

The demo GameScript constructs the route from a 128×128 heightmap with seed 20261101. The included save was generated and operated by pristine OpenTTD 15.3. For exact screenshot and performance comparisons, use that save, not a newly generated world. `game_start.scr` sets zoom 3 and camera tile (50,43). The launcher uses `-X -x` and a local config to isolate user settings. Output/error handles are redirected because this GUI MinGW build otherwise can fail when diagnostics write to an unavailable console.

## Engineering records

- [Architecture and extension audit](architecture.md)
- [Art specification, coverage and provenance](art.md)
- [Verification and compatibility](verification.md)
- [Third-party notices and distribution](THIRD_PARTY_NOTICES.md)
- [Prioritized continuation plan](roadmap.md)

Report fork bugs to this repository. Upstream's contribution guidance rejects fully automated/LLM-generated issues and pull requests; no upstream submission is part of this work. New code and procedural assets are AI-assisted and explicitly identified. Preserve human and upstream attribution; do not represent generated artwork as a named human artist's work.
