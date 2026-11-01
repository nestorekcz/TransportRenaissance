"""Original, editable miniature-world demo assets. Blender 4.5 LTS; GPL-2.0-only.

Run: blender -b --factory-startup --python atelier_models.py -- --output PATH
Geometry and material nodes are the source; the .blend is an editable export.
No third-party models, copied architecture, or AI concept images are used.
"""
import argparse
import json
import math
from pathlib import Path
import random
import sys
import fnmatch
import bpy
import bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

args = argparse.ArgumentParser()
args.add_argument('--output', type=Path, required=True)
args.add_argument('--only', default='')
args.add_argument('--samples', type=int, default=24)
opt = args.parse_args(sys.argv[sys.argv.index('--') + 1:])
OUT = opt.output.resolve()
(OUT / 'renders').mkdir(parents=True, exist_ok=True)
(OUT / 'source').mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = opt.samples
scene.cycles.use_denoising = True
scene.cycles.seed = 3107
scene.view_layers[0].use_pass_material_index = True
scene.render.resolution_x = scene.render.resolution_y = 576
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'Medium High Contrast' if 'Medium High Contrast' in [x.name for x in bpy.types.ColorManagedViewSettings.bl_rna.properties['look'].enum_items] else 'None'
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1
scene.world.color = (0.3, 0.3, 0.3)
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.68,.76,.86,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .65
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='CUDA'; prefs.get_devices()
    found=False
    for d in prefs.devices:
        d.use=d.type=='CUDA'; found |= d.use
    if found: scene.cycles.device='GPU'
except Exception: pass

M={}
def material(name, color, rough=.78, metal=0, texture=None):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    n=m.node_tree.nodes; l=m.node_tree.links; p=n.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1); p.inputs['Roughness'].default_value=rough
    p.inputs['Metallic'].default_value=metal
    if texture:
        tc=n.new('ShaderNodeTexCoord')
        noise=n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=texture
        noise.inputs['Detail'].default_value=2
        l.new(tc.outputs['Object'],noise.inputs['Vector'])
        ramp=n.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position=.18; ramp.color_ramp.elements[1].position=.82
        ramp.color_ramp.elements[0].color=(*(v*.83 for v in color),1)
        ramp.color_ramp.elements[1].color=(*(min(1,v*1.12) for v in color),1)
        l.new(noise.outputs['Fac'],ramp.inputs[0]); l.new(ramp.outputs[0],p.inputs['Base Color'])
        bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.17; bump.inputs['Distance'].default_value=.035
        l.new(noise.outputs['Fac'],bump.inputs['Height']); l.new(bump.outputs[0],p.inputs['Normal'])
    M[name]=m; return m

material('Limestone',(.60,.52,.39),texture=16)
material('Warm plaster',(.72,.64,.49),texture=22)
material('Ivory',(.82,.79,.68),texture=30)
material('Ochre plaster',(.64,.40,.18),texture=20)
material('Brick',(.35,.16,.095),texture=16)
material('Slate',(.105,.15,.17),texture=22)
material('Terracotta',(.40,.17,.085),texture=25)
material('Zinc',(.22,.29,.28),.67,.15,18)
material('Timber',(.22,.13,.07),texture=18)
material('Glass',(.075,.19,.23),.28,.22)
material('Glass pale',(.22,.34,.36),.36,.1)
material('Iron',(.045,.075,.075),.59,.5)
material('Steel',(.35,.40,.39),.46,.65)
material('Rubber',(.025,.03,.028),.88)
material('Company teal',(.045,.26,.30),.6,.16)
material('Vehicle cream',(.80,.75,.60),.65,.05)
material('Signal red',(.55,.09,.045),.65)
material('Lamp',(.9,.73,.35),.5)
material('Asphalt',(.13,.145,.15),texture=25)
material('Paving',(.44,.43,.38),texture=28)
material('Gravel',(.29,.28,.24),texture=13)
material('Soil',(.27,.20,.12),texture=15)
material('Grass',(.19,.26,.115),texture=18)
material('Leaf oak',(.16,.28,.075),texture=6)
material('Leaf lime',(.28,.36,.105),texture=6)
material('Leaf pine',(.075,.18,.10),texture=9)
material('Coal',(.035,.04,.045),texture=9)
material('Marking',(.73,.70,.59),.9)
material('Water',(.075,.24,.30),.35)
M['Company teal'].pass_index=1
scene.use_nodes=True
nodes=scene.node_tree.nodes; links=scene.node_tree.links; nodes.clear()
rl=nodes.new('CompositorNodeRLayers'); comp=nodes.new('CompositorNodeComposite'); links.new(rl.outputs['Image'],comp.inputs['Image'])
mask=nodes.new('CompositorNodeIDMask'); mask.index=1; mask.use_antialiasing=True; links.new(rl.outputs['IndexMA'],mask.inputs[0])
maskout=nodes.new('CompositorNodeOutputFile'); maskout.base_path=str(OUT/'masks'); maskout.format.file_format='PNG'; maskout.format.color_mode='BW'; links.new(mask.outputs[0],maskout.inputs[0])

