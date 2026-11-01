"""Make the editable source library pleasant to open. Run inside Blender.
GPL-2.0-only. This edits the source project, not exported sprite images.
"""
from pathlib import Path
import sys
import bpy
from mathutils import Vector

def gallery(path):
    names=[c.name for c in bpy.data.collections if c.name.startswith(('B0','I0','I1','N0','P0','V0'))]
    source=bpy.data.scenes.get('Source and export rig') or bpy.context.scene
    source.name='Source and export rig'; bpy.context.window.scene=source
    old=bpy.data.scenes.get('Asset library overview')
    if old: bpy.data.scenes.remove(old)
    scene=bpy.data.scenes.new('Asset library overview')
    scene.world=source.world
    for i,name in enumerate(sorted(names)):
        collection=bpy.data.collections[name]; collection.hide_render=False
        obj=bpy.data.objects.new(name+' [linked source]',None)
        obj.instance_type='COLLECTION'; obj.instance_collection=collection
        obj.location=((i%6)*26,(i//6)*26,0)
        scene.collection.objects.link(obj)
    bpy.context.window.scene=scene
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active
                space.shading.color_type='MATERIAL'
                rows=(len(names)+5)//6
                space.region_3d.view_distance=max(170,rows*23)
                space.region_3d.view_location=Vector((65,(rows-1)*13,0))
                space.region_3d.view_rotation=Vector((1,1,1)).to_track_quat('Z','Y')
                space.region_3d.view_perspective='ORTHO'
    readme=bpy.data.texts.get('START HERE') or bpy.data.texts.new('START HERE')
    readme.clear(); readme.write('RENAISSANCE ATELIER — editable sprite-source models\n\nThe overview contains linked collection instances. Select the Source and export rig scene to edit original meshes and material nodes. Collections use asset IDs. Isolate a collection before rendering. Rebuild production sprites using atelier_models.py and atelier_compile.py; this overview is not the gameplay scene. Units match OpenTTD authoring units, not economic metres.\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(path))

if __name__=='__main__': gallery(Path(bpy.data.filepath))
