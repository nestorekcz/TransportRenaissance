"""Stage and capture an isolated, native OpenTTD art review. GPL-2.0-only."""
import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import shutil
import subprocess
import time
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]; WORK=ROOT.parent; ART=WORK/'artifacts'; OUT=ART/'atelier'; RUN=OUT/'runtime'

def stage():
    for folder in ('baseset','lang','newgrf'):
        shutil.copytree(ART/'fork-runtime'/folder,RUN/folder,dirs_exist_ok=True)
    for file in ('openttd.exe',): shutil.copy2(ART/'atelier-engine-build'/file,RUN/file)
    for file in ('libunwind.dll','libc++.dll','libwinpthread-1.dll'):
        if (ART/'fork-runtime'/file).exists(): shutil.copy2(ART/'fork-runtime'/file,RUN/file)
    for folder in ('game/atelier','scripts','save','scenario/heightmap','screenshot'): (RUN/folder).mkdir(parents=True,exist_ok=True)
    for p in (ROOT/'media/renaissance/atelier-demo').glob('*.nut'): shutil.copy2(p,RUN/'game/atelier'/p.name)
    shutil.copy2(OUT/'game/renaissance-atelier.grf',RUN/'newgrf/renaissance-atelier.grf')
    config='''[misc]
resolution = 1600,1000
fullscreen = false
video_hw_accel = false
videodriver = "win32"
blitter = "32bpp-anim"
language = english.lng
display_opt = FULL_DETAIL
[graphicsset]
name = OpenGFX
[gui]
autosave_interval = 0
autosave_on_exit = false
pause_on_newgame = false
ai_developer_tools = true
newgrf_developer_tools = true
developer = 2
refresh_rate = 60
smooth_water = true
[game_creation]
map_x = 7
map_y = 7
heightmap_height = 4
heightmap_rotation = 0
starting_year = 1962
landscape = temperate
tree_placer = 0
custom_town_number = 1
[difficulty]
number_towns = 4
industry_density = 0
vehicle_breakdowns = 0
[economy]
town_growth_rate = 0
inflation = false
place_houses = 2
[game_scripts]
"Renaissance Atelier" =
[newgrf-static]
renaissance-meadow.grf =
renaissance-atelier.grf =
'''
    (RUN/'openttd.cfg').write_text(config)
    (RUN/'before.cfg').write_text(config.replace('renaissance-atelier.grf =',''))
    (RUN/'indexed.cfg').write_text(config.replace('32bpp-anim','8bpp-optimized'))
    im=Image.new('L',(128,128),128)
    for y in range(128):
        for x in range(128):
            h=128
            if 64<=y<=68: h=0
            if y<32 and 35<x<75: h=min(255,128+(32-y)*9)
            im.putpixel((127-x,y),h)
    im.save(RUN/'scenario/heightmap/atelier-river.png')
    positions=[]
    for x in (44,46,49,51):
        for y in (49,51,54,56): positions.append((x,y,6 if (x+y)%3 else 26))
    for x in (54,55,56,57):
        for y in (49,50,51,52): positions.append((x,y,29 if y<51 else 26))
    for x in (54,55,56,57):
        for y in (54,55,56,57): positions.append((x,y,14 if y==57 else 26))
    for x in (59,61):
        for y in (49,51,54,56): positions.append((x,y,30 if y<53 else 29))
    for x in (64,66,69):
        for y in (49,51): positions.append((x,y,18))
    # Fixed-seed town roads occupy these lots; preserve those connections.
    occupied={(54,52),(55,50),(55,51),(55,52),(55,54),(55,55)}
    positions=[p for p in positions if p[:2] not in occupied]
    finish=['script fixture.log','setting economy.place_houses 2']+[f'atelier_house {x} {y} {h}' for x,y,h in positions]
    trees=[(x,y,(x+y)%3) for x in (45,47,50,52) for y in (49,51,54,56)]+[(x,61,x%3) for x in range(40,72) if x not in (43,48,53,58,63,68)]+[(x,46,x%3) for x in (45,46,49,50,51,54,55,56,57,64,65,66,67)]
    finish += [f'atelier_tree {x} {y} {t}' for x,y,t in trees]
    finish+=['zoomto 2','scrollto instant 56 53','pause','save atelier-demo','screenshot viewport no_con atelier-first','script']
    (RUN/'scripts/finish.scr').write_text('\n'.join(finish)+'\n')
    (OUT/'scene-placements.json').write_text(json.dumps(positions,indent=2))
    (RUN/'scripts/game_start.scr').write_text('unpause\nschedule on-next-calendar-month scripts/finish.scr\n')
    (RUN/'scripts/autoexec.scr').write_text('')
    (RUN/'Launch-Atelier-Demo.ps1').write_text('''$ErrorActionPreference = 'Stop'
$runtime = $PSScriptRoot
Set-Content -LiteralPath "$runtime/scripts/game_start.scr" -Value "atelier_view 2 56 53`npause`n" -Encoding ascii
Start-Process -FilePath "$runtime/openttd.exe" -WorkingDirectory $runtime -ArgumentList "-X -x -c openttd.cfg -g `"$runtime/save/atelier-demo.sav`"" -RedirectStandardOutput "$runtime/play.log" -RedirectStandardError "$runtime/play-errors.log"
''')
    (RUN/'Launch-Atelier-Demo.cmd').write_text('@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Launch-Atelier-Demo.ps1"\r\n')

