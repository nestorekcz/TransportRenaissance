"""Editable infrastructure for the temperate world, rendered from actual meshes.
Run in Blender with -- --output artifacts/atelier-temperate --samples 16.
"""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
# Reuse the existing material/primitive rig without rebuilding approved assets.
common=(HERE/'atelier_models.py').read_text()
exec(compile(common.split("asset('B01_linden_house')")[0],str(HERE/'atelier_models.py'),'exec'),globals())
from temperate_plan import infrastructure
from mathutils import Matrix
jobs=infrastructure()
material('Pearl concrete',(.62,.60,.53),texture=24)
material('Navy metal',(.035,.085,.13),.64,.25)
material('Amber',(.64,.36,.09),.75)
material('Road R3',(.105,.12,.125),texture=48)
material('Paving R3',(.47,.455,.40),texture=30)
material('Ballast R3',(.32,.32,.285),texture=30)
material('Rail R3',(.31,.35,.34),.48,.5)
material('Rust R3',(.205,.135,.085),.85)
material('Sleepers R3',(.19,.135,.085),texture=24)
Z=math.sqrt(6)

def slab(name,x,y,w,d,z,h,mat): return box(name,(x,y,z+h/2),(w,d,h),mat,.015)
def plane(name,x0,y0,x1,y1,z,mat): return mesh(name,[(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)],[(0,1,2,3)],mat)
def rotate(angle):
    rot=Matrix.Rotation(math.radians(angle),4,'Z'); center=Vector((8,8,0))
    for o in current.objects:
        o.location=rot.to_3x3()@(o.location-center)+center
        o.rotation_euler=(rot.to_3x3()@o.rotation_euler.to_matrix()).to_euler()
def transpose(objects=None):
    # Reflect the entire mesh in x=y, including transformed local mesh vertices.
    for o in current.objects if objects is None else objects:
        mat=Matrix.Translation(o.location) @ o.rotation_euler.to_matrix().to_4x4() @ Matrix.Diagonal((*o.scale,1))
        for v in o.data.vertices:
            q=mat@v.co; v.co=(q.y,q.x,q.z)
        o.matrix_world=Matrix.Identity(4)
        for face in o.data.polygons: pass
        bm=bmesh.new(); bm.from_mesh(o.data); bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
def height(x,y,s):
    if s==0:return 0
    if s==12:return (16-x)/2
    if s==6:return y/2
    if s==3:return x/2
    if s==9:return (16-y)/2
    if s==8:return max(0,(16-x-y)/2)
    if s==4:return max(0,(y-x)/2)
    if s==2:return max(0,(x+y-16)/2)
    if s==1:return max(0,(x-y)/2)
    if s==13:return 8-max(0,(x+y-16)/2)
    if s==14:return 8-max(0,(x-y)/2)
    if s==7:return 8-max(0,(16-x-y)/2)
    if s==11:return 8-max(0,(y-x)/2)
    return 0
def deform(slope):
    for o in current.objects:
        mat=Matrix.Translation(o.location) @ o.rotation_euler.to_matrix().to_4x4() @ Matrix.Diagonal((*o.scale,1))
        for v in o.data.vertices:
            q=mat@v.co; q.z+=height(q.x,q.y,slope)/Z; v.co=q
        o.matrix_world=Matrix.Identity(4)
def road(axis='x',z=0,wide=True):
    previous=set(current.objects)
    # The same 9.8-unit carriageway and 3.1-unit pavements as the revised road.
    plane('Continuous asphalt',0,0,16,16,z+.025,'Road R3')
    for y in (1.55,14.45):
        slab('Stone pavement',8,y,16,3.1,z,.14,'Paving R3')
        slab('Kerb',8,3.1 if y<8 else 12.9,16,.21,z,.18,'Pearl concrete')
        for x in range(0,17,2): slab('Paver joint',x,y,.023,2.9,z+.142,.01,'Gravel')
    for x in (1,5,9,13): slab('Centre dash',x+.9,8,1.8,.13,z+.035,.008,'Marking')
    if axis=='y': transpose([o for o in current.objects if o not in previous])
