"""Organise real source meshes without changing native sprite coordinates."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector

source=bpy.context.scene;source.name='Native sprite export rig'
names=sorted(c.name for c in bpy.data.collections if c.name.startswith('W_'))
old=bpy.data.scenes.get('Model library')
if old:bpy.data.scenes.remove(old)
scene=bpy.data.scenes.new('Model library');scene.world=source.world
columns=12
for i,name in enumerate(names):
    c=bpy.data.collections[name];c.hide_render=False
    obj=bpy.data.objects.new(name+' — source instance',None);obj.instance_type='COLLECTION';obj.instance_collection=c
    obj.location=((i%columns)*26,(i//columns)*26,0);scene.collection.objects.link(obj)
bpy.context.window.scene=scene
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active;space.shading.color_type='MATERIAL'
            space.region_3d.view_distance=max(210,math.ceil(len(names)/columns)*23)
            space.region_3d.view_location=Vector(((columns-1)*13,(math.ceil(len(names)/columns)-1)*13,0))
            space.region_3d.view_rotation=Vector((1,1,1)).to_track_quat('Z','Y');space.region_3d.view_perspective='ORTHO'
readme=bpy.data.texts.get('START HERE') or bpy.data.texts.new('START HERE')
readme.clear();readme.write('TEMPERATE WORLD / editable source meshes\n\nModel library uses linked collection instances. W_ IDs match coverage.json. Native sprite export rig keeps every collection at its exact game origin; isolate one before rendering. Individual sprites may be near/far building fragments for vehicle depth sorting. Use temperate_*_models.py for deterministic rebuilding. Models are baked to 2D sprites for OpenTTD; this is not a real-time 3D renderer.\n')
report={'file':Path(bpy.data.filepath).name,'collections':len(names),'objects':0,'triangles':0,'missing_external_files':[],'empty_collections':[]}
for name in names:
    meshes=[o for o in bpy.data.collections[name].objects if o.type=='MESH']
    if not meshes:report['empty_collections'].append(name)
    report['objects']+=len(meshes);report['triangles']+=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes)
for im in bpy.data.images:
    if im.source=='FILE' and not im.packed_file and im.filepath and not Path(bpy.path.abspath(im.filepath)).exists():report['missing_external_files'].append(im.filepath)
assert not report['empty_collections'] and not report['missing_external_files'],report
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
Path(bpy.data.filepath).with_suffix('.validation.json').write_text(json.dumps(report,indent=2));print('TEMPERATE_LIBRARY_VALID',json.dumps(report),flush=True)
