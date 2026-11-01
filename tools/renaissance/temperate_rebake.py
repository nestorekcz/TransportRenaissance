"""Rebake one existing source collection without reconstructing its library."""
import bpy,sys,json,argparse
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--shift-y',type=float,default=0);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
out=Path(bpy.data.filepath).parents[1]
scene=bpy.data.scenes['Native sprite export rig'];bpy.context.window.scene=scene
for c in bpy.data.collections:
    if c.name.startswith('W_'):c.hide_render=c.name!=a.name
cam=scene.camera;cam.data.shift_y=a.shift_y
scene.render.filepath=str(out/'renders'/f'{a.name}.png')
for n in scene.node_tree.nodes:
    if n.type=='OUTPUT_FILE':n.file_slots[0].path=a.name+'-'
bpy.context.view_layer.update();origin=world_to_camera_view(scene,cam,Vector((0,0,0)))
bpy.ops.render.render(write_still=True)
records=json.loads((out/'renders.json').read_text())
for r in records:
    if r['id']==a.name:r['origin_px']=[round(origin.x*576),round((1-origin.y)*576)]
(out/'renders.json').write_text(json.dumps(records,indent=2));print('TEMPERATE_REBAKE',a.name,flush=True)