current=None
assets={}
def asset(name):
    global current
    current=bpy.data.collections.new(name); scene.collection.children.link(current); assets[name]=current
    print('ATELIER_BUILD',name,flush=True)
    return current
def attach(obj, name, mat):
    obj.name=name
    for c in list(obj.users_collection): c.objects.unlink(obj)
    current.objects.link(obj)
    if mat: obj.data.materials.append(M[mat])
    return obj
def box(name, loc, size, mat, bevel=.035):
    x,y,z=(s/2 for s in size)
    o=mesh(name,[(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
    o.location=loc
    if bevel:
        mod=o.modifiers.new('Soft manufactured edges','BEVEL'); mod.width=bevel; mod.segments=2
        o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return o
def mesh(name, verts, faces, mat):
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); current.objects.link(o); me.materials.append(M[mat]); return o
def cylinder(name, loc, radius, depth, mat, rotation=(0,0,0), vertices=16):
    vs=[(radius*math.cos(i*math.tau/vertices),radius*math.sin(i*math.tau/vertices),z) for z in (-depth/2,depth/2) for i in range(vertices)]
    fs=[tuple(reversed(range(vertices))),tuple(range(vertices,vertices*2))]+[(i,(i+1)%vertices,(i+1)%vertices+vertices,i+vertices) for i in range(vertices)]
    o=mesh(name,vs,fs,mat); o.location=loc; o.rotation_euler=rotation
    for p in o.data.polygons: p.use_smooth=len(p.vertices)==4
    return o
def ellipsoid(name, loc, scale, mat, seed=0):
    me=bpy.data.meshes.new(name); bm=bmesh.new(); bmesh.ops.create_icosphere(bm,subdivisions=2,radius=1); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(name,me); current.objects.link(o); me.materials.append(M[mat]); o.location=loc; o.scale=scale
    r=random.Random(seed)
    for v in o.data.vertices: v.co *= r.uniform(.88,1.1)
    for p in o.data.polygons: p.use_smooth=True
    return o
def beam(name,a,b,width,mat):
    a,b=Vector(a),Vector(b); o=box(name,(a+b)/2,(width,width,(a-b).length),mat,0)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler(); return o
def roof(x,y,w,d,z,h,mat='Terracotta'):
    x0,x1=x-w/2-.25,x+w/2+.25; y0,y1=y-d/2-.25,y+d/2+.25
    mesh('Gabled roof',[(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z),(x,y0,z+h),(x,y1,z+h)],[(0,1,4),(3,5,2),(0,4,5,3),(1,2,5,4)],mat)
    beam('Ridge cap',(x,y0,z+h+.04),(x,y1,z+h+.04),.14,mat)
    for k in range(1,8):
        t=k/8
        for s in (-1,1): beam('Tile course',(x+s*(w/2+.25)*t,y0,z+h*(1-t)+.025),(x+s*(w/2+.25)*t,y1,z+h*(1-t)+.025),.025,mat)
    for s in (-1,1): beam('Gutter',(x+s*(w/2+.3),y0,z),(x+s*(w/2+.3),y1,z),.09,'Zinc')
def windows(x,y,w,d,floors,spacing=2.1,start=1.4,modern=False):
    for floor in range(floors):
        z=start+floor*2.5
        for axis,length in ((0,w),(1,d)):
            count=max(1,int(length/spacing))
            for i in range(count):
                v=(i-(count-1)/2)*spacing
                for side in (-1,1):
                    loc=(x+v,y+side*(d/2+.025),z) if axis==0 else (x+side*(w/2+.025),y+v,z)
                    sz=(1.12,.12,1.45) if axis==0 else (.12,1.12,1.45)
                    box('Recessed stone frame',loc,sz,'Ivory',.025)
                    loc2=(loc[0],loc[1]+side*.071,loc[2]) if axis==0 else (loc[0]+side*.071,loc[1],loc[2])
                    sz2=(.9,.055,1.16) if axis==0 else (.055,.9,1.16)
                    box('Window glass',loc2,sz2,'Glass pale' if (i+floor)%4==0 else 'Glass',.01)
                    if not modern:
                        sz3=(.055,.06,1.2) if axis==0 else (.06,.055,1.2)
                        box('Window mullion',loc2,sz3,'Ivory',.004)
                    sill=(1.3,.3,.10) if axis==0 else (.3,1.3,.10)
                    box('Sill',(loc[0],loc[1],z-.77),sill,'Limestone',.02)
def chimney(x,y,z):
    box('Brick chimney',(x,y,z+.7),(.6,.65,1.4),'Brick'); box('Chimney cap',(x,y,z+1.43),(.8,.83,.16),'Limestone')
def door(x,y,z=1.1):
    box('Door frame',(x,y,z),(.95,.18,2.0),'Limestone')
    box('Timber door',(x,y+.11,z),(.73,.1,1.8),'Timber')
    box('Door glazing',(x,y+.17,z+.4),(.48,.02,.65),'Glass')
def planter(x,y,z=0):
    box('Planter',(x,y,z+.3),(1.4,.8,.6),'Limestone')
    ellipsoid('Low shrubs',(x,y,z+.65),(.65,.35,.4),'Leaf lime',8)
def bench(x,y,z=0):
    for yy in (-.22,0,.22): box('Bench slat',(x,y+yy,z+.65),(1.8,.16,.12),'Timber')
    for xx in (-.65,.65): box('Bench support',(x+xx,y,z+.32),(.10,.5,.64),'Iron')
    box('Bench back',(x,y-.29,z+1.04),(1.8,.1,.55),'Timber')
def lamp(x,y,z=0):
    cylinder('Lamp post',(x,y,z+2.25),.065,4.5,'Iron',vertices=8)
    beam('Lamp arm',(x,y,z+4.4),(x+.65,y,z+4.4),.08,'Iron')
    box('Lamp housing',(x+.65,y,z+4.35),(.52,.35,.18),'Iron')
    box('Lamp diffuser',(x+.65,y,z+4.24),(.42,.25,.055),'Lamp')

asset('B01_linden_house')
box('Foundation',(8,8,.25),(9.4,8.4,.5),'Limestone')
box('Plaster walls',(8,8,2.9),(9,8,5.3),'Warm plaster')
windows(8,8,9,8,2,2.5,1.55); door(8,12.13)
roof(8,8,9,8,5.55,2.6); chimney(6.1,7,7)
box('Entry steps',(8,12.8,.23),(2.1,1.4,.46),'Limestone'); planter(11.5,13)

asset('B02_orchard_villa')
box('Foundation',(8,7.5,.3),(9.8,9.5,.6),'Limestone')
box('Ochre walls',(8,7.5,2.7),(9.4,9.1,4.8),'Ochre plaster'); windows(8,7.5,9.4,9.1,2,2.7,1.45)
roof(8,7.5,9.4,9.1,5.15,3.0,'Slate'); chimney(6.2,6,7)
box('Bay window',(8,12.5,1.6),(3.0,1.5,2.8),'Ivory'); box('Bay glass',(8,13.28,1.8),(2.6,.05,1.75),'Glass')
roof(8,12.5,3.2,1.7,3.05,.6,'Slate'); door(11.3,12.1); planter(4,12.7)

asset('B03_historic_terrace')
for x,mat in ((4.6,'Warm plaster'),(10.7,'Ochre plaster')):
    box('Terrace plinth',(x,8,.25),(5.9,11.3,.5),'Limestone')
    box('Terrace walls',(x,8,4.1),(5.7,11,7.7),mat); windows(x,8,5.7,11,3,2,1.6)
    for z in (2.7,5.2,7.95): box('Cornice',(x,8,z),(6,11.25,.18),'Limestone')
    roof(x,8,5.9,11.2,8.05,2.5,'Slate'); chimney(x-1.4,6,9.3); door(x+1.1,13.6)

asset('B04_courtyard_apartments')
box('Stone base',(8,8,.38),(13.6,12.6,.76),'Limestone')
box('Apartment masonry',(8,8,5.6),(13,12,10.5),'Warm plaster'); windows(8,8,13,12,4,2.5,1.7)
for z in (3,5.5,8,10.9): box('Floor string course',(8,8,z),(13.4,12.4,.16),'Ivory')
box('Flat roof',(8,8,11),(13.5,12.5,.28),'Slate')
for x in (1.4,14.6): box('Parapet',(x,8,11.4),(.23,12.5,.65),'Limestone')
for y in (1.9,14.1): box('Parapet',(8,y,11.4),(13.4,.23,.65),'Limestone')
box('Stair penthouse',(4,5,12.0),(3.4,3,1.8),'Ivory'); box('Zinc cap',(4,5,12.95),(3.6,3.2,.15),'Zinc')
for x in (5,10):
    for z in (4,6.5,9):
        box('Balcony floor',(x,14.8,z),(2.2,1.5,.16),'Limestone')
        for xx in (-.9,-.3,.3,.9): beam('Balcony rail',(x+xx,15.4,z),(x+xx,15.4,z+.85),.035,'Iron')
        beam('Balcony handrail',(x-1,15.4,z+.85),(x+1,15.4,z+.85),.05,'Iron')
door(8,14.15); planter(2.8,14.9)

asset('B05_riverside_office')
box('Podium',(8,8,1.4),(13.5,12.5,2.8),'Limestone')
box('Curtain wall',(7.5,7.5,7.15),(11.8,10.8,8.8),'Glass pale',.1)
for z in (3.0,5.4,7.8,10.2,11.6): box('Horizontal reveals',(7.5,7.5,z),(12.1,11.1,.2),'Ivory')
for x in (2,4,6,8,10,12,13):
    for y in (2,13): box('Vertical fins',(x,y,7.1),(.13,.35,8.7),'Zinc')
for y in (3,5,7,9,11):
    for x in (1.45,13.55): box('Vertical fins',(x,y,7.1),(.35,.13,8.7),'Zinc')
box('Roof terrace',(7.5,7.5,11.8),(12.4,11.4,.25),'Paving'); box('Service core',(4,5,12.6),(3.5,4,1.6),'Ivory')
for x in (8,10,12):
    o=box('Solar panel',(x,6,12.2),(1.6,3,.1),'Glass'); o.rotation_euler.x=.2
for x in (3,6,9): box('Street glazing',(x,14.29,1.35),(2.5,.05,2.1),'Glass')
box('Entrance canopy',(11.3,14.7,2.6),(4,2,.15),'Zinc'); planter(3,14.8)

asset('B06_corner_cafe')
box('Shop plinth',(8,8,.2),(12.5,11.5,.4),'Limestone')
box('Shop walls',(8,8,4),(12,11,7.5),'Ivory'); windows(8,8,12,11,2,2.4,4.15)
for x in (3.5,7.2,11): box('Shopfront',(x,13.56,1.7),(3.0,.12,2.7),'Glass')
for y in (4.2,8,11.8): box('Shopfront',(14.06,y,1.7),(.12,3.0,2.7),'Glass')
box('Teal fascia',(8,13.7,3.25),(12.3,.25,.5),'Company teal')
o=box('Canvas awning',(8,14.4,2.9),(11.4,1.65,.12),'Company teal'); o.rotation_euler.x=.16
for x in (4,8,12):
    cylinder('Cafe table',(x,15,.8),.48,.08,'Timber')
    cylinder('Table stem',(x,15,.4),.06,.8,'Iron',vertices=8)
roof(8,8,12.3,11.3,7.9,2.7,'Slate'); chimney(4.5,5,9.5)
box('Dormer',(8,11.6,8.6),(2.4,2,1.9),'Ivory'); box('Dormer glass',(8,12.65,8.7),(1.5,.08,1.2),'Glass')
roof(8,11.6,2.4,2,9.6,.6,'Slate')

asset('B07_goods_warehouse')
box('Loading plinth',(8,8,.45),(12.8,12.8,.9),'Paving')
box('Brick hall',(8,7.5,2.8),(12,11,5),'Brick'); windows(8,7.5,12,11,1,3,3.6)
roof(8,7.5,12.4,11.4,5.4,1.5,'Zinc')
for x in (4.2,10.7):
    box('Loading door',(x,13.08,2.1),(3.6,.14,2.6),'Slate')
    for z in (1,1.4,1.8,2.2,2.6,3): box('Roller slat',(x,13.18,z),(3.4,.04,.04),'Steel',0)
box('Dock canopy',(8,13.8,3.6),(12.2,2.7,.2),'Zinc')
for x in (3.5,6.0): box('Cargo crate',(x,14.6,1.2),(1.4,1.1,1.4),'Timber')
box('Roof vent',(8,6,6.9),(2.2,1.6,.65),'Zinc')

def platform(name, rotate=False, station=False, front=False):
    asset(name)
    # Local origin is the draw-part origin, not the complete station tile.
    box('Platform',(8,2.5,.24),(16,5,.48),'Paving',.01)
    box('Platform coping',(8,4.8,.52),(16,.4,.12),'Ivory',.01)
    box('Safety line',(8,4.35,.55),(16,.13,.025),'Marking',0)
    if station:
        box('Station hall',(7,1.8,2.25),(8,3.3,4),'Brick'); windows(7,1.8,8,3.3,1,2,2.1)
        roof(7,1.8,8.3,3.6,4.3,1.3,'Slate')
        box('Station clock',(7,3.58,3.55),(.8,.08,.8),'Ivory')
        beam('Clock hand',(7,3.66,3.55),(7,3.66,3.82),.045,'Iron')
        box('Nameboard',(13,3.2,2.1),(2.4,.14,.55),'Company teal')
        for x in (12,14): beam('Sign post',(x,3.2,.5),(x,3.2,2.4),.07,'Iron')
    else:
        bench(7,2,.5); lamp(13,1,.5); planter(2,1,.5)
    if rotate:
        for o in current.objects:
            o.location.x,o.location.y=o.location.y,o.location.x
            o.rotation_euler.z += math.pi/2
            # A rotation plus translation produces the transposed footprint.
            o.location.x=5-o.location.x
platform('I01_platform_x')
platform('I02_station_x',station=True)
platform('I03_platform_y',rotate=True)
platform('I04_station_y',rotate=True,station=True)

asset('I05_bus_shelter')
for y in (5.5,10.5): beam('Shelter upright',(.5,y,.25),(.5,y,3.1),.09,'Iron')
box('Shelter back',(.5,8,1.7),(.08,5,2.7),'Glass pale')
box('Shelter canopy',(1.4,8,3.15),(2.6,5.5,.2),'Zinc')
box('Bench seat',(1,8,.75),(.7,3,.14),'Timber')
box('Stop pole',(1.2,11.5,1.8),(.09,.09,3.6),'Iron')
box('Bus roundel',(1.2,11.5,3.7),(.12,.7,.7),'Company teal')

def tree(kind, seed=11):
    rng=random.Random(seed); cylinder('Bark trunk',(0,0,2),.25,4,'Timber',vertices=10)
    if kind=='pine':
        for i in range(5):
            bpy.ops.mesh.primitive_cone_add(vertices=16,radius1=2.4-i*.34,radius2=.15,depth=3.5,location=(0,0,3.3+i*1.35))
            o=attach(bpy.context.object,'Needle whorl','Leaf pine')
            for p in o.data.polygons: p.use_smooth=True
    else:
        mat='Leaf oak' if kind=='oak' else 'Leaf lime'
        for i in range(21):
            a=rng.random()*math.tau; r=rng.random()*2.1
            x,y=math.cos(a)*r,math.sin(a)*r; z=4.1+rng.random()*3.2
            beam('Branch',(0,0,2.5),(x,y,z),.09,'Timber')
            ellipsoid('Leaf cluster',(x,y,z),(1.6,1.5,1.8 if kind=='lime' else 1.35),mat,seed+i)
for n,k in (('N01_oak','oak'),('N02_lime','lime'),('N03_pine','pine')):
    asset(n); tree(k)
asset('N04_shrubs'); planter(0,0)
asset('P01_street_furniture'); bench(5,8); lamp(10,8); planter(13,8)

def wheels(length,width,radius=.5):
    for x in (-length*.33,length*.33):
        for y in (-width/2,width/2):
            cylinder('Wheel',(x,y,radius),radius,.2,'Rubber',(math.pi/2,0,0),20)
            cylinder('Wheel hub',(x,y*1.03,radius),radius*.48,.23,'Steel',(math.pi/2,0,0),16)
def chassis(length=10,width=2.7):
    box('Underframe',(0,0,.8),(length,width,.45),'Iron',.06); wheels(length,width)

asset('V01_meridian_diesel')
chassis(10.4,2.65); box('Locomotive sill',(0,0,1.1),(10.8,2.85,.4),'Vehicle cream',.1)
box('Diesel hood',(-1,0,2.1),(7,2.45,1.8),'Company teal',.18)
box('Raised cab',(3,0,2.6),(2.7,2.7,2.8),'Company teal',.16)
for y in (-1.38,1.38):
    box('Cab side glass',(3,y,3.1),(1.8,.05,1.1),'Glass'); box('Cream band',(0,y,1.4),(10,.035,.3),'Vehicle cream',0)
box('Windscreen',(4.39,0,3.1),(.05,2.0,1.1),'Glass')
box('Cab roof',(3,0,4.08),(2.9,2.9,.18),'Zinc',.12)
for x in (-3,-1): cylinder('Cooling fan',(x,0,3.05),.65,.12,'Iron',vertices=24)
for x in (-3.5,-3,-2.5,-2,-1.5,-1,-.5,0,.5):
    for y in (-1.25,1.25): box('Side cooling louvre',(x,y,2.3),(.13,.03,1.05),'Iron',0)
for x in (-5.3,5.3):
    for y in (-.85,.85): cylinder('Buffer',(x,y,.9),.23,.35,'Iron',(0,math.pi/2,0))
for y in (-.85,.85): box('Headlight',(4.44,y,2),(.09,.32,.32),'Lamp')

asset('V02_passenger_coach')
chassis(10.3,2.6); box('Coach body',(0,0,2.0),(10.5,2.8,2.4),'Vehicle cream',.25)
box('Coach roof',(0,0,3.3),(10.6,2.9,.55),'Zinc',.25)
for y in (-1.42,1.42):
    box('Teal waist',(0,y,1.3),(10,.05,.6),'Company teal',0)
    for x in (-4,-2.5,-1,.5,2,3.5): box('Passenger window',(x,y,2.4),(1.1,.05,1.05),'Glass',.08)
for x in (-5.3,5.3): box('Vestibule',(x,0,2),(.15,1.4,1.9),'Iron',.12)

for load in (False,True):
    asset('V03_hopper_loaded' if load else 'V03_hopper_empty'); chassis(9.9,2.7)
    box('Hopper floor',(0,0,1.25),(9.3,2.7,.4),'Iron')
    for y in (-1.4,1.4):
        box('Hopper wall',(0,y,2.05),(9.5,.16,1.6),'Company teal')
        for x in (-4,-2,0,2,4): box('Hopper ribs',(x,y*1.06,2.05),(.13,.15,1.75),'Steel')
    for x in (-4.7,4.7): box('End wall',(x,0,2.05),(.15,2.8,1.6),'Company teal')
    if load:
        for x in (-3.5,-1.8,0,1.8,3.5): ellipsoid('Coal load',(x,0,2.6),(1.3,1.25,.55),'Coal',int(x*10+100))

asset('V04_civic_bus')
chassis(9.4,2.5); box('Bus body',(0,0,1.95),(9.6,2.65,2.55),'Vehicle cream',.32)
box('Bus roof',(0,0,3.29),(9.5,2.6,.24),'Zinc',.18)
for y in (-1.34,1.34):
    box('Livery band',(0,y,1.3),(9.1,.04,.6),'Company teal',0)
    for x in (-3.6,-2.1,-.6,.9,2.4): box('Passenger glass',(x,y,2.45),(1.15,.06,1.05),'Glass',.07)
box('Driver windshield',(4.81,0,2.45),(.04,2.15,1.15),'Glass',.08)
box('Destination panel',(4.83,0,3.13),(.04,1.9,.28),'Iron')
for y in (-.9,.9): box('Headlamps',(4.84,y,1.35),(.07,.35,.3),'Lamp')
box('Passenger doors',(3.7,1.37,1.9),(1.1,.05,2.1),'Glass')

asset('V05_parcel_truck')
chassis(9,2.5); box('Box cargo body',(-1.1,0,2.35),(6.6,2.8,3),'Vehicle cream',.12)
box('Cab',(3.3,0,1.95),(2.7,2.6,2.4),'Company teal',.28)
box('Front glass',(4.67,0,2.45),(.05,2.15,.95),'Glass')
for y in (-1.33,1.33): box('Door glass',(3.4,y,2.45),(1.5,.05,.9),'Glass')
for y in (-1.42,1.42): box('Parcel stripe',(-1.1,y,2.2),(6.4,.04,.45),'Company teal',0)
box('Rear roller door',(-4.43,0,2.3),(.06,2.5,2.6),'Zinc')
for y in (-.9,.9): box('Headlamps',(4.69,y,1.35),(.08,.35,.3),'Lamp')

asset('V06_river_ferry')
verts=[]
for z,w,l in ((.0,2.5,11),(.9,3,12)):
    verts.extend([(-l,-w,z),(l-3,-w,z),(l,0,z),(l-3,w,z),(-l,w,z)])
mesh('Displacement hull',verts,[(0,4,3,2,1),(5,6,7,8,9)]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)],'Company teal')
box('Passenger deck',(-1,0,1.1),(17,5.5,.25),'Timber')
box('Salon',(-2,0,2.4),(12,4.7,2.5),'Vehicle cream',.25)
for y in (-2.4,2.4):
    for x in (-7,-5,-3,-1,1,3): box('Salon window',(x,y,2.6),(1.3,.06,1.3),'Glass',.1)
