"""Package the fleet import with source provenance and native verification evidence."""
from collections import Counter
import difflib
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile
from PIL import Image

WORK=Path(__file__).resolve().parents[3]
ROOT=WORK/'TransportRenaissance'
OUT=WORK/'artifacts/atelier-future-heritage'
OLD=WORK/'artifacts/atelier-r2'
FLEET=OUT/'source/fleet'

def read(path): return json.loads(path.read_text(encoding='utf-8'))
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,data): path.write_text(json.dumps(data,indent=2),encoding='utf-8')

manifest=read(OUT/'import-manifest.json')
build=read(OUT/'fleet-build.json')
audit=read(OUT/'verification/native-engine-audit.json')
blender=read(OUT/'verification/blender-libraries.json')
compat=read(OUT/'verification/compatibility.json')
perf=read(OUT/'verification/performance.json')
mapping=read(OUT/'runtime-mapping.json')
assert len(mapping)==256 and {r['engine_id'] for r in mapping}==set(range(256))
assert audit['engines']==256 and audit['resolved_directions']==2048
assert audit['non_graphics_property_differences']==[]
assert blender['result']=='PASS' and blender['collections']==344 and blender['base_models_bounds_checked']==256
assert compat['exit_code']==0 and compat['stock_save_written'] and compat['fork_reload']['exit_code']==0
assert len(perf)==2 and all(r['exit_code']==0 for r in perf)
assert all(len(r['distinct_tiles_per_powered_vehicle'])==7 and min(r['distinct_tiles_per_powered_vehicle'].values())>1 for r in perf)
assert digest(OUT/'imports'/manifest['archive'])==manifest['archive_sha256']
# Compare every extracted member, including source documents and masks, with the ZIP.
archive_files=0
with zipfile.ZipFile(OUT/'imports'/manifest['archive']) as z:
    for info in z.infolist():
        if info.is_dir(): continue
        assert hashlib.sha256(z.read(info)).hexdigest()==digest(FLEET/info.filename),info.filename
        archive_files+=1
for row in manifest['imported_models']:
    assert digest(FLEET/row['file'])==row['sha256'],row['file']
world_hash=digest(OUT/'game/renaissance-atelier.grf')
assert world_hash==digest(OLD/'game/renaissance-atelier.grf')==digest(OUT/'runtime/newgrf/renaissance-atelier.grf')
assert digest(OUT/'runtime/save/atelier-roads-r2.sav')==digest(OLD/'runtime/save/atelier-demo.sav')
assert build['sha256']==digest(OUT/'game/future-heritage/future-heritage.grf')==digest(OUT/'runtime/newgrf/future-heritage.grf')
assert build['states']==344 and build['directions']==2752
captures=[('fleet-overview','Native game / normal zoom'),('fleet-road-vehicles','Native game / buses and revised roads'),
          ('fleet-freight','Native game / locomotive and empty freight wagons'),('fleet-ferry','Native game / ferry'),
          ('fleet-houses','Native game / approved houses preserved'),('fleet-indexed','Native game / indexed fallback'),
          ('train-purchase','Native train purchase list'),('road-purchase','Native road-vehicle purchase list'),
          ('ship-purchase','Native ship purchase list'),('aircraft-purchase','Native aircraft purchase list'),
          ('fleet-trains','Native game / railway context'),('fleet-diesel','Native game / passenger coaches')]
for name,_ in captures:
    with Image.open(OUT/(name+'.png')) as img: assert img.size==(1600,1000)
category_counts=Counter(r['category'] for r in manifest['imported_models'] if r['state']=='default')
libraries={category.lower():digest(OUT/'source/blender'/f'{category.lower()}.blend') for category in category_counts}
tests=(OUT/'engine-tests.log').read_text(encoding='utf-8',errors='replace')
rerun=(OUT/'engine-regression-host.log').read_text(encoding='utf-8',errors='replace')
assert len(re.findall(r'Test\s+#\d+:.*?Passed',tests))==96
assert '100% tests passed, 0 tests failed out of 2' in rerun

source=OUT/'source/integration'; source.mkdir(exist_ok=True)
for script in sorted((ROOT/'tools/renaissance').glob('future_heritage_*.py')):
    shutil.copy2(script,source/script.name)
for name in ('atelier_runtime.py','atelier_verify.py','verify_runtime.py','build_assets.py'):
    shutil.copy2(ROOT/'tools/renaissance'/name,source/name)
