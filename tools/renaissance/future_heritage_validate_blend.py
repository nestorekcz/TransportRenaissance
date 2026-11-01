"""Reopen every imported library and compare mesh bounds with supplied metadata."""
import argparse
import json
from pathlib import Path
import sys
import bpy
from mathutils import Vector

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
opt=p.parse_args(sys.argv[sys.argv.index('--')+1:]);OUT=opt.output.resolve()
entries=json.loads((OUT/'blender-import.json').read_text())
models={r['engine_id']:r for r in json.loads((OUT/'source/fleet/fleet_manifest.json').read_text())['records']}
checks=[]
for library in sorted({r['library'] for r in entries}):
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'source/blender'/library))
    for row in (r for r in entries if r['library']==library):
        c=bpy.data.collections[row['collection']]; objects=list(c.all_objects)
        points=[o.matrix_world@Vector(p) for o in objects if o.type=='MESH' for p in o.bound_box]
        assert points,row
        lo=[min(p[k] for p in points) for k in range(3)]; hi=[max(p[k] for p in points) for k in range(3)]
        assert len(objects)==row['imported_objects'],row
        missing=[im.name for o in objects if o.type=='MESH' for mat in o.data.materials if mat and mat.use_nodes for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and (im:=n.image) and not im.has_data]
        assert not missing,(row,missing)
        if row['state']=='default':
            source=models[row['engine_id']]['bounds_metres']
            error=max(abs(a-b) for a,b in zip(lo+hi,source['min']+source['max']))
            assert error<.002,(row,error,lo,hi,source)
        else:error=None
        checks.append({**row,'bounds_min':lo,'bounds_max':hi,'source_bounds_error':error,'missing_textures':missing})
    print('LIBRARY_CHECKED',library,flush=True)
assert len(checks)==344
(OUT/'verification/blender-libraries.json').write_text(json.dumps({'result':'PASS','collections':344,'base_models_bounds_checked':256,'records':checks},indent=2))
print('BLENDER_VALIDATION_PASS',len(checks),flush=True)
