"""Validate and package the revised demo and its review evidence. GPL-2.0-only."""
import hashlib
import csv
import html
import json
from pathlib import Path
import re
import shutil
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parents[2]; WORK=ROOT.parent
OLD=WORK/'artifacts/atelier'; OUT=WORK/'artifacts/atelier-r2'
def read(path): return json.loads(path.read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
before={r['sprite_id']:r for r in read(OLD/'demo-coverage.json')}
after={r['sprite_id']:r for r in read(OUT/'demo-coverage.json')}
assert before.keys()==after.keys()
unchanged=[]; changed=[]
for scale in (1,2,4):
    a=Image.open(OLD/f'game/atelier-{scale}x.png').convert('RGBA')
    b=Image.open(OUT/f'game/atelier-{scale}x.png').convert('RGBA')
    for sid,row in after.items():
        assert row['export_rect']==before[sid]['export_rect'],(sid,'anchor or size changed')
        x,y,w,h,dx,dy=row['export_rect']; rect=(x*scale,y*scale,(x+w)*scale,(y+h)*scale)
        assert rect[2]<=b.width and rect[3]<=b.height
        same=a.crop(rect).tobytes()==b.crop(rect).tobytes()
        if row['category'] not in ('road','rail'): assert same,(sid,'unrelated art changed')
        if scale==4: (unchanged if same else changed).append(sid)
        if row['category']=='road': assert a.crop(rect).getchannel('A').tobytes()==b.crop(rect).getchannel('A').tobytes(),sid
for name in (OLD/'renders').glob('B*.png'):
    assert digest(name)==digest(OUT/'renders'/name.name),name
for name in ('openttd.exe','save/atelier-demo.sav'):
    assert digest(OLD/'runtime'/name)==digest(OUT/'runtime'/name),name
for name in ('road-before','road-after','town-after','overview-after','rail-before','rail-after','vehicles-after','indexed-after'):
    assert Image.open(OUT/f'{name}.png').size==(1600,1000)
assert digest(OUT/'road-before.png')!=digest(OUT/'road-after.png')
assert (OUT/'source/atelier-library.blend').stat().st_size>100000
performance=read(OUT/'verification/performance.json')
assert len(performance)==4 and all(r['exit_code']==0 for r in performance)

status={
    'revision':2,'demo_only':True,'full_production_approved':False,
    'road_logical_slots':sum(r['category']=='road' for r in after.values()),
    'rail_logical_slots':sum(r['category']=='rail' for r in after.values()),
    'changed_sprite_ids':changed,'unchanged_sprite_count':len(unchanged),
    'all_house_renders_byte_identical':True,
    'non_road_rail_sprites_pixel_identical_at_all_zooms':True,
    'road_ground_alpha_identical_at_all_zooms':True,
    'engine_and_save_byte_identical_to_v1':True,
    'native_captures':8,'native_performance_runs':4,
    'source_collections':len(read(OUT/'source/catalog.json')),
    'sprite_camera_renders':len(read(OUT/'renders.json')),
    'grf_sha256':digest(OUT/'game/renaissance-atelier.grf'),
    'blend_sha256':digest(OUT/'source/atelier-library.blend'),
    'scope_note':'Source collections and render variants are not distinct complete asset families.',
    'limitations':[
        'Demo review only; full production remains gated by user approval.',
        'Road slopes, level crossings, bridge ramps, depot and stop ground surfaces retain inherited artwork.',
        'Rail slopes, fences, signals and station tracks retain inherited artwork.',
        'The long turnout and its point mechanism are source proposals; native tile junctions use the exported curve overlays.',
        'No railway physics, pathfinding, track gauge, vehicle capacity or costs changed.',
        'Vehicle models are the existing demo geometry, presented in larger studio views.',
        'Performance samples use the small fixed demo, not a dense-city stress benchmark.'
    ]}
(OUT/'validation.json').write_text(json.dumps(status,indent=2))
for r in after.values(): r['integration']='compiled; native demo reviewed at normal and close zoom; indexed fallback captured'
(OUT/'demo-coverage.json').write_text(json.dumps(list(after.values()),indent=2))
shutil.copytree(OLD/'inventory',OUT/'inventory',dirs_exist_ok=True)
manifest=read(OUT/'inventory/asset-manifest.json')
for row in manifest:
    if row['set']=='base' and row['sprite_id'] in after:
        entry=after[row['sprite_id']]
        row.update(replacement=entry['source_asset'],integration='native art demo revision 2; stable sprite replacement',
                   validation='1x/2x/4x and indexed compiled; representative native views reviewed; full topology/state matrix pending',
                   current_project_override='renaissance-atelier.grf / revision 2')
(OUT/'inventory/asset-manifest.json').write_text(json.dumps(manifest,indent=2))
with (OUT/'inventory/asset-manifest.csv').open(newline='',encoding='utf-8') as f:
    fields=next(csv.reader(f))
with (OUT/'inventory/asset-manifest.csv').open('w',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); writer.writeheader()
    for row in manifest:
        writer.writerow({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in row.items()})
summary=read(OUT/'inventory/summary.json')
summary['art_review_revision']=2
summary['revision_coverage']='322 logical demo slots; houses and other non-road/rail sprite pixels preserved from v1; no full-production approval'
(OUT/'inventory/summary.json').write_text(json.dumps(summary,indent=2))
for name in ('atelier_models.py','atelier_corridors.py','atelier_compile.py','atelier_gallery.py','atelier_studio.py','atelier_review_sheets.py','atelier_runtime.py','atelier_verify.py','atelier_revision.py','atelier_revision_package.py','build_assets.py','verify_runtime.py'):
    shutil.copy2(ROOT/'tools/renaissance'/name,OUT/'source/scripts'/name)

rows=[]
for run in performance:
    label=('Previous demo' if run['configuration']=='before' else 'Road revision')+(' / normal' if run['zoom']==2 else ' / 4x close')
    def metric(label): return re.search(re.escape(label)+r': ([0-9.]+)',run['metrics'])[1]
    rows.append(f"| {label} | {metric('Game loop rate')} | {metric('Video output rate')} | {metric('Drawing times')} | {run['peak_working_set_bytes']/1048576:.2f} MiB |")
readme=f'''# Atelier road revision 2

The approved houses are unchanged. The roads now use editable meshes with raised paving, kerbs, gutters, curved corners and regular lane markings. The railway proposal has timber sleepers, rail fixings, visible aggregate and separate rail profiles. The existing train and road-vehicle models are shown in large, genuine source-model renders.

Open [the visual review](review.html), or run [Launch-Atelier-Demo.cmd](runtime/Launch-Atelier-Demo.cmd). The map opens paused; press F1 to run it. The editable library is [atelier-library.blend](source/atelier-library.blend). The first demo remains in ../atelier.

## Scope and validation

- {len(after)} logical demo sprite slots; 1,288 encoded sprite variants; {len(changed)} road/rail slots changed from v1.
- {len(unchanged)} slots unchanged. House PNGs are byte-identical; all non-road/rail atlas crops match at 1x, 2x and 4x.
- {status['source_collections']} source collections and {status['sprite_camera_renders']} sprite-camera renders. These counts include technical parts and topology variants, not complete production families.
- Eight native 1600 x 1000 captures, including an indexed fallback, and four native performance runs.
- Engine executable and save are byte-identical to the previous demo. The prior stock-save round trip and 98 passing engine tests remain applicable to those unchanged binaries; they were not rerun for this art-only revision.
- Current build: [build.json](build.json). Full checks: [validation.json](validation.json). The full prior inventory remains in [inventory](inventory/summary.json).

## Railway proposal versus game implementation

The straight, curve, crossing and transparent junction overlays are integrated into the demo. The larger turnout shown on the review board is a source design study with common bearers, check rails and a point motor. Its longer geometry and point mechanism are not represented as animated game infrastructure.

## Remaining demo boundaries

Road slopes, crossing tiles, bridge ramps, depot/stop ground; rail slopes, fences, signals and station tracks retain inherited artwork. Their transition style needs the next infrastructure pass if this direction is approved. This is not a full asset overhaul. The vehicle boards show the existing demo geometry, without claiming a new vehicle production pass.

## Performance evidence

Same saved map, same software renderer, 1600 x 1000. Before means Atelier v1; after means this revision. Each measurement is a native rolling profiler snapshot after about one in-game month. The GPU is used for offline model rendering, not runtime 3D assets. Peak process working set is system memory; no dedicated runtime GPU allocation was measured.

| Run | Simulation FPS | Video FPS | Drawing ms | Peak working set |
| --- | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

See [raw measurements](verification/performance.json) and [hardware](hardware.json). These are four observations of a small demo, not a dense-city performance guarantee.

## Reproduce from the workspace root

```powershell
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/atelier_revision.py stage
tools/blender-4.5.15-windows-x64/blender.exe -b --factory-startup --python-exit-code 1 --python TransportRenaissance/tools/renaissance/atelier_models.py -- --output artifacts/atelier-r2 --only 'I06*,I07*,I10*,I11*' --samples 24
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/atelier_compile.py --output artifacts/atelier-r2
tools/blender-4.5.15-windows-x64/blender.exe -b --factory-startup --python-exit-code 1 --python TransportRenaissance/tools/renaissance/atelier_studio.py -- --output artifacts/atelier-r2
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/atelier_review_sheets.py
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/atelier_revision.py capture
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/atelier_revision.py verify
tools/python/Scripts/python.exe TransportRenaissance/tools/renaissance/atelier_revision_package.py
```

The stage step copies the prior demo and preserves its approved exports. Native captures and verification need a Windows desktop graphics session. All new geometry and scripts are original procedural work under GPL-2.0-only, with existing source and runtime licences included. Studio views use the actual source meshes; no generated concept images stand in for game evidence.

Full production is still awaiting approval.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')

gallery=''.join(f'<figure><a href="{file}.png"><img loading="lazy" src="{file}.png" alt="{title}"></a><figcaption>{title}</figcaption></figure>' for file,title in [
    ('road-models','Editable road kit'),('train-models','Train source models'),('vehicle-models','Road-vehicle source models'),('railway-proposal','Railway proposal: the point motor is source-only'),('ferry-model','Additional ferry source model'),('overview-after','Actual game, normal zoom'),('town-after','Actual game beside the approved houses'),('rail-after','Actual game railway junction'),('indexed-after','Actual game, indexed fallback')])
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Atelier / Road revision 02</title>
<style>*{box-sizing:border-box}body{margin:0;background:#edece5;color:#243b3c;font:18px/1.5 Segoe UI,system-ui}main{max-width:1400px;padding:48px 28px;margin:auto}h1{font-size:clamp(36px,5vw,68px);line-height:1.05;margin:14px 0}h2{margin-top:48px}p{max-width:920px;color:#566a68}a{color:#176c73}nav{display:flex;gap:12px;flex-wrap:wrap;margin:26px 0}nav a,button{padding:10px 18px;border:1px solid #b8c7bd;border-radius:9px;background:#f6f5ee;font:inherit;color:#243b3c;cursor:pointer}button[aria-pressed=true]{background:#245e60;color:white}figure{margin:22px 0;background:#f6f5ee;padding:12px;border-radius:14px}img{width:100%;display:block;height:auto;border-radius:7px}figcaption{font-size:15px;padding:8px 6px;color:#566a68}.tag{font-size:14px;letter-spacing:.15em;color:#247b7e}footer{padding:30px 0;border-top:1px solid #c8ccc0}</style>
<main><div class="tag">RENAISSANCE ATELIER / REVISION 02 / DEMO REVIEW</div><h1>Streets with shape.<br>Transport models in detail.</h1><p>The houses you approved are unchanged. The road kit now has kerbs, paving, gutters, regular lane markings and curved corners. Below are the actual train and road-vehicle source models, plus a conventional railway proposal.</p>
<nav><a href="runtime/Launch-Atelier-Demo.cmd">Play revised demo</a><a href="source/atelier-library.blend">Editable Blender library</a><a href="README.md">Scope and verification</a><a href="validation.json">Validation data</a></nav>
<h2>Same map, revised streets</h2><p>These are native game captures at the same camera position. The model boards farther down use studio lighting and are labelled separately.</p><div><button id="old" aria-pressed="false" onclick="pick(false)">Previous roads</button> <button id="new" aria-pressed="true" onclick="pick(true)">Revised roads</button></div><figure><img id="comparison" src="road-after.png" alt="Revised roads in the actual game"><figcaption id="caption">Revision 02 — native game capture, close zoom</figcaption></figure>
<h2>Source models and gameplay checks</h2>'''+gallery+'''<h2>Demo boundaries</h2><p>The flat road kit and conventional railway sprites are integrated. Road slopes, crossings, bridge ramps, depot and stop ground, rail slopes, fences, signals and station tracks still use inherited art. The large turnout's point mechanism is a source proposal. Vehicle models are the existing demo geometry shown at a useful size.</p><p>Four native performance samples compare the previous and revised demo. Full measurements and the unchanged-house checks are in the verification links above. Full production remains awaiting your approval.</p><footer>Original editable meshes and source scripts · GPL-2.0-only · This is a representative demo, not a completed library.</footer></main>
<script>function pick(revised){document.getElementById('comparison').src=revised?'road-after.png':'road-before.png';document.getElementById('comparison').alt=revised?'Revised roads in the actual game':'Previous roads in the actual game';document.getElementById('caption').textContent=revised?'Revision 02 — native game capture, close zoom':'Previous demo — same saved map and camera';document.getElementById('new').setAttribute('aria-pressed',revised);document.getElementById('old').setAttribute('aria-pressed',!revised)}</script></html>'''
(OUT/'review.html').write_text(page,encoding='utf-8')
# Verify local review links, rather than shipping broken references.
for ref in re.findall(r'(?:src|href)="([^"]+)"',page):
    assert (OUT/ref).exists(),ref
(OUT/'delivery.json').write_text(json.dumps({'revision':2,'review':'review.html','readme':'README.md','launcher':'runtime/Launch-Atelier-Demo.cmd','models':'source/atelier-library.blend','build':read(OUT/'build.json'),'validation':status},indent=2))
print(json.dumps(status,indent=2))