def launch(scene,config='openttd.cfg',extra=()):
    out=(RUN/'stdout.log').open('w'); err=(RUN/'stderr.log').open('w')
    return subprocess.Popen([str(RUN/'openttd.exe'),'-X','-x','-c',config,'-g',str((RUN/scene).resolve()),*extra],cwd=RUN,stdout=out,stderr=err)

def generate():
    p=launch('scenario/heightmap/atelier-river.png',extra=['-G','20261101','-d','script=4'])
    try:
        for k in range(1500):
            log=(RUN/'stderr.log').read_text(errors='replace')
            if 'Your script made an error' in log or 'could not be found' in log:
                raise RuntimeError(log[-7000:])
            if (RUN/'save/atelier-demo.sav').exists() and (RUN/'screenshot/atelier-first.png').exists():
                time.sleep(1); print('ATELIER_GENERATED',flush=True); return
            if p.poll() is not None: raise RuntimeError(log[-7000:])
            time.sleep(.1)
        raise RuntimeError('Generation timeout; '+log[-5000:])
    finally:
        p.terminate(); p.wait(timeout=15)

def capture(label,zoom,x,y,config='openttd.cfg'):
    target=RUN/'screenshot'/f'{label}.png'
    if target.exists(): target.unlink()
    (RUN/'scripts/game_start.scr').write_text(f'pause\natelier_view {zoom} {x} {y}\nscreenshot viewport no_con {label}\n')
    p=launch('save/atelier-demo.sav',config)
    try:
        for k in range(1200):
            if target.exists():
                time.sleep(.5); shutil.copy2(target,OUT/f'{label}.png'); print('CAPTURED',label,flush=True); return
            if p.poll() is not None: raise RuntimeError((RUN/'stderr.log').read_text())
            time.sleep(.1)
        raise RuntimeError('No capture '+label)
    finally: p.terminate(); p.wait(timeout=15)

if __name__=='__main__':
    pa=argparse.ArgumentParser(); pa.add_argument('action',choices=['stage','generate','capture']); op=pa.parse_args()
    if op.action=='stage': stage()
    elif op.action=='generate': generate()
    else:
        for row in [('before-overview',2,56,53,'before.cfg'),('after-overview',2,56,53,'openttd.cfg'),('before-close',0,55,52,'before.cfg'),('after-close',0,55,52,'openttd.cfg'),('station-close',0,51,45,'openttd.cfg'),('rail-vehicles-close',0,65,44,'openttd.cfg'),('road-vehicles-close',0,64,57,'openttd.cfg'),('ferry-close',0,68,64,'openttd.cfg'),('river-close',1,62,64,'openttd.cfg'),('indexed-check',2,56,53,'indexed.cfg')]: capture(*row)