box('Upper deck',(-2,0,3.8),(12.5,5,.2),'Ivory',.15)
box('Wheelhouse',(3,0,4.6),(3,3.6,1.6),'Vehicle cream',.2)
box('Bridge windscreen',(4.53,0,4.8),(.06,3.1,.9),'Glass')
box('Bridge roof',(3,0,5.5),(3.4,4,.18),'Zinc')
cylinder('Funnel',(-5,0,4.6),.6,1.8,'Company teal')
for x in (-7,-4,-1,2):
    for y in (-2.7,2.7): beam('Deck rail',(x,y,1.2),(x,y,2.05),.045,'Ivory')
for y in (-2.7,2.7): beam('Handrail',(-8,y,2.05),(5,y,2.05),.055,'Ivory')

# Preview components and reusable source kit. Infrastructure integration is
# assembled by the sprite compiler using the exact legacy layouts.
sys.path.insert(0,str(Path(__file__).resolve().parent))
from atelier_corridors import build as build_corridors
build_corridors(globals())
asset('I08_bridge_segment')
box('Concrete deck',(8,8,-.3),(16,12,.6),'Limestone')
box('Carriageway',(8,8,.03),(16,9,.08),'Asphalt',0)
for y in (2.2,13.8):
    box('Bridge parapet',(8,y,.6),(16,.3,1.3),'Limestone')
    for x in range(1,16,2): box('Parapet recess',(x,y+(.16 if y>8 else -.16),.6),(1.1,.035,.65),'Slate',0)
