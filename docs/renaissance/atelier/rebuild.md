# Rebuild and collate the art

## Repository and artifact boundary

This PR starts at `main` commit `f1fa0af2766d07820b15166179585b0ae4bbcd95`. It contains procedural Blender sources, the fleet importer/compiler, sprite mappings, review fixture scripts, screenshots and measured evidence. It has no engine or normal-game packaging changes. `tools/renaissance/atelier_engine_helpers.py` emits the optional capture-helper patch from the reviewed `atelier_console_helpers.inc` source; apply it only in a dedicated fixture build. The normal game can load the resulting GRFs and save without these helpers.

The original workspace already contains the full playable delivery at `artifacts/atelier-temperate`, approved houses/roads at `artifacts/atelier-r2`, and the preserved supplied fleet at `artifacts/atelier-future-heritage`. [delivery-manifest.json](evidence/delivery-manifest.json) identifies the large generated files. They are kept outside Git; this PR does not silently bundle executables, the 118 MB supplied ZIP, or hundreds of MB of Blender outputs. GitHub's [screenshot review](review.md) works without those files.

For final integration, load the static packs in this order:

```ini
[newgrf-static]
renaissance-meadow.grf =
renaissance-atelier.grf =
temperate-world.grf =

[newgrf]
future-heritage.grf =
```

The fleet is a regular NewGRF and belongs in the world's NewGRF list. Load its review save or select it before creating a new game; do not force it into an unrelated existing save. Static world art is temperate-only. The imported fleet retains all supplied vehicle IDs/climates. Other world climates are deferred.

The separate regional-development and live vehicle-renderer branches own their engine/settings/launcher changes. After collating, stage the art files through the final package builder, decide which fleet renderer to expose, and repeat native capture, vehicle-property and save checks on that combined engine. The compatibility results in this PR describe the isolated art checkpoint, not a combined regional/live-mesh build. No automatic merge or default-launcher change is part of this PR.

## Inputs and layout

Use Windows x64 and the sibling layout established by `tools/renaissance/bootstrap.ps1`:

```text
workspace/
  TransportRenaissance/       this source checkout
  tools/                     pinned compiler, Python, OpenGFX and Blender
  artifacts/                 generated sources, sprites, runtimes and evidence
  TTD_Future_Heritage_Full_Fleet.zip
```

Run the existing bootstrap and normal/baseline builds as described in the [project guide](../README.md) to obtain `tools/python`, `tools/sources/opengfx`, `artifacts/fork-runtime` and `artifacts/baseline-runtime`. The art sources use Blender 4.5.15 LTS (`5afeabba6097`) at `tools/blender-4.5.15-windows-x64`; its portable archive SHA-256 is `52dd02fd74877fa08e74b67d7854cf32468a232c02aaa19b6844c91285574f8d`. NML is pinned to 0.7.5 and OpenGFX to `e68bd9b7cb60305aa98c687b6836e0e0b08e2847`.

Supply the original fleet ZIP. Its expected SHA-256, byte count and model counts are committed in `media/renaissance/atelier-demo/fleet-input.json`; a temporary receipt from the original machine is no longer needed. `--archive` accepts its actual location, and `--assets-only` allows clean source import without an earlier runtime. Preserve the archive's complete notices and source tree.

## Generate source libraries and graphics

Run these commands from the workspace root after installing the prerequisites. They recreate the current approved direction, not byte-identical historical v1 checkpoints. Cycles output can vary between driver/hardware versions; the manifest hashes identify the delivered build.

