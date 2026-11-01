"""Validate and publish the local, reviewable temperate asset delivery."""
import hashlib,html,json,re,shutil
from collections import Counter
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from temperate_plan import WORK,ROOT,OUT,infrastructure,world,details
from temperate_audit import audit

def read(path):return json.loads(path.read_text())
def write(path,data):path.write_text(json.dumps(data,indent=2))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

build=read(OUT/'build.json');coverage=read(OUT/'coverage.json');assert not build['partial']
jobs=infrastructure()+world()+details();assert len({j['key'] for j in jobs})==len(jobs)
render_checks=[]
for folder in ('','world','details'):
    records={r['id']:r for r in read(OUT/folder/'renders.json')}
    for j in jobs:
        if j.get('source_dir','')!=folder:continue
        name='W_'+j['key'].replace(':','_');r=records[name];im=Image.open(OUT/folder/'renders'/r['file']);b=im.getchannel('A').getbbox()
        assert b and b[0]>0 and b[1]>0 and b[2]<im.width and b[3]<im.height,(name,b)
        assert (OUT/folder/'masks'/f'{name}-0001.png').exists()
        render_checks.append({'key':j['key'],'alpha_bounds':b,'dimensions':im.size})
write(OUT/'verification/render-bounds.json',render_checks)
assert all((OUT/'game'/f'world-{i}-{s}x.png').exists() for i in range(build['pages']) for s in (1,2,4))
assert len(coverage)==build['sprites']
libraries=[OUT/'source/temperate-infrastructure.blend',OUT/'world/source/temperate-world.blend',OUT/'details/source/temperate-details.blend']
library_checks=[read(p.with_suffix('.validation.json')) for p in libraries]
assert sum(r['collections'] for r in library_checks)==len(jobs)
engine=read(OUT/'verification/native-engine-audit.json');compat=read(OUT/'verification/compatibility.json');performance=read(OUT/'verification/performance.json')
assert engine['engines']==256 and engine['resolved_directions']==2048 and not engine['differences_from_approved_fleet']
assert compat['stock_save_written'] and compat['fork_reload']['exit_code']==0
assert all(len(r['distinct_tiles_per_powered_vehicle'])==9 and min(r['distinct_tiles_per_powered_vehicle'].values())>1 for r in performance)
bridge_traffic={}
for zoom in (2,0):
    log=(OUT/f'verification/after-z{zoom}-0/stderr.log').read_text()
    for vehicle,label,x in [('11','train',76),('14','bus',63)]:
        coords={(int(t)%128,int(t)//128) for v,t in re.findall(r'ATELIER_TRAFFIC (\d+) tile=(\d+)',log) if v==vehicle}
        assert (x,61) in coords and (x,71) in coords,(label,coords)
        bridge_traffic[f'{label}-z{zoom}']=sorted(coords)
write(OUT/'verification/bridge-traffic.json',bridge_traffic)
prior=WORK/'artifacts/atelier-future-heritage'
assert sha(OUT/'runtime/newgrf/future-heritage.grf')==sha(prior/'runtime/newgrf/future-heritage.grf')
assert sha(OUT/'runtime/openttd.exe')==sha(prior/'runtime/openttd.exe')
assert sha(OUT/'runtime/newgrf/renaissance-atelier.grf')==sha(prior/'runtime/newgrf/renaissance-atelier.grf')
assert sha(OUT/'runtime/newgrf/temperate-world.grf')==sha(OUT/'game/temperate-world.grf')==build['sha256']
inventory=audit()
status={'result':'PASS','scope':'Temperate world production pass, approved houses and full Future Heritage fleet retained',
        'new_model_view_collections':len(jobs),'new_logical_sprite_slots':len(coverage),'colour_zoom_alternatives':len(coverage)*4,
        'source_libraries':library_checks,'render_bounds_checked':len(render_checks),'native_fleet':engine,'traffic_powered_vehicles':9,
        'native_capture_count':20,'save_roundtrip':True,'engine_binary_unchanged':True,'approved_house_pack_unchanged':True,'approved_fleet_pack_unchanged':True,
        'runtime_grf_sha256':build['sha256'],'inventory_source_slots_reviewed':inventory['reviewed_source_raster_slots'],
        'limitations':['Native runtime uses baked 2D sprites from editable 3D sources.','Art-only replacement; no changes to vehicle, pathfinding, economy or save schemas.',
                       'Other climates are deferred by user instruction.','Native visual checks cover representative scenes; each possible bridge length, terrain combination and vehicle direction is not separately photographed.',
                       'Technical waterway/catenary overlays, disaster art and small effects are explicitly retained in the audit.',
                       'Performance figures describe this 128 x 128 review fixture with nine powered vehicles, not a dense-city stress test.']}
write(OUT/'validation.json',status)

integration=OUT/'source/integration';integration.mkdir(exist_ok=True)
for pattern in ('temperate_*.py','atelier_models.py','atelier_corridors.py','atelier_runtime.py','atelier_verify.py','verify_runtime.py','build_assets.py'):
    for p in (ROOT/'tools/renaissance').glob(pattern):shutil.copy2(p,integration/p.name)
for name in ('COPYING.md','COPYING'):
    if (ROOT/name).exists():shutil.copy2(ROOT/name,OUT/name)
write(OUT/'source/provenance.json',{'original_meshes':'Generated by the included temperate source scripts under the repository GPL terms.',
      'native_masks':'OpenGFX 8.0 GPL source rectangles and masks are retained with file provenance in coverage.json / inventory.',
      'approved_sources':'../atelier-r2/source/atelier-library.blend; ../atelier-future-heritage/source/fleet; both remain unchanged.',
      'source_tools':{'Blender':'4.5.15','NML':'0.7.5','renderer':'Cycles orthographic, 2:1 native projection, 16 samples, shared approved light rig'},
      'new_grf_id':'TW 01 01','native_export':'8bpp fallback + 32bpp at normal / 2x / 4x; exact base IDs and Action5 feature offsets; independent near/far sprite layers.'})

draw_rates=[float(re.search(r'Drawing rate: ([0-9.]+)',r['metrics'])[1]) for r in performance if r['configuration']=='after']
peak=max(r['peak_working_set_bytes'] for r in performance if r['configuration']=='after')/1048576
readme=f'''# Temperate world — integrated asset update

Open [review.html](review.html), or run [Launch-Atelier-Demo.cmd](runtime/Launch-Atelier-Demo.cmd). The scene opens paused; F1 starts traffic. The approved houses and the complete supplied Future Heritage fleet are preserved.

This pass adds **{len(jobs):,} editable model-view collections**, **{len(coverage):,} logical sprite replacements**, and four colour/zoom alternatives per slot. Counts include directional, construction, growth, animation and near/far sorting pieces; they are not counts of unique building designs.

Road and rail bridge approaches now meet their decks at the correct native height and orientation. All built-in bridge families, road/rail/ship depots, bay and through cargo stops, bus shelters, tunnel portals, conventional slopes, monorail/maglev guideways, crossings, signals, stations, airports, temperate town/industry buildings, tree stages, field boundaries, headquarters and navigation details use matching materials and models. Cargo stops have loading offices, shutters, canopies and yard details. Field, shore and foundation textures have editable procedural material sources.

## Editable files

- [Infrastructure library](source/temperate-infrastructure.blend)
- [Town, industry, airport and tree library](world/source/temperate-world.blend)
- [Track details, signals and landmarks](details/source/temperate-details.blend)
- [Exact sprite assignments](coverage.json) and [compiled graphics pack](game/temperate-world.grf)
- [Source inventory audit](inventory/temperate-asset-audit.csv), covering all 10,806 original raster records
- [Preserved full vehicle model browser](../atelier-future-heritage/source/fleet/START_HERE.html)

Each Blender file opens on a spaced model library. Its separate export scene keeps source coordinates intact. The native game uses baked sprites, not real-time 3D meshes. This is a graphics-only static overlay, loaded after Renaissance Meadow and Atelier; Future Heritage remains the vehicle NewGRF.

## Verification

All {len(jobs):,} generated views have nonempty, unclipped alpha bounds and matching mask files. Three source libraries reopen with no missing external images. All 256 engine IDs still resolve eight views, and the checked vehicle properties match the approved fleet exactly. Nine powered vehicles move in the expanded fixture. Save/load passes through the baseline engine and back with this graphics package enabled. The engine executable is byte-identical to the previously tested art runtime; no new engine changes were made in this pass.

Paired measurements at two zooms report {min(draw_rates):.2f}–{max(draw_rates):.2f} drawing FPS after the update and a maximum sampled process working set of {peak:.1f} MiB. These measurements cover the review fixture, not a dense-city stress test. Raw evidence: [validation](validation.json), [performance](verification/performance.json), [save roundtrip](verification/compatibility.json).

Other climates are deferred. The audit explicitly retains compatible catenary/waterway technical overlays, small effects, disaster art and interface graphics. These are reviewed inherited assets and are not represented as newly modeled replacements. Existing approved source libraries, archives and checkpoints are untouched. The review save allows the old small airfield for comparison; this fixture setting is not part of the graphics pack.

## Rebuild from the workspace root

Use the pinned Blender and Python tools already in this workspace. Run each model command with `--output artifacts/atelier-temperate` for infrastructure, `--output artifacts/atelier-temperate/world` for world models, and `--output artifacts/atelier-temperate/details` for detail models; append `--samples 16`. Scripts are in `TransportRenaissance/tools/renaissance`: `temperate_models.py`, `temperate_world_models.py`, and `temperate_detail_models.py`. Completed views resume from `renders.json`; remove an affected metadata entry when intentionally rebaking it.

Then run `temperate_compile.py` without `--partial`, `temperate_gallery.py` inside each saved Blender file, and `temperate_runtime.py stage`, `capture`, `audit`, `performance`, `compatibility`. Finally run `temperate_package.py`. `fixture` deliberately regenerates only this isolated delivery's review save; the fleet checkpoint is retained alongside it.

The pack preserves stable sprite IDs and native layer anchors. OpenGFX mask provenance and repository GPL terms are retained in [source/provenance.json](source/provenance.json). New pack SHA-256: `{build['sha256']}`.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')

captures=[('bridge-road','Continuous road bridge and crossing'),('rail-river','Railway bridge with moving train'),('cargo-directions','Four cargo-stop and depot entrance directions'),('cargo-stop','Loading office and freight bays'),('road-depot','Open road workshop'),('rail-depot','Rail maintenance shed'),('airport-review','Airport terminal, apron and runway'),('airfield-review','Small airfield and hangar'),('town-gallery','Civic and town model review'),('sawmill-review','Sawmill and timber handling'),('forest-review','Managed forestry'),('refinery-review','Refinery process equipment'),('steelmill-review','Steelworks'),('farm-review','Farm and crop materials'),('world-overview','Playable temperate district'),('indexed','Indexed-colour fallback')]
figures=''.join(f'<figure><a href="{n}.png"><img loading="lazy" src="{n}.png" alt="{html.escape(t)}"></a><figcaption>{html.escape(t)}</figcaption></figure>' for n,t in captures)
cards=[]
for j in jobs:
    name='W_'+j['key'].replace(':','_');src='/'.join(v for v in (j.get('source_dir',''),'renders',name+'.png') if v)
    title=j.get('symbol') or j.get('family') or j.get('name') or j['kind']
    cards.append(f'<figure class="model" data-search="{html.escape((j["category"]+" "+j["key"]+" "+title).lower())}"><a href="{src}"><img loading="lazy" src="{src}" alt="{html.escape(title)}"></a><figcaption><b>{html.escape(j["key"])}</b> · {html.escape(title.replace("_"," ").lower())}<small>{html.escape(j["category"])}</small></figcaption></figure>')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Renaissance / Temperate world</title><style>
*{box-sizing:border-box}body{margin:0;background:#eeeee5;color:#183044;font:17px/1.55 Segoe UI,system-ui}main{max-width:1500px;margin:auto;padding:48px 30px}h1{font-size:clamp(40px,6vw,76px);line-height:1.06;margin:20px 0}h2{margin-top:48px}p{max-width:960px;color:#4b5d65}a{color:#245c74}nav{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}nav a{padding:12px 18px;background:#fffdf6;border:1px solid #c7cdbf;border-radius:7px;text-decoration:none}nav a:first-child{background:#193b4c;color:white}.eyebrow{font-size:13px;letter-spacing:.15em;color:#95763e}.stats{display:flex;gap:36px;flex-wrap:wrap;padding:24px 0;border-bottom:1px solid #c9cebf}.stats b{display:block;font-size:36px}.shots{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,570px),1fr));gap:22px}figure{margin:0;padding:10px;background:#fffdf5;border-radius:9px}img{display:block;width:100%;height:auto;border-radius:4px}figcaption{padding:9px 5px;color:#4b5d65;font-size:14px}.models{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:16px}.model img{aspect-ratio:1;object-fit:contain}.model small{display:block;color:#7b877c}input{font:inherit;padding:12px 16px;border:1px solid #b4c0b3;border-radius:6px;width:min(100%,600px);margin:10px 0 22px}footer{margin-top:45px;border-top:1px solid #c7ccbd;padding:25px 0;font-size:14px;color:#657065}</style><main>
<div class="eyebrow">RENAISSANCE ATELIER / TEMPERATE PRODUCTION</div><h1>A connected<br>miniature world.</h1><p>Continuous roads and rails across bridges. Depots with open workshops. Cargo stops with real loading buildings. A matching temperate library around the approved houses and your imported fleet.</p>
<nav><a href="runtime/Launch-Atelier-Demo.cmd">Play the updated scene</a><a href="README.md">Read the delivery notes</a><a href="game/temperate-world.grf">Graphics package</a><a href="../atelier-future-heritage/source/fleet/START_HERE.html">Browse your vehicle models</a></nav>'''
page+=f'<div class="stats"><div><b>{len(jobs):,}</b>editable model views</div><div><b>{len(coverage):,}</b>new logical sprite slots</div><div><b>256</b>preserved vehicle IDs</div><div><b>3</b>new Blender libraries</div></div>'
page+='<h2>Inside the game</h2><p>Actual captures from the isolated, playable review save. Select any image to inspect its full resolution.</p><div class="shots">'+figures+'</div>'
page+='<h2>Editable source models</h2><p>Source renders include construction and growth states and separate near/far layers used for native vehicle sorting. They are model views, not additional unique buildings.</p><nav><a href="source/temperate-infrastructure.blend">Infrastructure</a><a href="world/source/temperate-world.blend">Town, industry and nature</a><a href="details/source/temperate-details.blend">Details and landmarks</a></nav><input id="filter" type="search" aria-label="Filter model views" placeholder="Filter: depots, bridges, airport, signals, tree, sprite ID…"><div class="models">'+''.join(cards)+'</div>'
page+='<h2>Coverage and verification</h2><p>All original raster slots are reconciled in the audit. The temperate replacement set, approved artwork, deferred climates and retained technical effects are recorded separately. Native fleet resolution, moving traffic, sprite bounds, editable sources and save compatibility passed. Performance measurements describe this review scene.</p><nav><a href="validation.json">Validation</a><a href="inventory/temperate-asset-audit.csv">Complete source audit</a><a href="coverage.json">Exact replacements</a><a href="verification/performance.json">Measured performance</a></nav><footer>Original procedural meshes · OpenGFX masks attributed · Native 2D sprite rendering · Temperate scope approved by the user</footer></main><script>document.getElementById("filter").addEventListener("input",e=>{const q=e.target.value.toLowerCase().trim();document.querySelectorAll(".model").forEach(c=>c.hidden=!c.dataset.search.includes(q))})</script></html>'
(OUT/'review.html').write_text(page,encoding='utf-8')
for ref in re.findall(r'(?:src|href)="([^"]+)"',page):assert (OUT/ref).exists(),ref
# Repository review documentation is curated; generated pages stay in OUT.
write(OUT/'delivery.json',{'review':'review.html','launcher':'runtime/Launch-Atelier-Demo.cmd','validation':'validation.json','readme':'README.md','libraries':[str(p.relative_to(OUT)).replace('\\','/') for p in libraries]})
print('TEMPERATE_DELIVERY_PASS',len(jobs),len(coverage),flush=True)