box('Pier',(8,8,-2.5),(2.5,10,4.5),'Limestone')

# Split bridge parts keep vehicles between the deck and the near parapet.
bridge=assets['I08_bridge_segment']
for suffix,selector in [('deck',lambda o:o.name.startswith(('Concrete deck','Carriageway')) or (o.name.startswith(('Bridge parapet','Parapet recess')) and o.location.y<8)),('front',lambda o:o.name.startswith(('Bridge parapet','Parapet recess')) and o.location.y>8),('pier',lambda o:o.name.startswith('Pier'))]:
    for axis in ('x','y'):
        asset('I08_'+suffix+'_'+axis)
        if suffix=='pier':
            # Runtime repeats an 8-unit column at its near-edge draw origin.
            box('Repeatable pier',(8,1,-1.6) if axis=='x' else (1,8,-1.6),(2.5,2,8) if axis=='x' else (2,2.5,8),'Limestone')
            continue
        for src in bridge.objects:
            if selector(src):
                o=src.copy(); o.data=src.data.copy(); current.objects.link(o)
                if axis=='y':
                    o.location.x,o.location.y=o.location.y,o.location.x
                    o.rotation_euler.z+=math.pi/2

for axis in ('x','y'):
    asset('I09_station_canopy_'+axis)
    roof(8,8,15.8,15.8,0,1.6,'Zinc')
    for y in (4,8,12): box('Canopy glazing',(8,y,.65),(10,1.2,.05),'Glass pale',0)