shutil.copy2(ROOT/'media/renaissance/atelier-demo/fleet-input.json',source/'archive_receipt.json')
shutil.copytree(OUT/'runtime/game/atelier',source/'demo-game-script',dirs_exist_ok=True)
shutil.copy2(OLD/'hardware.json',OUT/'hardware.json')
base=subprocess.check_output(['git','-C',str(ROOT),'show','f1fa0af276:src/console_cmds.cpp'],text=True)
modified=(WORK/'artifacts/atelier-engine-source/src/console_cmds.cpp').read_text()
(source/'engine-art-helpers.patch').write_text(''.join(difflib.unified_diff(base.splitlines(True),modified.splitlines(True),fromfile='a/src/console_cmds.cpp',tofile='b/src/console_cmds.cpp')),encoding='utf-8')

status={'result':'PASS','scope':'Import the supplied fleet; no full world-art production',
        'base_models':256,'empty_variants':88,'editable_collections':344,'blender_libraries':5,
        'category_counts':dict(category_counts),'archive_files_byte_identical':archive_files,
        'native_vehicle_ids':256,'native_purchase_directions_resolved':2048,'compiled_state_directions':2752,
        'non_graphics_property_differences':0,'world_art_byte_identical_to_road_revision_2':True,
        'prior_demo_save_preserved':True,'stock_save_roundtrip_passed':True,
        'engine_tests':{'initial_passed':96,'initial_failed_in_restricted_environment':2,'host_rerun_passed':2,'total_passed':98},
        'native_captures':len(captures),'small_demo_performance_samples':2,
        'sha256':{'archive':manifest['archive_sha256'],'fleet_grf':build['sha256'],'world_grf':world_hash,'blender_libraries':libraries},
        'limitations':['The runtime renders sprites, not the GLB meshes.',
                      'Supplied helicopter rotors are static in body sheets; the duplicate native overlay is suppressed.',
                      'Independent wheel/rod/rotor animations and 3D LODs were not added by this import.',
                      'The benchmark uses seven powered vehicles in a small demo, not a dense-city stress test.',
                      'The native audit resolves purchase graphics for every ID and direction; moving traffic covers representative demo vehicles.',
                      'Aircraft retain supplied airborne sprite art without landing gear; their source meshes retain landing gear.',
                      'Full world-art production and remaining infrastructure variants require a separate scope.']}
write(OUT/'validation.json',status)
rows=[]
for r in perf:
    def metric(label): return re.search(re.escape(label)+r': ([0-9.]+)',r['metrics'])[1]
    rows.append(f"| {'Normal' if r['zoom']==2 else '4x close'} | {metric('Game loop rate')} | {metric('Video output rate')} | {metric('Drawing times')} | {r['peak_working_set_bytes']/1048576:.2f} MiB |")
