"""Town, industry, airport and vegetation model batch for the temperate world."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
source=(HERE/'temperate_models.py').read_text()
exec(compile(source.split('for job in jobs:')[0],str(HERE/'temperate_models.py'),'exec'),globals())
from temperate_plan import world
jobs=world()

def construction(job):
    stage=job.get('stage',3)
    if stage>=2:return
    # Edit actual geometry: unfinished masonry and external scaffolding.
    maxz=1.0 if stage==0 else 3.5
    for o in list(current.objects):
        mat=Matrix.Translation(o.location) @ o.rotation_euler.to_matrix().to_4x4() @ Matrix.Diagonal((*o.scale,1))
        centre=sum((mat@v.co).z for v in o.data.vertices)/max(1,len(o.data.vertices))
        if centre>maxz:bpy.data.objects.remove(o,do_unlink=True)
    x,y=job.get('anchor',(0,0));w,d,*_=job.get('bounds',(14,14,30))
    for xx in (x,x+w):
        for yy in (y,y+d):slab('Construction scaffold',xx,yy,.13,.13,0,maxz+.8,'Timber')
    for yy in (y,y+d):beam('Scaffold rail',(x,yy,maxz+.6),(x+w,yy,maxz+.6),.1,'Timber')

def town(job):
    name=job['name'];sid=job['sprite_id'];ax,ay=job['anchor'];bw,bd,bh=job['bounds']
    w=max(3,min(14,bw));d=max(3,min(14,bd));x=ax+w/2;y=ay+d/2
    style=job['house_id'];mat=['Warm plaster','Brick','Ochre plaster','Ivory'][style%4]
    if 'PARK' in name:
        for xx,yy in ((4,5),(11,9)):
            cylinder('Tree trunk',(xx,yy,1.9),.2,3.8,'Timber')
            ellipsoid('Garden tree canopy',(xx,yy,4.1),(2.4,2.5,2.8),'Leaf lime',style+int(xx))
        bench(9,4);planter(3,12);return
    if 'FOUNTAIN' in name or 'STATUE' in name:
        cylinder('Civic stone basin',(8,8,.35),3.1,.7,'Limestone',vertices=32)
        cylinder('Fountain water',(8,8,.72),2.75,.05,'Water',vertices=32)
        cylinder('Sculpture pedestal',(8,8,1.2),.7,1.1,'Ivory')
        if 'STATUE' in name:
            cylinder('Abstract bronze monument',(8,8,2.7),.45,2.0,'Iron',vertices=8)
            ellipsoid('Sculpted crown',(8,8,3.9),(.6,.6,.65),'Iron',1)
        else:
            cylinder('Upper fountain bowl',(8,8,1.8),1.3,.23,'Ivory',vertices=24)
            beam('Water jet',(8,8,1.9),(8,8,3),.11,'Glass pale')
        return
    if 'STADIUM' in name:
        part=job['part'];side=1.4 if part%2==0 else 14.6
        for k in range(5):slab('Spectator terrace',8,side+(k*.5 if side<8 else -k*.5),16,.5,k*.3,.3,'Pearl concrete')
        for x0 in (2,6,10,14):beam('Stadium canopy mast',(x0,side,0),(x0,side,4.5),.13,'Steel')
        slab('Grandstand roof',8,side,16,4.2,4.5,.17,'Zinc')
        return
    if 'CHURCH' in name:
        slab('Church nave',8,8,8.5,12,0,6,'Limestone');roof(8,8,8.8,12.3,6,3,'Slate')
        slab('Bell tower',5,4,3.4,3.5,0,11,'Limestone');roof(5,4,3.8,3.9,11,3.8,'Slate')
        windows(8,8,8.5,12,1,3,3.6);door(8,14.12)
        for z in (3,6,9):box('Tower stone course',(5,4,z),(3.6,3.7,.16),'Ivory')
        return
    if any(v in name for v in ('CINEMA','THEATER')):
        slab('Civic auditorium',8,7,12.8,11.8,0,6.8,'Brick');slab('Auditorium roof',8,7,13.2,12.2,6.8,.5,'Slate')
        for xx in (4,8,12):slab('Entrance pilaster',xx,13,1,1,0,5.9,'Ivory');box('Entrance doors',(xx,13.58,1.6),(2,.08,2.8),'Glass')
        slab('Theatre marquee',8,14,13.5,2.5,4.2,.3,'Navy metal');box('Marquee fascia',(8,15.3,4.35),(12,.08,.55),'Amber')
        return
    small=any(v in name for v in ('HOUSE','COTTAGE'))
    floors=2 if small else 3 if 'FLATS' in name else 4 if 'HOTEL' in name else 6 if 'TALL' in name else 4
    if not small:floors=max(2,floors+(style%3)-1)
    if 'WAREHOUSE' in name:floors=1
    floors=min(floors,max(1,int(bh/Z/2.5))) if bh>8 else floors
    if style==4:floors=7
    h=floors*2.5+.4
    slab('Stone plinth',x,y,w+.15,d+.15,0,.35,'Limestone')
    slab('Main building',x,y,w,d,.35,h,mat)
    windows(x,y,w,d,floors,2.3,1.6,modern=not small)
    if 'FLATS' in name:
        for z in range(1,floors):
            for xx in (x-w*.27,x+w*.27):
                slab('Apartment balcony',xx,y+d/2+.45,w*.32,1.1,z*2.5+.5,.14,'Limestone')
                slab('Balcony balustrade',xx,y+d/2+.98,w*.32,.09,z*2.5+.65,.65,'Navy metal')
    if 'HOTEL' in name:
        for xx in (x-w/2+.2,x+w/2-.2):slab('Hotel facade pilaster',xx,y+d/2+.08,.42,.24,.35,h,'Ivory')
        cylinder('Hotel corner pavilion',(x-w*.25,y-d*.23,h+1.1),min(w,d)*.23,1.6,'Warm plaster',vertices=24)
        cylinder('Pavilion cap',(x-w*.25,y-d*.23,h+2),min(w,d)*.25,.25,'Zinc',vertices=24)
    if small or ('FLATS' in name and style%2) or ('OFFICE' in name and style%3==0):
        roof(x,y,w,d,h+.35,2.4,'Slate' if style%2 else 'Terracotta');chimney(x-2,y,h+1.3)
    else:
        slab('Roof parapet',x,y,w+.3,d+.3,h+.35,.28,'Ivory');slab('Flat roof membrane',x,y,w-.5,d-.5,h+.63,.05,'Slate')
        for xx in (-1.5,1.5):box('Roof plant',(x+xx,y,h+.95),(1.5,2,.6),'Zinc')
        for z in range(1,floors):box('Storey cornice',(x,y,z*2.5+.35),(w+.13,d+.13,.12),'Limestone')
    if 'SHOPS' in name or 'MALL' in name or 'HOTEL' in name:
        for xx in (x-w*.27,x+w*.27):box('Ground floor storefront',(xx,y+d/2+.08,1.4),(w*.37,.08,2.0),'Glass')
        slab('Street awning',x,y+d/2+.55,w+.3,1.4,2.6,.17,'Navy metal')
    door(x,y+d/2+.15)

def industry(job):
    family=job['family'];v=job['variant'];x0,y0=job['anchor'];w,d,h=job['bounds'];w=min(15,max(3,w));d=min(15,max(3,d));x=x0+w/2;y=y0+d/2
    if family in ('coal-mine','forest') and (v in (2,3,4,5) or family=='forest'):
        if family=='forest':
            if v==4:
                for yy in range(4,13,2):
                    for z in (0.4,1.05):cylinder('Harvested timber',(8,yy,z),.33,10,'Timber',(0,math.pi/2,0),vertices=12)
            else:
                scale=[.3,.5,.8,1][v]
                for tx,ty in ((3,4),(8,3),(13,5),(5,11),(11,12)):
                    cylinder('Forest tree trunk',(tx,ty,3.8*scale),.22*scale,7.6*scale,'Timber',vertices=10)
                    for k in range(4):ellipsoid('Conifer crown',(tx,ty,(4+k*1.3)*scale),((2-k*.35)*scale,(2-k*.35)*scale,1.6*scale),'Leaf pine',17+v*3+k)
        else:
            for a,b in [(3,3),(12,3),(3,12),(12,12)]:beam('Winding tower leg',(a,b,0),(6+(a>8)*3,6+(b>8)*3,10),.32,'Iron')
            slab('Headframe deck',7.5,7.5,5,5,8,.3,'Steel')
            cylinder('Winding wheel',(7.5,7.5,10),1.6,.2,'Navy metal',(math.pi/2,0,0),vertices=24)
            for a in range(8):
                t=a*math.pi/4+(v-2)*math.pi/8;beam('Wheel spoke',(7.5,7.5,10),(7.5+1.5*math.cos(t),7.5,10+1.5*math.sin(t)),.09,'Steel')
        return
    if family=='power-plant' and v>=4:
        # Curved cooling-tower shell, with an open dark mouth.
        verts=[];faces=[]
        for z,r in [(0,5.7),(2,4.9),(5,3.7),(8,3.1),(11,3.5),(12,4)]:
            for k in range(32):verts.append((8+r*math.cos(k*math.tau/32),8+r*math.sin(k*math.tau/32),z))
        for j in range(5):
            for k in range(32):faces.append((j*32+k,j*32+(k+1)%32,(j+1)*32+(k+1)%32,(j+1)*32+k))
        mesh('Cooling tower shell',verts,faces,'Pearl concrete');cylinder('Tower open throat',(8,8,11.7),3.7,.05,'Iron',vertices=32);return
    if family=='oil-well':
        slab('Pump concrete pad',8,8,12,10,0,.25,'Pearl concrete')
        for yy in (6,10):beam('Pump A frame',(5,yy,0),(8,yy,5),.3,'Iron');beam('Pump A frame',(11,yy,0),(8,yy,5),.3,'Iron')
        phase=(v-1)*math.tau/6;z1=5+math.sin(phase);z2=5-math.sin(phase)
        beam('Walking beam',(3,8,z1),(13,8,z2),.5,'Navy metal');beam('Pump rod',(3,8,.5),(3,8,z1),.12,'Steel')
        cylinder('Drive crank',(10,8,2),1.1,.3,'Amber',(math.pi/2,0,0),vertices=20);return
    if family in ('refinery','oil-rig') and v%4 in (1,2):
        for xx in (4.5,11.5):
            cylinder('Process vessel',(xx,8,3.7),2.5,7.4,'Ivory',vertices=24)
            cylinder('Tank crown',(xx,8,7.5),2.6,.18,'Zinc',vertices=24)
            for z in (1.3,6.4):cylinder('Tank steel band',(xx,8,z),2.54,.13,'Steel',vertices=24)
        for yy in (3,13):beam('Transfer pipe',(2,yy,1),(14,yy,1),.32,'Steel')
        return
    if family=='steelmill' and v%5 in (2,3):
        for xx in (5,11):
            cylinder('Blast furnace',(xx,8,5),2.3,10,'Rust R3',vertices=20)
            for z in (3,6,9):cylinder('Furnace band',(xx,8,z),2.4,.25,'Steel',vertices=20)
            cylinder('Exhaust stack',(xx,8,12),.9,4,'Iron',vertices=16)
        return
    if family=='farm' and v%4==1:
        for xx in (5,11):cylinder('Grain silo',(xx,8,4.2),2.6,8.4,'Ivory',vertices=24);cylinder('Silo cap',(xx,8,8.45),2.7,.25,'Zinc',vertices=24)
        return
    if family=='bank':
        slab('Bank stone facade',8,8,13,12,0,6.5,'Limestone');windows(8,8,13,12,2,2.6,2)
        for xx in (3,6.3,9.6,13):slab('Bank column',xx,14.1,.5,.6,0,6.8,'Ivory')
        slab('Bank cornice',8,8,13.6,12.6,6.5,.5,'Ivory');roof(8,8,13.3,12.3,7,1.5,'Slate');return
    height0=4.8 if family=='farm' else min(9,max(4,h/Z*.7))
    slab('Industrial plinth',x,y,w,d,0,.3,'Pearl concrete')
    slab('Factory hall',x,y,w,d,.3,height0,'Brick' if family in ('coal-mine','power-plant','steelmill','factory') else 'Warm plaster')
    roof(x,y,w,d,height0+.3,1.8,'Terracotta' if family=='farm' else 'Zinc')
    for yy in (y-d*.25,y+d*.25):box('Industrial window',(x+w/2+.04,yy,3),(.06,max(1,d*.3),1.3),'Glass pale')
    for xx in (x-w*.25,x+w*.25):box('Service bay',(xx,y+d/2+.06,1.6),(max(1,w*.3),.08,2.8),'Navy metal')
    if family in ('power-plant','factory','steelmill'):
        cylinder('Masonry chimney',(x-2,y-2,height0+3),.65,6,'Brick',vertices=20)
        cylinder('Chimney crown',(x-2,y-2,height0+6),.75,.2,'Limestone',vertices=20)
    if family=='sawmill':
        for j in range(4):
            for k in range(2):cylinder('Seasoned timber stack',(x-w*.25+j*.7,y+d*.35,.55+k*.6),.29,3.8,'Timber',(math.pi/2,0,0),vertices=12)
        slab('Sawmill loading canopy',x,y+d*.4,w,3.5,3.4,.16,'Navy metal')
    if family=='factory' and v%2==0:
        for xx in (-3,0,3):slab('Sawtooth roof light',x+xx,y,1.3,d*.7,height0+1.4,.18,'Glass pale')

def airport(job):
    sid=job['variant']
    if sid in (2655,2656,2657,2658):
        front=sid%2==1
        if front:
            slab('Hangar near wall',14.6,8,.5,16,0,8,'Warm plaster');roof(8,8,15,16,8,2,'Zinc')
            for yy in (1,15):slab('Hangar portal pier',8,yy,15,.5,0,1.2,'Pearl concrete')
        else:slab('Hangar far wall',.5,8,.5,16,0,8,'Warm plaster')
        return
    if sid==2651:
        slab('Control tower shaft',8,8,5,5,0,12,'Pearl concrete');slab('Control cabin',8,8,9,9,12,2.8,'Glass');slab('Control roof',8,8,9.5,9.5,14.8,.4,'Navy metal')
        beam('Tower aerial',(8,8,15.2),(8,8,18),.1,'Steel');return
    if sid in (2659,2660,2661,2662):
        slab('Passenger bridge',8,8,15.5,3.3,2.5,2.5,'Glass pale');slab('Bridge roof',8,8,16,3.7,5,.18,'Zinc')
        for xx in (2,14):slab('Bridge pier',xx,8,.5,.5,0,2.5,'Steel')
        return
    if sid==2633:
        slab('Heliport tower',8,8,13,13,0,12,'Warm plaster');windows(8,8,13,13,4,2.6,1.6)
        slab('Helipad roof',8,8,16,16,12,.4,'Road R3')
        for xx in (5.5,10.5):slab('Helipad H',xx,8,.5,7,12.42,.02,'Marking')
        slab('Helipad H crossbar',8,8,5,.5,12.42,.02,'Marking');return
    slab('Terminal plinth',8,8,15.8,15.8,0,.35,'Pearl concrete')
    slab('Terminal hall',8,8,15.5,15.5,.35,4.2,'Glass pale')
    for xx in (1,4,7,10,13,15):slab('Terminal mullion',xx,15.8,.12,.12,.3,4.3,'Ivory')
    slab('Terminal roof',8,8,16,16,4.6,.4,'Navy metal')
    for xx in (5,11):slab('Skylight',xx,8,3,8,5,.15,'Glass')

def air_surface(sid):
    runway=2645<=sid<=2649 or 2673<=sid<=2675
    grass=2669<=sid<=2672
    plane('Airport surface',0,0,16,16,.01,'Grass' if grass else 'Paving R3')
    if runway:
        plane('Runway asphalt',0,1.4,16,14.6,.025,'Road R3')
        for yy in (2,14):slab('Runway edge',8,yy,16,.13,.03,.02,'Marking')
        for xx in (2,10):slab('Runway centre stripe',xx,8,4,.23,.03,.02,'Marking')
        if sid in (2649,2673,2675):
            for yy in (3,5,7,9,11,13):slab('Threshold bar',3,yy,5,.6,.03,.02,'Marking')
    elif sid!=2634 and not grass and sid!=2667:
        # Native taxiway positions: parallel edges, centre lines and junctions.
        if sid in (2636,2639,2640,2641,2642):
            x=3 if sid==2636 else 13 if sid==2642 else 8
            slab('North south taxi line',x,8,.10,16,.03,.01,'Amber')
        if sid in (2637,2638,2639,2641,2643,2644):
            y=13 if sid==2637 else 3 if sid==2643 else 8
            slab('East west taxi line',8,y,16,.10,.03,.01,'Amber')
        if sid==2635:
            for x in (3,13):slab('Aircraft stand border',x,8,.12,10,.03,.01,'Marking')
            slab('Aircraft stand stop',8,3,10,.12,.03,.01,'Marking');slab('Stand centre',8,8,.10,8,.04,.01,'Amber')
    if not grass:
        for v in (4,12):slab('Apron expansion joint',v,8,.025,16,.028,.005,'Gravel')

def air_extra(job):
    v=job['variant']
    if v<6:
        air_surface(2634 if v==0 else 2649 if v==5 else 2646);transpose()
    elif v<12:
        # Open hangars retain independent near/far walls for aircraft sorting.
        if v in (7,9):slab('Hangar far wall',.6,8,.5,16,0,8,'Warm plaster')
        else:
            slab('Hangar side',14.6,8,.5,16,0,8,'Warm plaster');roof(8,8,15.7,16,8,2,'Zinc')
            if v in (10,11):slab('Hangar back',8,1,16,.4,0,8,'Warm plaster')
        if v in (6,7):transpose()
        elif v==10:rotate(90)
        elif v==11:rotate(180)
    elif v==12:
        plane('Helipad inset',0,0,16,16,.02,'Road R3')
        for xx in (5.5,10.5):slab('Helipad H',xx,8,.55,7,.04,.02,'Marking')
        slab('Helipad crossbar',8,8,5,.55,.04,.02,'Marking')
    else:plane('Airfield grass',0,0,16,16,.01,'Grass')

for job in jobs:
    asset('W_'+job['key'].replace(':','_'));kind=job['kind'];sid=job.get('sprite_id',job.get('index'))
    if kind=='town':town(job)
    elif kind=='industry':industry(job)
    elif kind in ('town_ground','industry_ground'):
        ground_material='Grass' if job.get('family')=='forest' else 'Soil' if job.get('family')=='farm' else 'Paving R3'
        plane('Site ground',0,0,16,16,.01,ground_material)
        if kind=='town_ground' and 'STADIUM' in job['name']:
            plane('Playing field',0,0,16,16,.03,'Grass')
            part=job['part'];xedge=2 if part<2 else 14;yedge=2 if part%2==0 else 14
            slab('Pitch touchline',8,yedge,16,.11,.04,.01,'Marking');slab('Pitch goal line',xedge,8,.11,16,.04,.01,'Marking')
            slab('Pitch halfway line',15.94 if part<2 else .06,8,.12,16,.04,.01,'Marking')
        else:
            for v in (4,8,12):slab('Paving joint',8,v,16,.025,.02,.005,'Gravel')
    elif kind=='airport':airport(job)
    elif kind=='airport_extra':air_extra(job)
    elif kind=='airport_ground':
        air_surface(sid)
    elif kind=='airport_fence':
        for xx in (0,4,8,12,16):slab('Airport fence post',xx,0,.1,.1,0,1.5,'Steel')
        for z in (.4,.8,1.2):beam('Airport wire',(0,0,z),(16,0,z),.04,'Iron')
        if sid==2663:transpose()
    elif kind=='windsock':
        slab('Windsock pole',0,0,.12,.12,0,5,'Steel');beam('Wind cone',(0,0,5),(2.8,0,4.8+math.sin((sid-2676)*math.pi/2)*.3),.4,'Amber')
    elif kind=='radar':
        slab('Radar mast',0,0,.28,.28,0,4,'Steel')
        angle=(sid-2680)*math.pi/6
        o=box('Rotating radar antenna',(0,0,4.3),(4,.25,1.3),'Ivory');o.rotation_euler.z=angle
    elif kind=='tree':
        species=job['species'];stage=job['stage'];scale=[.28,.5,.75,1,1,.9,.8][stage]
        h=(5.8+(species%4)*.6)*scale
        cylinder('Tree trunk',(0,0,h*.38),.20*scale,h*.76,'Timber',vertices=10)
        if stage<6:
            leaf='Leaf pine' if species%4==0 else 'Leaf oak' if species%3==0 else 'Leaf lime'
            if stage==5:leaf='Timber'
            for i in range(4):
                t=i*math.pi/2+.3*species;ellipsoid('Layered canopy',(math.cos(t)*scale,math.sin(t)*scale,h*.72+i*.12),(1.7*scale,1.8*scale,2.1*scale),leaf,species*17+i)
        else:
            for i in range(4):
                t=i*math.pi/2;beam('Dead branch',(0,0,h*.45),(math.cos(t)*1.5*scale,math.sin(t)*1.5*scale,h*.85),.09*scale,'Timber')
    if kind in ('town','industry') and job.get('family')!='forest':construction(job)
    current['native_sprite']=job['key'];current['category']=job['category'];current.asset_mark()

tail=source.split('# Reuse the same lights')[1]
tail=tail.replace('temperate-infrastructure.blend','temperate-world.blend').replace('infrastructure-plan.json','world-plan.json')
exec(compile('# Reuse the same lights'+tail,str(HERE/'temperate_models.py'),'exec'),globals())
