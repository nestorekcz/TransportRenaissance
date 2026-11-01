"""Append the supplied GLBs into editable Blender libraries, without remodelling."""
import argparse
import json
import math
from pathlib import Path
import sys
import bpy
from mathutils import Vector

p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,required=True)
o=p.parse_args(sys.argv[sys.argv.index('--')+1:]); OUT=o.output.resolve()
SOURCE=OUT/'source/fleet'; LIB=OUT/'source/blender'; LIB.mkdir(exist_ok=True)
records=json.loads((SOURCE/'fleet_manifest.json').read_text())['records']; report=[]
for category in ('Train','Carriage','Road','Ship','Aircraft'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene; scene.name=category+' fleet gallery'
    geometry=bpy.data.collections.new('Editable source models'); scene.collection.children.link(geometry)
    display=bpy.data.collections.new('Gallery instances'); scene.collection.children.link(display)
    subset=[r for r in records if r['category']==category]
    span=85 if category=='Aircraft' else 65 if category=='Ship' else 28
    for index,r in enumerate(subset):
        for state,key in [('default','model'),('empty','empty_model')]:
            if not r.get(key): continue
            name=f"FH_{r['engine_id']:03d}_{state}"
            collection=bpy.data.collections.new(name); geometry.children.link(collection)
            before=set(bpy.data.objects)
            bpy.ops.import_scene.gltf(filepath=str(SOURCE/r[key]))
            imported=list(set(bpy.data.objects)-before)
            for ob in imported:
                for c in list(ob.users_collection): c.objects.unlink(ob)
                collection.objects.link(ob)
            collection['engine_id']=r['engine_id']; collection['vehicle_name']=r['name']; collection['source_glb']=r[key]
            collection['import_note']='Original supplied geometry and PBR material nodes; glTF Y-up converted by Blender importer.'
            collection.asset_mark(); collection.asset_data.description=r['name']+' / '+category+' / '+state
            # Source collections remain editable at their original coordinates.
            # Visible gallery instances are separate and carry all presentation transforms.
            geometry.children.unlink(collection)
            instance=bpy.data.objects.new(name+' / '+r['name'],None)
            instance.instance_type='COLLECTION'; instance.instance_collection=collection
            instance.location=((index%8)*span,(index//8)*span,0)
            if state=='empty': instance.hide_viewport=True; instance.hide_render=True
            display.objects.link(instance)
            report.append({'engine_id':r['engine_id'],'state':state,'collection':name,'library':f'{category.lower()}.blend','imported_objects':len(imported)})
            print('GLB_IMPORTED',r['engine_id'],state,len(imported),flush=True)
    text=bpy.data.texts.new('START HERE')
    text.write('FUTURE HERITAGE — imported vehicle library\n\nCollections are marked as assets. The visible gallery contains collection instances; the original geometry remains at authoring scale and origin. Instance a collection, or use Make Instances Real on a copy to edit. Empty-load instances are hidden in the gallery. GLB originals and materials remain in ../fleet/models. No geometry was regenerated or redesigned. Runtime sprites and their anchors are compiled separately.\n')
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                v=area.spaces.active; v.shading.color_type='MATERIAL'
                v.region_3d.view_perspective='ORTHO'
                v.region_3d.view_location=Vector((span*3.5,span*((len(subset)+7)//8-1)/2,0))
                v.region_3d.view_distance=span*max(8,(len(subset)+7)//8)
                v.region_3d.view_rotation=Vector((1,-1,1)).to_track_quat('Z','Y')
    bpy.ops.wm.save_as_mainfile(filepath=str(LIB/(category.lower()+'.blend')))
    print('LIBRARY_SAVED',category,flush=True)
(OUT/'blender-import.json').write_text(json.dumps(report,indent=2))
assert len(report)==344
print('BLENDER_IMPORT_COMPLETE',len(report),flush=True)