```powershell
$python = "$PWD/tools/python/Scripts/python.exe"
$blender = "$PWD/tools/blender-4.5.15-windows-x64/blender.exe"
$scripts = "$PWD/TransportRenaissance/tools/renaissance"

& $python "$scripts/build_assets.py" --output artifacts/assets
& $python "$scripts/atelier_inventory.py"
Copy-Item artifacts/atelier/inventory/ogfx1_base.nfo artifacts/opengfx-base.nfo

& $blender -b --factory-startup --python "$scripts/atelier_models.py" -- --output artifacts/atelier-r2 --samples 24
& $python "$scripts/atelier_compile.py" --output artifacts/atelier-r2
Copy-Item artifacts/atelier/inventory artifacts/atelier-r2/inventory -Recurse

& $python "$scripts/future_heritage_import.py" --assets-only --archive TTD_Future_Heritage_Full_Fleet.zip
& $python "$scripts/future_heritage_compile.py"
& $blender -b --factory-startup --python "$scripts/future_heritage_blend.py" -- --output artifacts/atelier-future-heritage
& $blender -b --factory-startup --python "$scripts/future_heritage_validate_blend.py" -- --output artifacts/atelier-future-heritage

& $blender -b --factory-startup --python "$scripts/temperate_models.py" -- --output artifacts/atelier-temperate --samples 16
& $blender -b --factory-startup --python "$scripts/temperate_world_models.py" -- --output artifacts/atelier-temperate/world --samples 16
& $blender -b --factory-startup --python "$scripts/temperate_detail_models.py" -- --output artifacts/atelier-temperate/details --samples 16
& $python "$scripts/temperate_compile.py"

& $blender -b artifacts/atelier-temperate/source/temperate-infrastructure.blend --python "$scripts/temperate_gallery.py"
& $blender -b artifacts/atelier-temperate/world/source/temperate-world.blend --python "$scripts/temperate_gallery.py"
& $blender -b artifacts/atelier-temperate/details/source/temperate-details.blend --python "$scripts/temperate_gallery.py"
```

The temperate model exporters resume completed records from `renders.json`. For an intentional geometry change, regenerate in a fresh output folder or remove the affected render records before rerunning. A resumed partial batch is not evidence of a fresh full render. Do not use `temperate_compile.py --partial` for a release.

Outputs are `artifacts/assets/renaissance-meadow.grf`, `artifacts/atelier-r2/game/renaissance-atelier.grf`, `artifacts/atelier-future-heritage/game/future-heritage/future-heritage.grf`, and `artifacts/atelier-temperate/game/temperate-world.grf`. Source `.blend` files open as arranged collection libraries; their separate export scenes retain the original sprite origins. Masks, atlas coordinates, NML and coverage JSON remain beside each output.

## Native fixture and validation

For the existing delivery, use `temperate_runtime.py stage`, `capture`, `audit`, `performance` and `compatibility`, then `temperate_package.py`. `fixture` deliberately regenerates only this delivery's review save. These commands require the isolated helper engine and prior fleet runtime; they are not prerequisites for compiling the art.

To build those fixtures in a new workspace:

1. Run `atelier_engine_helpers.py --output artifacts/engine-art-helpers.patch` from the workspace root. Create a separate source checkout at the art checkpoint and apply that patch with `git apply`. Configure/build it as `artifacts/atelier-engine-build` using the flags in the historical [pipeline guide](pipeline.md). The patch adds five offline developer commands for houses, trees, camera, vehicle audit and purchase previews; it changes no save schema or renderer.
2. Copy the newly built `atelier-r2` source/render/game outputs into `artifacts/atelier` while retaining `atelier/inventory`. Run `atelier_runtime.py stage`, `generate` and `capture`. Copy its resulting `runtime` folder into `artifacts/atelier-r2/runtime`. This establishes the predecessor fixture needed by the import scripts; exact archived before/after images remain in the committed evidence.
3. Run `future_heritage_import.py --archive PATH` without `--assets-only`, then `future_heritage_runtime.py stage`, `generate`, `audit`, `capture`, `performance` and `compatibility`.
4. Run `temperate_runtime.py stage`, `fixture`, `capture`, `audit`, `performance` and `compatibility`, then `temperate_package.py`. Keep the game closed between runs. A native Windows graphics/font session is required for these checks.

For a quick check from the repository root, requiring only Python's standard library:

```powershell
python tools/renaissance/check_atelier_review.py
# Also hash-check the original local delivery (not a newly rendered variant):
python tools/renaissance/check_atelier_review.py --workspace "C:/path/to/workspace"
python tools/renaissance/atelier_engine_helpers.py --output ../artifacts/engine-art-helpers.patch
git apply --check ../artifacts/engine-art-helpers.patch
```

The source checker compares generated assignment plans with committed coverage, checks preservation of approved house/tree slots, validates recorded bounds and native audit consistency, and checks screenshot dimensions. It does not rerender models, simulate traffic or benchmark the game. The path-filtered Atelier CI runs this check. Native evidence, measurement limits and the final post-benchmark buoy alias are retained under `evidence/verification`.