# Camera reproduces the runtime 2:1 isometric ground projection, with exact
# projected origins recorded per render instead of visually guessed offsets.
rig=bpy.data.collections.new('RENDER_RIG'); scene.collection.children.link(rig); current=rig
bpy.ops.object.camera_add(location=(108,108,81.649658))
cam=attach(bpy.context.object,'Isometric 2:1 camera',None)
cam.rotation_euler=(Vector((8,8,0))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO'; cam.data.ortho_scale=96/math.sqrt(8); cam.data.shift_y=.25
scene.camera=cam
for name,loc,power,size in [('Key softbox',(-25,-40,70),40000,35),('Sky fill',(35,20,50),10000,40)]:
    bpy.ops.object.light_add(type='AREA',location=loc); l=attach(bpy.context.object,name,None)
    l.data.energy=power; l.data.shape='DISK'; l.data.size=size
    l.rotation_euler=(Vector((8,8,0))-l.location).to_track_quat('-Z','Y').to_euler()

catalog=[]
for name,c in assets.items():
    c.hide_render=True
    tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in c.objects if o.type=='MESH')
    mats=sorted({m.name for o in c.objects if o.type=='MESH' for m in o.data.materials})
    catalog.append({'id':name,'source_collection':name,'source_triangles':tris,'materials':mats,'objects':len(c.objects),'license':'GPL-2.0-only; original AI-assisted procedural geometry'})