def rail(axis='x',z=0,family='rail',full=False):
    previous=set(current.objects)
    if full: plane('Meadow ground',0,0,16,16,z-.04,'Grass')
    if family=='rail':
        slab('Ballast shoulder',8,8,16,6.1,z,.12,'Ballast R3')
        for j in range(15):
            x=j*1.05+.5; slab('Timber sleeper',x,8,.32,4.25,z+.12,.17,'Sleepers R3')
            for y in (6.96,9.04):
                for dy in (-.18,.18): slab('Rail fastening',x,y+dy,.18,.12,z+.28,.08,'Iron')
        for y in (6.96,9.04):
            slab('Oxidised rail foot',8,y,16,.30,z+.26,.06,'Rust R3')
            slab('Rail web',8,y,16,.09,z+.31,.11,'Rust R3')
            slab('Steel running surface',8,y,16,.17,z+.42,.07,'Rail R3')
    elif family=='mono':
        slab('Monorail guideway',8,8,16,2.1,z,.52,'Pearl concrete')
        for y in (7.05,8.95): slab('Guide rail',8,y,16,.12,z+.52,.08,'Rail R3')
    else:
        slab('Maglev guide bed',8,8,16,4.4,z,.22,'Pearl concrete')
        for y in (6.15,9.85): slab('Maglev stator',8,y,16,.65,z+.22,.3,'Navy metal')
    if axis=='y': transpose([o for o in current.objects if o not in previous])

def depot(job):
    family,part=job['family'],job['part']; x0,x1=(2.2,13.8) if family=='rail' else (1.2,14.8)
    y0,y1=1.4,14.7; h=6.4 if family=='rail' else 5.7
    if part in ('rear','all'):
        slab('Far workshop wall',x0,8,.4,13.2,0,h,'Brick' if family=='rail' else 'Warm plaster')
        for y in (4,7,10):box('Clerestory far',(x0-.22,y,h-1.4),(.06,1.8,.8),'Glass pale',.01)
    if part in ('front','all'):
        slab('Near workshop wall',x1,8,.42,13.2,0,h,'Brick' if family=='rail' else 'Warm plaster')
        slab('Rear wall',8,y0,x1-x0,.4,0,h,'Brick')
        for y in (4,7,10):
            box('Workshop stone frame',(x1+.23,y,3.2),(.09,1.9,1.25),'Pearl concrete')
            box('Workshop glass',(x1+.29,y,3.2),(.04,1.6,1.0),'Glass')
        for x in (x0+.6,x1-.6): slab('Portal pier',x,y1,1.15,.45,0,h,'Pearl concrete')
        slab('Open vehicle portal lintel',8,y1,x1-x0,.6,h-1,1,'Pearl concrete')
        box('Company fascia',(8,y1+.32,h-.45),(x1-x0-2,.06,.45),'Company teal')
        roof(8,8,x1-x0+.2,13.8,h,1.8,'Slate' if family=='rail' else 'Zinc')
        for x in (5.5,10.5): box('Roof skylight',(x,8,h+1.15),(1.15,5.1,.13),'Glass pale')
        for y in (4,11):cylinder('Roof vent',(8,y,h+2.02),.25,.45,'Zinc',vertices=12)
    rotate(job['angle'])

def stop_ground(job):
    plane('Paved apron',0,0,16,16,0,'Paving R3')
    plane('Truck turning area',0,2.7,12.9,13.1,.025,'Road R3')
    for y in (4.2,11.8):slab('Loading lane edge',6.5,y,10.8,.12,.036,.012,'Marking')
    for y in (5.4,10.6):slab('Dock bay stripe',10.9,y,2.1,.12,.036,.012,'Amber')
    rotate(job['angle'])

