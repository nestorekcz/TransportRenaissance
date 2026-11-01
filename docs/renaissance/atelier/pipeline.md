# Reproducible source and export pipeline

All paths below are relative to the workspace containing `TransportRenaissance`, `tools`, and `artifacts`. No account, cloud service or install-wide configuration is required. The portable runtime uses `-X -x` and its own config/save directory.

## Inputs

- Engine art checkpoint: project commit `f1fa0af276`, plus `artifacts/atelier/source/engine-art-helpers.patch`. Do not build the demo against unrelated unfinished work in the current worktree. The corresponding frozen source is `artifacts/atelier-engine-source`.
- OpenGFX: pinned revision `e68bd9b7cb60305aa98c687b6836e0e0b08e2847` at `tools/sources/opengfx`.
- Blender: official portable 4.5.15 LTS, build hash `5afeabba6097`; archive SHA-256 `52dd02fd74877fa08e74b67d7854cf32468a232c02aaa19b6844c91285574f8d`.
- Python 3.9 environment: `tools/python/Scripts/python.exe`, Pillow and NML 0.7.5. CMake/Ninja and compiler dependencies follow the existing `tools/renaissance/dependencies.json`.
- Compiler: `tools/llvm-mingw-20261020-ucrt-x86_64`; dependency prefix `tools/deps`.

## Generate assets

```powershell
# Run from the workspace root.
tools/blender-4.5.15-windows-x64/blender.exe -b --factory-startup --python TransportRenaissance/tools/renaissance/atelier_models.py -- --output artifacts/atelier --samples 24
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/atelier_inventory.py
Copy-Item artifacts/atelier/inventory/ogfx1_base.nfo artifacts/opengfx-base.nfo
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/atelier_compile.py
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/atelier_inventory.py
```

For a clean first build, the inventory tool can run without a demo coverage file and records zero replacements until compilation. The second inventory run attaches actual replacements. `--only B01_linden_house,N01_oak` on the Blender command refreshes selected renders while recreating the complete editable source project. Never use an old partial `renders.json` as proof of a fresh full export.

`atelier_models.py` creates 35 named model/component/load-state collections, 25 shared materials, 87 directional source renders and separate material-index masks. The `.blend` opens to an overview of linked asset instances; switch to **Source and export rig** to edit original meshes. Collection IDs match the catalog. Isolate a collection for manual source rendering. The overview is an authoring aid, not the playable district.

`atelier_compile.py` maps base slots explicitly, applies original house draw origins, constructs matching terrain/road/rail surfaces, preserves exact terrain masks, and emits NML, GRF and PNG intermediates. Geometry source and the compiled game's sprite offsets are both retained. All vehicle orientations are actual model renders; no synthetic mirrored opposite sides. Company colours come from a separate mask pass. Compilation asserts unique IDs and maximum normal dimensions. Seeded source generation is reproducible; byte-identical Cycles output across different GPU/drivers is not guaranteed, so hashes identify this delivered build.

## Native build

Use the existing dependency setup. Configure the frozen art source with the same release flags as `build.ps1`, selecting `artifacts/atelier-engine-source` and `artifacts/atelier-engine-build`:

```powershell
$env:PATH = "$PWD/tools/llvm-mingw-20261020-ucrt-x86_64/bin;$PWD/tools/python/Scripts;$env:PATH"
cmake -S artifacts/atelier-engine-source -B artifacts/atelier-engine-build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=clang++ -DCMAKE_C_COMPILER=clang -DCMAKE_RC_COMPILER=llvm-windres "-DCMAKE_CXX_FLAGS=-include stdlib.h" "-DCMAKE_PREFIX_PATH=$PWD/tools/deps" "-DZLIB_LIBRARY=$PWD/tools/deps/lib/libzs.a" -DOPTION_USE_ASSERTS=ON
cmake --build artifacts/atelier-engine-build --parallel 8
ctest --test-dir artifacts/atelier-engine-build --output-on-failure
```

The three console helpers are `atelier_house`, `atelier_tree` and `atelier_view`. They are offline, developer-tool-only fixture commands. Houses use the existing house placement command, trees use the existing planting command followed by mature growth, and the view command flushes the existing viewport position before screenshots. There is no renderer, simulation-loop, save-schema or network-format change in this patch. The helpers are not needed by stock OpenTTD to load the scene.

## Stage and verify

```powershell
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/atelier_runtime.py stage
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/atelier_runtime.py generate
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/atelier_runtime.py capture
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/atelier_verify.py
```

`stage` refreshes the isolated runtime config/scripts; it does not modify other releases or personal saves. Before regenerating, archive the existing `runtime/save/atelier-demo.sav` and `runtime/screenshot/atelier-first.png` so `generate` cannot mistake an old result for a new one. Generation builds a 128² heightmap, fixed seed 20261101, town/roads/rail/industries, signals and seven powered vehicles, then places 56 protected houses and 55 mature trees and saves on the next calendar month. Other incidental trees may also exist.

`capture` launches the same paused save for each view and compares Meadow against Meadow + Atelier at identical camera settings. Native `screenshot viewport no_con` preserves the actual zoom and UI. Normal screenshot mode is not used for close-ups because it resamples to normal zoom. No source render is labelled as an in-game view.

`atelier_verify.py` runs sequential paired measurements using `fps` after one calendar month, polls Windows process working-set counters and logs vehicle positions through the GameScript. It also loads/saves through the pinned baseline executable, then reloads that result in the art fork. Native graphics and regression tests need normal Windows font/graphics access in this environment; restricted desktop access otherwise prevented correct native execution.

Re-run the compiler only when source/render changes require it. Re-run capture and paired benchmarks after changes affecting delivered graphics. Do not label every sprite visually verified merely because NML compiles: verify each batch's directions, states, slopes, sorting, masking and actual construction interactions. Automated captures do not replace manual overlay/selection checks.

## License and provenance

Original procedural geometry, material nodes, Python/Squirrel fixture scripts and source render exports were authored for this project with AI assistance. The project distributes its interest in these under GPL-2.0-only, without a claim of exclusive rights in AI-assisted output. No Cities: Skylines, SimCity, Transport Tycoon or other proprietary game assets were copied.

OpenGFX is GPL-2.0-only. Terrain/shore alpha masks, pixel-slot coordinates and structural layout references derive from its pinned sources. Preserve `OpenGFX-LICENSE.txt`, `authoroverview.csv` and all engine/dependency notices. Existing inherited sprites and the earlier Meadow package retain their original provenance; Meadow includes the previously documented ImageGen meadow texture. The new Atelier models are geometry, not generated image concepts.

The runtime includes the prior release's license directory and engine COPYING notice. Blender is an authoring dependency and is not bundled into the playable runtime. PNG and GRF are the supported game exports; no glTF/FBX/PBR export is misrepresented as loadable by this engine.
