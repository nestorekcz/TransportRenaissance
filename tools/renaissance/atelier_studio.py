"""Large review renders of the real editable meshes; not gameplay captures."""
import argparse
import json
import math
from pathlib import Path
import sys
import bpy
from mathutils import Vector

p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,required=True); p.add_argument('--only',default='')
opt=p.parse_args(sys.argv[sys.argv.index('--')+1:]); OUT=opt.output.resolve()
(OUT/'studio').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'source/atelier-library.blend'))
scene=bpy.data.scenes['Source and export rig']; bpy.context.window.scene=scene
scene.use_nodes=False
scene.render.resolution_x=1200; scene.render.resolution_y=800
scene.render.resolution_percentage=100
scene.cycles.samples=48
scene.camera.data.shift_x=scene.camera.data.shift_y=0
scene.render.film_transparent=True
for c in scene.collection.children: c.hide_render=c.name!='RENDER_RIG'

try:
    pref=bpy.context.preferences.addons['cycles'].preferences
    pref.compute_device_type='CUDA'; pref.get_devices()
    for d in pref.devices: d.use=d.type=='CUDA'
    scene.cycles.device='GPU'
except Exception: pass

jobs=[]
for name in ['V01_meridian_diesel','V02_passenger_coach','V03_hopper_empty','V03_hopper_loaded','V04_civic_bus','V05_parcel_truck','V06_river_ferry']:
    jobs.extend([(name,'perspective'),(name,'side')])
for name in ['I10_road_10_urban','I10_road_09_urban','I10_road_07_urban','I07_road_intersection','I06_track_straight','I11_track_2','I11_turnout']:
    jobs.append((name,'perspective'))

records=[]
for name,view in jobs:
    if opt.only and not name.startswith(tuple(opt.only.split(','))): continue
    collection=bpy.data.collections[name]; collection.hide_render=False
    vehicle=name.startswith('V'); ferry=name=='V06_river_ferry'
    target=Vector((0,0,1.7)) if vehicle else Vector((8,8,.1))
    if view=='side': eye=Vector((0,26,4.7))
    elif vehicle: eye=Vector((16,24,13))
    else: eye=Vector((23,28,27))
    cam=scene.camera; cam.location=target+eye
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=(28 if ferry else 14) if vehicle else 26
    if name=='I11_turnout':
        target=Vector((13,7,.1)); cam.location=target+eye
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.ortho_scale=36
    path=OUT/'studio'/f'{name}-{view}.png'; scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)
    records.append({'source_collection':name,'view':view,'file':path.name,'kind':'studio render of editable source mesh; not gameplay'})
    collection.hide_render=True
    print('STUDIO_RENDER',name,view,flush=True)
records=[{'source_collection':name,'view':view,'file':f'{name}-{view}.png','kind':'studio render of editable source mesh; not gameplay'} for name,view in jobs if (OUT/'studio'/f'{name}-{view}.png').exists()]
(OUT/'studio/manifest.json').write_text(json.dumps(records,indent=2))
print('STUDIO_DONE',len(records),flush=True)