def stop(job):
    mode,part=job['mode'],job['part']
    if part==1:
        if mode=='cargo':
            slab('Loading building plinth',14.35,8,3.05,15.7,0,.45,'Pearl concrete')
            slab('Freight office and warehouse',14.4,8,2.85,15.5,.45,3.8,'Warm plaster')
            slab('Navy roof fascia',14.4,8,3.1,15.8,4.1,.28,'Navy metal')
            slab('Standing seam roof',14.4,8,3.05,15.8,4.38,.16,'Zinc')
            for y in (4.8,9.4):
                box('Loading door',(12.93,y,2.0),(.045,2.8,2.8),'Navy metal')
                for z in (1,1.5,2,2.5,3):box('Roller shutter slat',(12.90,y,z),(.055,2.65,.045),'Steel',0)
                slab('Dock canopy',12.2,y,1.6,3.2,3.6,.16,'Navy metal')
                box('Rubber dock bumper',(12.86,y,.73),(.2,2.7,.45),'Rubber')
            box('Office glazing',(12.9,13.5,2.5),(.07,1.5,1.2),'Glass pale')
            for y in (1.4,14.7):slab('Safety bollard',12.4,y,.18,.18,0,1.05,'Amber')
            box('Dispatch sign',(12.89,7.1,3.8),(.08,2.4,.45),'Company teal')
            box('Roof ventilator',(14.4,5,4.7),(1.1,1.5,.36),'Steel')
        else:
            slab('Ticket office',14.4,11.7,2.8,5.6,0,3.5,'Warm plaster')
            box('Ticket window',(12.95,11.8,2.1),(.06,2.5,1.2),'Glass')
            slab('Passenger shelter roof',14.0,6,3.7,7,3.25,.18,'Navy metal')
            for y in (3,9):slab('Canopy column',12.5,y,.1,.1,0,3.3,'Steel')
            box('Passenger bench',(14.2,5.8,.7),(.65,3.6,.16),'Timber')
            slab('Office roof',14.4,11.7,3.1,6.0,3.5,.2,'Zinc')
    else:
        y=(15.1 if part==0 else .7) if mode=='cargo' else (.7 if part==0 else 14.5)
        slab('Low boundary wall',7,y,11,.3,0,.6,'Pearl concrete')
        if mode=='cargo':
            for x in (4,6,8):
                slab('Pallet',x,y,1.3,.8,.05,.12,'Timber')
                slab('Crated cargo',x,y,1.1,.72,.17,.6+(x%3)*.16,'Timber')
        elif part==0:
            lamp(3,y); box('Bus stop marker',(3.1,y,2.65),(.55,.18,.65),'Company teal')
    rotate(job['angle'])

def bridge(job):
    axis,part,style,family=job['axis'],job['part'],job['style'],job['family']
    ramp,elevated=job['ramp'],job['elevated']; z=0 if ramp else 8/Z if elevated else 3/Z
    mat='Timber' if style=='timber' else 'Navy metal' if style in ('cantilever','tubular','arch') else 'Pearl concrete'
    if part=='pillar':
        # The engine repeats pillar slices every eight vertical pixels.
        slab('Pier slice',8,1.1,2.6,2.1,-8/Z,8/Z,'Pearl concrete')
        for y in (.2,2):slab('Pier recessed edge',8,y,1.65,.08,-8/Z,8/Z,'Limestone')
    else:
        if part=='deck':
            slab('Structural deck',8,8,16,12.1,z-.6,.6,mat)
            if family=='road':
                plane('Bridge asphalt',0,3.1,16,12.9,z+.025,'Road R3')
                for y in (2.55,13.45):slab('Bridge pavement',8,y,16,1.1,z,.14,'Paving R3')
                for x in (1,5,9,13):slab('Continuous centre dash',x+.9,8,1.8,.13,z+.035,.01,'Marking')
                for y in (3.1,12.9):slab('Bridge kerb',8,y,16,.21,z,.18,'Pearl concrete')
            else: rail(z=z,family=family)
        sides=(2.05,13.95) if ramp or elevated else ((2.05,) if part=='deck' else (13.95,))
        for y in sides:
            slab('Parapet footing',8,y,16,.32,z,.45,mat)
            slab('Continuous top rail',8,y,16,.16,z+1.2,.12,mat)
            for x in (0,2,4,6,8,10,12,14,16): slab('Parapet post',x,y,.12,.14,z+.45,.8,mat)
            if style in ('arch','cantilever','tubular') and not (ramp or elevated):
                h=5.2 if style!='arch' else 4.2
                for i in range(4):
                    a=i*4;b=a+4
                    beam('Truss diagonal',(a,y,z+1),(b,y,z+h),.20,mat)
                    beam('Truss counter diagonal',(a,y,z+h),(b,y,z+1),.16,mat)
                beam('Truss chord',(0,y,z+h),(16,y,z+h),.28,mat)
                if style=='tubular':beam('Tube upper edge',(0,y,z+h+.65),(16,y,z+h+.65),.5,mat)
            if style=='suspension' and not (ramp or elevated):
                for x in (1,15):slab('Suspension tower',x,y,.5,.6,z,9,'Pearl concrete')
                pts=[(x,y,z+4+((x-8)/8)**2*4) for x in range(17)]
                for a,b in zip(pts,pts[1:]):beam('Main suspension cable',a,b,.12,'Navy metal')
                for x in range(2,16,2):beam('Cable hanger',(x,y,z+1),(x,y,z+4+((x-8)/8)**2*4),.065,'Steel')
        if ramp or elevated:
            for y in (2.05,13.95):slab('Abutment wall',8,y,16,.5,-.8,z+.8, 'Pearl concrete')
    if axis=='y':transpose()
    if ramp:deform(job['slope'])