readme=f'''# Future Heritage fleet — imported and integrated

Open [the visual review](review.html), [browse every supplied model](source/fleet/START_HERE.html), or run [Launch-Atelier-Demo.cmd](runtime/Launch-Atelier-Demo.cmd). The game opens paused; press F1 to run traffic.

## Delivered

All 256 base vehicle models and 88 additional empty-cargo variants from the supplied archive are preserved and imported into five editable Blender libraries: [train engines](source/blender/train.blend), [carriages](source/blender/carriage.blend), [road vehicles](source/blender/road.blend), [ships](source/blender/ship.blend), and [aircraft](source/blender/aircraft.blend). Their collection assets retain the original mesh and material data, at the original model origin. The visible gallery uses collection instances. Empty variants are hidden in that gallery but remain available as assets.

Coverage is 35 train engines, 81 carriage slots, 88 road vehicles, 11 ships and 41 aircraft, including all built-in climates and IDs 0–255. Related roster slots can share design families; these counts do not imply 256 unrelated designs.

The [game-ready fleet GRF](game/future-heritage/future-heritage.grf) assigns artwork separately to every existing vehicle ID. The [ID and scale mapping](runtime-mapping.json) and [sprite manifest](sprite-manifest.json) record all replacements. 344 model/load states yield 2,752 directional sprites, with normal, 2x and 4x RGBA alternatives, indexed fallback and primary company-colour masks. The demo company uses dark blue. Loading uses the supplied empty/loaded states.

The runtime is still the native sprite renderer. The GLBs and Blender libraries are genuine editable authoring assets. Helicopter rotors are baked into the supplied body sprites; their duplicate native overlay is suppressed. This import adds no independent rotor, wheel or rod animation. Aircraft sheets omit landing gear, as supplied. Collision meshes, runtime 3D LODs and a 3D renderer conversion are outside this import.

## Play and install

The isolated demo already has both packs enabled. The house, road, rail and environment GRF is byte-identical to road revision 2. The former map is retained as `runtime/save/atelier-roads-r2.sav`; the fleet-enabled map is `runtime/save/atelier-demo.sav`. The original revision folders are unchanged.

For another compatible game installation, copy `future-heritage.grf` to its `newgrf` directory and enable it in NewGRF Settings before starting a new game. This is a regular vehicle NewGRF, not a static base-set override. Saved games using it retain that dependency. Other vehicle NewGRFs may override the same IDs; their combinations were not tested. No missing-art substitution or deletion of vehicle IDs is used.

## Verification

- All {archive_files:,} extracted files match the preserved ZIP byte for byte, including all 344 GLBs. The five Blender libraries reopen successfully, contain all 344 asset collections, and match bounds for all 256 base models; no missing external texture references were found.
- The native engine resolves all eight purchase directions for each of the 256 IDs from this GRF. Compared with the previous demo, there are zero differences in the audited type, speed, power, weight, capacity, cargo, price, running cost, introduction date, lifetime, climate and refit-mask fields. NML changes only `sprite_id` and the graphics assignments.
- The standard baseline engine loaded the fleet demo, ran its traffic and wrote a save. The art engine then reloaded that save successfully. This checks this save and these packs; it is not a claim of compatibility with every third-party GRF or later fork format.
- 96 engine tests passed initially. Two regression tests failed in the restricted environment, which logged font-loading warnings; both passed when rerun with host font access. All 98 tests therefore have passing results. Raw logs are included.
- Twelve 1600 × 1000 native captures cover representative moving vehicles, four purchase lists, the district and indexed fallback. This is not a manual gameplay review of every possible vehicle/load/orientation combination.

Evidence: [validation](validation.json), [native ID audit](verification/native-engine-audit.json), [Blender checks](verification/blender-libraries.json), [save roundtrip](verification/compatibility.json), [build manifest](fleet-build.json).

## Measured performance

Windows 11, Ryzen 5 5600X, approximately 32 GiB RAM; software `32bpp-anim`, 1600 × 1000, 60 Hz output target. The RTX 3070 is used for offline asset rendering, not native 3D game rendering. Two rolling profiler snapshots were taken after approximately one game month. All seven powered demo vehicles moved through multiple tiles. These are observations of a small scene, not a full-fleet or dense-city stress benchmark, and are not a paired before/after comparison.

| View | Simulation FPS | Video FPS | Drawing ms, 64 samples | Peak working set |
| --- | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

[Raw performance data](verification/performance.json) · [Hardware record](hardware.json). Working set is process system memory; GPU allocation was not measured.

## Source, provenance and rebuild

The original delivery receipt located the ZIP in the local temporary release directory. The exact ZIP is preserved in [imports](imports/TTD_Future_Heritage_Full_Fleet.zip). SHA-256: `{manifest['archive_sha256']}`. Its full extracted source, original documentation, geometry-generation scripts, reference provenance and licence files are retained under `source/fleet`. Existing licences apply to those supplied components; this import does not relicense the archive. The original archive README describes its pre-integration status; this document describes the subsequent integration.

New integration scripts and the read-only native audit/purchase-window helpers are copied to [source/integration](source/integration/). Scripts execute from their repository locations because workspace-relative paths are intentional. Dependencies already installed here are Blender 4.5.15, Python, Pillow and NML 0.7.5. Native capture/verification needs a Windows graphics session.

From the workspace root:

```powershell
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/future_heritage_import.py --archive artifacts/atelier-future-heritage/imports/TTD_Future_Heritage_Full_Fleet.zip
tools/blender-4.5.15-windows-x64/blender.exe -b --factory-startup --python-exit-code 1 --python TransportRenaissance/tools/renaissance/future_heritage_blend.py -- --output artifacts/atelier-future-heritage
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/future_heritage_compile.py
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/future_heritage_runtime.py stage
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/future_heritage_runtime.py generate
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/future_heritage_runtime.py audit
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/future_heritage_runtime.py capture
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/future_heritage_runtime.py performance
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/future_heritage_runtime.py compatibility
tools/blender-4.5.15-windows-x64/blender.exe -b --factory-startup --python-exit-code 1 --python TransportRenaissance/tools/renaissance/future_heritage_validate_blend.py -- --output artifacts/atelier-future-heritage
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/future_heritage_package.py
```

The engine helper patch is relative to project commit `f1fa0af2766d07820b15166179585b0ae4bbcd95`. It includes the existing demo helpers plus the fleet audit and purchase-window helpers. The isolated source/build are in `artifacts/atelier-engine-source` and `artifacts/atelier-engine-build`; rebuild with `tools/python/Scripts/cmake.exe --build artifacts/atelier-engine-build`. The GRF does not require the diagnostic helpers to display its vehicles. The `generate` step recreates only the fleet demo; preserve personal edits before rerunning it.

House and road revision sources remain in `artifacts/atelier-r2`. This fleet import is complete within the stated bounds. It does not approve or claim completion of full world-art production.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')

library_links=''.join(f'<a href="source/blender/{category.lower()}.blend">{html.escape(category)} · {count}</a>' for category,count in category_counts.items())
gallery=''.join(f'<figure><a href="{name}.png"><img loading="lazy" src="{name}.png" alt="{html.escape(label)}"></a><figcaption>{html.escape(label)}</figcaption></figure>' for name,label in captures)
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Future Heritage / Imported fleet</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f0eee6;color:#162b40;font:18px/1.55 Segoe UI,system-ui}main{max-width:1440px;margin:auto;padding:48px 28px}h1{font-size:clamp(42px,6vw,76px);line-height:1.05;margin:16px 0 24px}h2{margin-top:44px}p{max-width:960px;color:#4a5b68}a{color:#20546f}nav{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}nav a{background:#fcfaf3;border:1px solid #c5c9c8;border-radius:8px;padding:11px 16px;text-decoration:none}nav a:first-child{background:#172f49;color:#fff}.eyebrow{font-size:14px;letter-spacing:.14em;color:#88602c}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:16px;margin:34px 0}.stats div{padding:18px;background:#fffdf6;border-top:3px solid #c79a51;border-radius:4px}.stats strong{font-size:34px;display:block}.stats span{font-size:16px;color:#51616d}figure{margin:24px 0;padding:12px;background:#fffdf7;border-radius:12px}img{display:block;width:100%;height:auto;border-radius:5px}figcaption{font-size:15px;padding:8px 4px;color:#52616c}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,560px),1fr));gap:20px}.grid figure{margin:0}footer{border-top:1px solid #c8cbc5;padding:28px 0;margin-top:40px;color:#52616c;font-size:15px}</style>
<main><div class="eyebrow">RENAISSANCE ATELIER / FUTURE HERITAGE</div><h1>Your fleet.<br>Imported into the game.</h1><p>The supplied pearl, navy and amber models now have editable Blender libraries and native game graphics. The approved houses and revised road and railway artwork are preserved.</p>
<nav><a href="runtime/Launch-Atelier-Demo.cmd">Play fleet demo</a><a href="source/fleet/START_HERE.html">Browse all vehicle models</a><a href="game/future-heritage/future-heritage.grf">Game graphics pack</a><a href="README.md">Verification and rebuild</a></nav>
<div class="stats"><div><strong>256</strong><span>Built-in vehicle IDs</span></div><div><strong>88</strong><span>Additional empty variants</span></div><div><strong>5</strong><span>Editable Blender libraries</span></div><div><strong>2,752</strong><span>Directional state sprites</span></div></div>
<h2>Editable source library</h2><p>Original supplied geometry and materials, imported as collection assets. The catalogue contains related model families across roster slots. These are actual mesh renders from the archive.</p><nav>'''+library_links+'''</nav><figure><a href="source/fleet/START_HERE.html"><img src="source/fleet/Fleet_Overview.jpg" alt="Supplied full-fleet model contact sheet"></a><figcaption>Source-model render board from the supplied archive — separate from the native game captures below.</figcaption></figure>
<h2>Inside the native game</h2><p>Representative vehicles at normal and close zoom, plus the actual purchase lists. Select an image for its full 1600 × 1000 capture.</p><div class="grid">'''+gallery+'''</div>
<h2>Checked and preserved</h2><p>All 256 vehicle IDs resolve eight views. Audited prices, capacities, speeds, dates and other checked gameplay properties match the previous demo. All 344 Blender collections reopen, and all 256 primary model bounds match the supplied metadata. Save-and-reload checks passed in the standard baseline engine and art engine.</p><p>The native renderer uses sprites. Supplied helicopter rotor artwork remains static, and independent wheel or rod animations were not added. Performance measurements cover the small demo; dense-city testing remains separate.</p><nav><a href="validation.json">Validation report</a><a href="verification/performance.json">Measured performance</a><a href="runtime-mapping.json">All vehicle mappings</a><a href="import-manifest.json">Import provenance</a></nav><footer>Imported from TTD_Future_Heritage_Full_Fleet.zip · Original archive and reference licences retained · Full world-art production remains a separate scope.</footer></main></html>'''
(OUT/'review.html').write_text(page,encoding='utf-8')
for ref in re.findall(r'(?:src|href)="([^"]+)"',page): assert (OUT/ref).exists(),ref
write(OUT/'delivery.json',{'review':'review.html','launcher':'runtime/Launch-Atelier-Demo.cmd','model_browser':'source/fleet/START_HERE.html','readme':'README.md','build':build,'validation':status})
print(json.dumps({k:v for k,v in status.items() if k not in ('sha256','limitations')},indent=2))