(OUT/'source/catalog.json').write_text(json.dumps(catalog,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'source/atelier-library.blend'))

renders=json.loads((OUT/'renders.json').read_text()) if opt.only and (OUT/'renders.json').exists() else []
for name,c in assets.items():
    if opt.only and not any(fnmatch.fnmatchcase(name,p) for p in opt.only.split(',')): continue
    c.hide_render=False
    vehicle=name.startswith('V')
    directions=8 if vehicle else (4 if name=='I05_bus_shelter' else 1)
    # Both opposite sides are modeled. Four-view symmetric legacy slots use
    # the corresponding four exported directions without synthetic mirroring.
    originals=[(o,o.location.copy(),o.rotation_euler.copy()) for o in c.objects]
    for d in range(directions):
        if vehicle:
            # DIR_N starts along the screen vertical; subsequent views clockwise.
            angle=math.radians(225-d*45)
            from mathutils import Matrix
            rot=Matrix.Rotation(angle,4,'Z')
            for o,loc,euler in originals:
                o.location=rot.to_3x3()@loc+Vector((8,8,0)); o.rotation_euler=(rot.to_3x3()@euler.to_matrix()).to_euler()
        elif name.startswith('N'):
            for o,loc,euler in originals: o.location=loc+Vector((8,8,0))
        elif name=='I05_bus_shelter':
            from mathutils import Matrix
            rot=Matrix.Rotation(d*math.pi/2,4,'Z')
            for o,loc,euler in originals:
                o.location=rot.to_3x3()@(loc-Vector((8,8,0)))+Vector((8,8,0)); o.rotation_euler=(rot.to_3x3()@euler.to_matrix()).to_euler()
        path=OUT/'renders'/f'{name}-{d}.png'; scene.render.filepath=str(path)
        maskout.file_slots[0].path=f'{name}-{d}-'
        bpy.context.view_layer.update()
        anchor=Vector((8,8,0)) if vehicle or name.startswith('N') else Vector((0,0,0))
        p=world_to_camera_view(scene,cam,anchor)
        renders=[r for r in renders if (r['id'],r['direction'])!=(name,d)]
        renders.append({'id':name,'direction':d,'file':path.name,'origin_px':[round(p.x*576),round((1-p.y)*576)],'pixels_per_base_pixel':6})
        bpy.ops.render.render(write_still=True)
        print('ATELIER_RENDER',name,d,flush=True)
    for o,loc,euler in originals: o.location=loc; o.rotation_euler=euler
    c.hide_render=True
(OUT/'renders.json').write_text(json.dumps(renders,indent=2))
print('ATELIER_MODELS_DONE',len(catalog),len(renders),flush=True)
sys.path.insert(0,str(Path(__file__).resolve().parent))
from atelier_gallery import gallery
gallery(OUT/'source/atelier-library.blend')