def drive_stop(job):
    # Native through stops have one three-unit strip on either side of the road.
    layout=job['layout']; cargo=job['mode']=='cargo'
    x=14.4 if layout==0 else 1.6 if layout==1 else 8
    y=8 if layout<2 else 1.6 if layout==2 else 14.4
    w,d=(2.8,12.5) if layout<2 else (12.5,2.8)
    if cargo:
        slab('Roadside freight office',x,y,w,d,0,3.5,'Warm plaster')
        slab('Freight roof',x,y,w+.2,d+.2,3.5,.2,'Navy metal')
        for t in (-3,0,3):
            loc=(x+(-1.43 if x>8 else 1.43),y+t,1.8) if layout<2 else (x+t,y+(1.43 if y<8 else -1.43),1.8)
            box('Loading shutter',loc,(.05,2.2,2.6) if layout<2 else (2.2,.05,2.6),'Navy metal')
    else:
        slab('Shelter roof',x,y,w,d,3.2,.2,'Zinc')
        for t in (-5,5):slab('Shelter post',x if layout<2 else x+t,y+t if layout<2 else y,.12,.12,0,3.2,'Steel')
        box('Passenger seating',(x,y,.75),(1,7,.15) if layout<2 else (7,1,.15),'Timber')

def tunnel(job):
    # Entrance at x=0; split far approach and near portal at native layers.
    if job['part']==0:
        plane('Tunnel darkness',0,3.2,.5,12.8,0,'Iron')
        if job['family']=='road':road()
        else:rail(family=job['family'])
        slab('Tunnel dark interior',1.5,8,.2,9.5,0,3.6,'Iron')
    else:
        for y in (2.5,13.5):slab('Portal buttress',2.3,y,3.6,1.8,0,4.2,'Pearl concrete')
        slab('Portal lintel',2.3,8,3.6,12.8,3.7,.9,'Pearl concrete')
        for y in (3.6,12.4):slab('Portal inner lining',3.4,y,2.4,.25,0,3.8,'Limestone')
        slab('Grass over portal',.9,8,1.7,16,4.6,.12,'Grass')
    rotate(job['angle'])

