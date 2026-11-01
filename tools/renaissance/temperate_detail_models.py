"""Shared transport details and landmarks, with exact native state slots."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
source=(HERE/'temperate_models.py').read_text()
exec(compile(source.split('for job in jobs:')[0],str(HERE/'temperate_models.py'),'exec'),globals())
from temperate_plan import details
jobs=details()
material('Signal green',(.035,.65,.16),.55)
def ribbon(name,points,half,z,mat):
    vs=[]
    for i,(x,y) in enumerate(points):
        a=points[max(0,i-1)];b=points[min(len(points)-1,i+1)];length=math.dist(a,b);nx=-(b[1]-a[1])/length;ny=(b[0]-a[0])/length
        vs.extend([(x+nx*half,y+ny*half,z),(x-nx*half,y-ny*half,z)])
    mesh(name,vs,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(points)-1)],mat)
def arc(cx,cy,a,b):return [(cx+8*math.cos(a+(b-a)*i/24),cy+8*math.sin(a+(b-a)*i/24)) for i in range(25)]
paths=[[(8,0),(8,16)],[(0,8),(16,8)],arc(0,0,0,math.pi/2),arc(16,16,math.pi,1.5*math.pi),arc(0,16,-math.pi/2,0),arc(16,0,math.pi/2,math.pi)]
for job in jobs:
    asset('W_'+job['key'].replace(':','_'));kind=job['kind']
    if kind=='guideway':
        j=job['layout'];family=job['family']
        if not job.get('overlay'):plane('Meadow ground',0,0,16,16,-.03,'Grass')
        slopes={14:1,15:2,22:3,13:4,21:6,17:7,12:8,23:9,18:11,20:12,19:13,16:14}
        s=slopes.get(j)
        indexes=[j] if j<6 else [0,1] if j==6 else [2,3] if j==24 else [4,5] if j==25 else [1 if s in (12,3,8,2,7,13) else 0] if s else []
        for idx in indexes:
            path=paths[idx];ribbon('Guideway slab',path,1.15 if family=='mono' else 2.25,.26,'Pearl concrete')
            if family=='mono':ribbon('Running beam',path,.85,.52,'Steel')
            else:
                for side in (-1,1):
                    shifted=[]
                    for i,(x,y) in enumerate(path):
                        a=path[max(0,i-1)];b=path[min(len(path)-1,i+1)];l=math.dist(a,b)
                        shifted.append((x-(b[1]-a[1])/l*side*1.8,y+(b[0]-a[0])/l*side*1.8))
                    ribbon('Magnetic stator',shifted,.3,.52,'Navy metal')
        if j in slopes:deform(slopes[j])
    elif kind=='signal':
        v=job['variant'];green=v%2;typ=job['signal_type']
        slab('Signal plinth',0,0,.7,.7,0,.18,'Pearl concrete');slab('Signal post',0,0,.15,.15,0,6.4,'Steel')
        if job['semaphore']:
            arm=box('Semaphore blade',(.9,0,5.9),(1.9,.14,.28),'Signal red' if typ!=2 else 'Amber');arm.rotation_euler.y=-math.pi/4 if green else 0
            band=box('Blade white band',(1.25,-.08,5.9),(.3,.03,.3),'Ivory')
            if green:
                r=Matrix.Rotation(-math.pi/4,3,'Y');band.location=r@(band.location-Vector((.9,0,5.9)))+Vector((.9,0,5.9));band.rotation_euler.y=-math.pi/4
        else:
            box('Signal hood',(0,0,5.6),(.65,.4,1.5),'Iron')
            cylinder('Signal lamp',(0,.24,5.9 if not green else 5.2),.18,.05,'Signal green' if green else 'Signal red',(math.pi/2,0,0),vertices=16)
        if typ:
            box('Signal class plate',(0,.10,4.35),(.65,.12,.45),'Ivory' if typ in (1,4) else 'Amber')
            if typ in (3,5):box('Path diagonal marker',(0,.18,4.35),(.12,.025,.42),'Iron').rotation_euler.y=math.pi/4
        rot=Matrix.Rotation(math.radians([0,180,90,270,45,225,135,315][v//2]),4,'Z')
        for o in current.objects:o.location=rot.to_3x3()@o.location;o.rotation_euler=(rot.to_3x3()@o.rotation_euler.to_matrix()).to_euler()
    elif kind=='guide_crossing':
        road(job['axis']);rail('y' if job['axis']=='x' else 'x',family=job['family'])
        for x,y in [(3,3),(13,13)]:
            slab('Crossing pole',x,y,.17,.17,0,2.6,'Steel')
            box('Warning head',(x,y,2.4),(.55,.18,.55),'Signal red' if job['closed'] else 'Iron')
    elif kind=='field_fence':
        v=job['variant'];group=v//6;hedge=group in (0,1,3,4);stone=group==5
        if hedge:
            for y in range(0,17,2):
                if group==1 and 6<=y<=10:continue
                ellipsoid('Living field hedge',(16,y,.7),(.55,1.1,.9),'Leaf oak',y)
                if group in (3,4):ellipsoid('Hedge blossoms',(15.8,y,1.35),(.27,.45,.2),'Amber' if group==3 else 'Signal red',y)
            if group==1:
                for z in (.45,1):beam('Field gate rail',(16,6,z),(16,10,z),.08,'Timber')
        elif stone:slab('Field dry stone wall',16,8,.6,16,0,1.1,'Limestone')
        else:
            for y in (0,4,8,12,16):slab('Field fence post',16,y,.16,.16,0,1.2,'Timber')
            for z in (.4,1):beam('Field fence rail',(16,0,z),(16,16,z),.08,'Timber')
        if v%2:transpose()
        if v%6>=2:
            deform([9,12,6,3][v%6-2])
            if v%6>=4:
                for o in current.objects:o.location.z-=8/Z
    elif kind=='landmark':
        sid=job['variant']
        if sid==2601:
            for x,y in [(7,7),(9,7),(7,9),(9,9)]:beam('Transmitter lattice leg',(x,y,0),(8,8,20),.18,'Steel')
            for z in range(1,20,2):beam('Lattice cross brace',(7.4,7.4,z),(8.6,8.6,z+1),.10,'Signal red')
            cylinder('Broadcast dish',(8,8,13),1.1,.15,'Ivory',(math.pi/2,0,0),vertices=24)
        elif sid==2602:
            cylinder('Lighthouse tower',(8,8,6),2.5,12,'Ivory',vertices=24)
            for z in (3,8):cylinder('Tower red band',(8,8,z),2.51,1.1,'Signal red',vertices=24)
            cylinder('Lantern gallery',(8,8,12.1),3.1,.25,'Iron',vertices=24);cylinder('Lantern room',(8,8,13.2),1.9,2,'Glass pale',vertices=24);cylinder('Lantern roof',(8,8,14.3),2.3,.3,'Navy metal',vertices=24)
        elif sid==2632:
            slab('Monument plinth',8,8,4,4,0,1.3,'Limestone');slab('Company dedication plaque',8,10.02,2,.04,.5,.5,'Company teal')
            cylinder('Bronze column',(8,8,2.5),.6,2.5,'Iron',vertices=12);ellipsoid('Monument crown',(8,8,4.1),(.7,.7,.85),'Iron',3)
        elif sid==4790:
            slab('Owned land marker post',8,8,.14,.14,0,1.7,'Timber');box('Company land sign',(8,8,1.6),(1.4,.15,.75),'Company teal')
        else:
            ground_only=sid in (2611,2613,2615,2618,2620,2622,2625,2627,2629)
            if ground_only:plane('Headquarters court',0,0,16,16,.02,'Paving R3');planter(8,8)
            else:
                floors=1 if sid<2607 else 2 if sid<2611 else 3 if sid<2618 else 5 if sid<2625 else 7
                slab('Headquarters block',8,8,12,12,0,floors*2.4,'Warm plaster');windows(8,8,12,12,floors,2.5,1.4,modern=True)
                slab('Headquarters roof',8,8,12.5,12.5,floors*2.4,.3,'Navy metal');slab('Company colour fascia',8,14.1,11.5,.10,2.4,.45,'Company teal')
    elif kind=='dock':
        v=job['variant'];slab('Landing pier',8,8,16,7.7,0,.45,'Pearl concrete')
        for y in (4.3,11.7):
            for x in (1,7,14):cylinder('Mooring bollard',(x,y,.65),.17,.4,'Iron',vertices=12)
            beam('Pier rail',(0,y,1.3),(16,y,1.3),.07,'Steel')
        for x in (2,14):slab('Pier pile',x,8,.65,6,-3,3,'Limestone')
        if v%2:transpose()
        if v<4:deform([12,9,3,6][v])
    elif kind=='buoy':
        cylinder('Buoy float',(0,0,.25),1.2,.5,'Signal red',vertices=24);cylinder('Buoy tower',(0,0,1.25),.22,2,'Steel',vertices=12);box('Navigation marker',(0,0,2.3),(.7,.15,.8),'Signal red')
    elif kind=='roadworks':
        for x in (3,8,13):
            slab('Roadworks barrier foot',x,8,.6,1.2,0,.12,'Iron');slab('Striped roadwork board',x,8,2.3,.15,.6,.6,'Ivory')
            for dx in (-.7,.2):box('Amber warning stripe',(x+dx,8.09,.9),(.4,.03,.65),'Amber')
    elif kind=='waypoint':
        v=job['variant'];y=2 if v%2==0 else 14
        slab('Waypoint platform',8,y,16,3.4,0,.24,'Pearl concrete')
        for x in (2,14):
            slab('Waypoint marker post',x,y,.15,.15,0,3.8,'Steel');box('Company waypoint sign',(x,y,3.6),(2,.15,.65),'Company teal')
        if v>=2:transpose()
    elif kind=='helipad':
        for x in (5.5,10.5):slab('Helipad H',x,8,.5,7,.04,.02,'Marking')
        slab('Helipad crossbar',8,8,5,.5,.04,.02,'Marking')
    current['native_sprite']=job['key'];current['category']=job['category'];current.asset_mark()

tail=source.split('# Reuse the same lights')[1].replace('temperate-infrastructure.blend','temperate-details.blend').replace('infrastructure-plan.json','details-plan.json')
exec(compile('# Reuse the same lights'+tail,str(HERE/'temperate_models.py'),'exec'),globals())