for job in jobs:
    name='W_'+job['key'].replace(':','_'); asset(name)
    kind=job['kind']
    if kind=='depot':depot(job)
    elif kind=='stop':stop(job)
    elif kind=='stop_ground':stop_ground(job)
    elif kind=='drive_stop':drive_stop(job)
    elif kind=='bridge':bridge(job)
    elif kind=='road_slope':road(job['axis']);deform(job['slope'])
    elif kind=='rail_slope':
        s=job['slope'];axis='x' if s in (12,3,8,2,7,13) else 'y'
        rail(axis,full=True);deform(s)
    elif kind=='rail_fence':
        v=job['variant'];axis='x' if v%2==0 else 'y'
        for x in (0,4,8,12,16):slab('Boundary post',x,0,.12,.12,0,1.2,'Timber')
        for z in (.45,1):beam('Fence wire',(0,0,z),(16,0,z),.045,'Iron')
        if axis=='y':transpose()
        if v>=4:deform([3,6,12,9][v-4])
    elif kind=='crossing':
        road(job['axis']);rail('y' if job['axis']=='x' else 'x')
        # The engine selects the existing off/on slots; closed has red lamps.
        for x,y in [(3,3),(13,13)]:
            slab('Crossing pole',x,y,.17,.17,0,2.6,'Steel')
            box('Warning head',(x,y,2.4),(.55,.18,.55),'Iron')
            box('Crossing light',(x,y+.10,2.4),(.27,.05,.27),'Signal red' if job['closed'] else 'Rubber')
    elif kind=='streetlight':lamp(0,0);rotate(job['angle'])
    elif kind=='tunnel':tunnel(job)
    elif kind=='ship_depot':
        v=job['variant'];front=v<2;rear=v>=4;axis='x' if v%2==0 else 'y'
        if front:slab('Boathouse near wall',8,14,16,.45,0,5.5,'Warm plaster');roof(8,8,15.8,13,5.5,2,'Zinc')
        elif rear:slab('Boathouse far wall',8,2,16,.45,0,5.5,'Warm plaster')
        else:
            for y in (2,14):slab('Boathouse wall',8,y,16,.45,0,5.5,'Warm plaster')
            slab('Boathouse rear',1,8,.45,12,0,5.5,'Warm plaster');roof(8,8,15.8,13,5.5,2,'Zinc')
        if axis=='y':transpose()
    else:raise ValueError(kind)
    current['native_sprite']=job['key'];current['category']=job['category'];current.asset_mark()

# Reuse the same lights and exact camera as the approved house source.
rig_code=common.split('# Camera reproduces the runtime')[1].split('catalog=[]')[0]
exec(compile('# Camera reproduces the runtime'+rig_code,str(HERE/'atelier_models.py'),'exec'),globals())
catalog=[]
for name,c in assets.items():
    c.hide_render=True
    catalog.append({'id':name,'objects':len(c.objects),'source_triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in c.objects if o.type=='MESH')})
(OUT/'source/catalog.json').write_text(json.dumps(catalog,indent=2))
(OUT/'infrastructure-plan.json').write_text(json.dumps(jobs,indent=2))
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'source/temperate-infrastructure.blend'))
renders=json.loads((OUT/'renders.json').read_text()) if (OUT/'renders.json').exists() else []
for name,c in assets.items():
    if opt.only and not any(fnmatch.fnmatchcase(name,p) for p in opt.only.split(',')):continue
    path=OUT/'renders'/f'{name}.png'
    # Completed individual bakes can be resumed after an interruption.
    if path.exists() and any(r['id']==name for r in renders):continue
    cam.data.shift_y=.33 if name=='W_1442' else .25
    c.hide_render=False;scene.render.filepath=str(path);maskout.file_slots[0].path=name+'-'
    bpy.context.view_layer.update();p=world_to_camera_view(scene,cam,Vector((0,0,0)))
    bpy.ops.render.render(write_still=True)
    renders=[r for r in renders if r['id']!=name]
    renders.append({'id':name,'direction':0,'file':path.name,'origin_px':[round(p.x*576),round((1-p.y)*576)],'pixels_per_base_pixel':6})
    (OUT/'renders.json').write_text(json.dumps(renders,indent=2));c.hide_render=True
    print('TEMPERATE_RENDER',name,flush=True)
print('TEMPERATE_MODELS_DONE',len(catalog),len(renders),flush=True)
