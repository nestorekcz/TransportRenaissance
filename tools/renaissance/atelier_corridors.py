"""Editable road and conventional railway kit for Atelier revision 2.

Original procedural meshes, GPL-2.0-only. Coordinates use the engine's
16-unit tile. build() runs inside the shared Blender authoring rig.
"""
import math
import random


def arc(cx, cy, radius, start, end, steps=24):
    return [(cx+radius*math.cos(start+(end-start)*i/steps),
             cy+radius*math.sin(start+(end-start)*i/steps)) for i in range(steps+1)]


def build(api):
    import bpy
    from mathutils import Vector
    from mathutils.geometry import tessellate_polygon
    asset, box, mesh = (api[n] for n in ('asset', 'box', 'mesh'))
    mat = api['material']
    mat('Road asphalt R2', (.105,.12,.125), texture=48)
    mat('Pavement R2', (.47,.455,.40), texture=30)
    mat('Kerb R2', (.62,.60,.53), texture=22)
    mat('Gutter R2', (.22,.23,.215), texture=32)
    mat('Joint R2', (.31,.32,.29))
    mat('Rail rust R2', (.205,.135,.085), .85)
    mat('Rail head R2', (.31,.35,.34), .48, .5)
    mat('Ballast R2', (.32,.32,.285), texture=30)
    mat('Sleepers R2', (.19,.135,.085), texture=24)

    def polygon(name, pts, z, material):
        v=[Vector((x,y,z)) for x,y in pts]
        triangles=tessellate_polygon([v])
        index={(round(p.x,6),round(p.y,6)):i for i,p in enumerate(v)}
        faces=[tuple(p if isinstance(p,int) else index[(round(p.x,6),round(p.y,6))] for p in t) for t in triangles]
        return mesh(name, v, faces, material)

    def ribbon(name, points, half, z, material):
        verts=[]
        for i,(x,y) in enumerate(points):
            a=points[max(0,i-1)]; b=points[min(len(points)-1,i+1)]
            length=math.hypot(b[0]-a[0],b[1]-a[1])
            nx,ny=-(b[1]-a[1])/length,(b[0]-a[0])/length
            verts.extend([(x+nx*half,y+ny*half,z),(x-nx*half,y-ny*half,z)])
        return mesh(name,verts,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(points)-1)],material)

    def line(name, a, b, width, z, material):
        return ribbon(name,[a,b],width/2,z,material)

    def kerb(points):
        # The dark gutter and light stone cap read separately at gameplay zoom.
        ribbon('Recessed drainage channel',points,.24,.045,'Gutter R2')
        ribbon('Continuous stone kerb',points,.105,.18,'Kerb R2')
        # Individual joints, placed by distance rather than curve subdivision.
        total=0
        for a,b in zip(points,points[1:]):
            length=math.dist(a,b)
            for j in range(math.floor(total/1.4)+1, math.floor((total+length)/1.4)+1):
                t=(j*1.4-total)/length; x=a[0]+(b[0]-a[0])*t; y=a[1]+(b[1]-a[1])*t
                nx,ny=-(b[1]-a[1])/length,(b[0]-a[0])/length
                line('Kerb stone joint',(x-nx*.10,y-ny*.10),(x+nx*.10,y+ny*.10),.022,.185,'Joint R2')
            total+=length

    def road(bits, urban):
        a,b=3.1,12.9
        polygon('Continuous asphalt bed',[(0,0),(16,0),(16,16),(0,16)],.025,'Road asphalt R2')
        paving=[]; boundaries=[]
        if bits in (5,10):
            transform=(lambda x,y:(x,y)) if bits==5 else (lambda x,y:(y,x))
            paving=[[(0,0),(a,0),(a,16),(0,16)],[(b,0),(16,0),(16,16),(b,16)]]
            paving=[[transform(*p) for p in poly] for poly in paving]
            boundaries=[[transform(x,0),transform(x,16)] for x in (a,b)]
            for t in (1,5,9,13): line('Regular centre dash',transform(8,t),transform(8,t+1.8),.13,.04,'Marking')
            # Paver seams and a discrete iron drain stay out of the carriageway.
            for x in (1.55,14.45):
                line('Paver longitudinal joint',transform(x,0),transform(x,16),.025,.145,'Joint R2')
            for t in range(0,17,2):
                for lo,hi in ((0,a-.15),(b+.15,16)):
                    line('Paver cross joint',transform(lo,t),transform(hi,t),.025,.145,'Joint R2')
            for k in range(5):
                line('Drain grille',transform(a+.32,3+k*.14),transform(a+.65,3+k*.14),.055,.05,'Iron')
        elif bits in (3,6,9,12):
            # Genuine quarter-circle geometry. No square elbow at the inside edge.
            corners={9:(0,0,1,1),3:(16,0,-1,1),6:(16,16,-1,-1),12:(0,16,1,-1)}
            ox,oy,sx,sy=corners[bits]
            transform=lambda x,y:(ox+sx*x,oy+sy*y)
            inner=arc(0,0,a,0,math.pi/2)
            outer=arc(0,0,b,0,math.pi/2)
            paving=[[(0,0),*inner],[(16,0),(16,16),(0,16),*reversed(outer)]]
            paving=[[transform(*p) for p in poly] for poly in paving]
            boundaries=[[transform(*p) for p in points] for points in (inner,outer)]
            for start in (.10,.60,1.10):
                ribbon('Curved centre dash',[transform(*p) for p in arc(0,0,8,start,start+.22,8)],.065,.04,'Marking')
            for radius in (1.55,14.45):
                ribbon('Curved paver seam',[transform(*p) for p in arc(0,0,radius,0,math.pi/2)],.013,.145,'Joint R2')
        elif bits in (1,2,4,8):
            # Rounded termination of the carriageway, with a walkable surround.
            angle={1:0,2:math.pi/2,4:math.pi,8:-math.pi/2}[bits]
            def transform(x,y):
                x-=8; y-=8
                return (8+x*math.cos(angle)-y*math.sin(angle),8+x*math.sin(angle)+y*math.cos(angle))
            cap=arc(8,8,4.9,math.pi,0)
            path=[(a,0),(a,8),*cap[1:],(b,0)]
            paving=[[(0,0),*path,(16,0),(16,16),(0,16)]]
            paving=[[transform(*p) for p in poly] for poly in paving]
            boundaries=[[transform(*p) for p in path]]
        else:
            # Corner islands of T and four-way intersections have generous radii.
            for ox,oy,sx,sy,edge_u,edge_v in [(0,0,1,1,1,8),(16,0,-1,1,1,2),(16,16,-1,-1,4,2),(0,16,1,-1,4,8)]:
                transform=lambda x,y:(ox+sx*x,oy+sy*y)
                u,v=bool(bits&edge_u),bool(bits&edge_v)
                if u and v:
                    r=1.4
                    boundary=[(a,0),(a,a-r),*arc(a-r,a-r,r,0,math.pi/2,16)[1:],(0,a)]
                    patch=[(0,0),*boundary]
                elif u:
                    boundary=[(a,0),(a,8)]; patch=[(0,0),(a,0),(a,8),(0,8)]
                else:
                    boundary=[(0,a),(8,a)]; patch=[(0,0),(8,0),(8,a),(0,a)]
                paving.append([transform(*p) for p in patch]); boundaries.append([transform(*p) for p in boundary])
            for bit,p,q in [(1,(8,.6),(8,2.3)),(4,(8,13.7),(8,15.4)),(8,(.6,8),(2.3,8)),(2,(13.7,8),(15.4,8))]:
                if bits&bit: line('Junction approach dash',p,q,.13,.04,'Marking')
        for points in paving: polygon('Raised pedestrian paving',points,.14,'Pavement R2')
        for points in boundaries: kerb(points)
        if not urban:
            # Outer green margin distinguishes the local village street variant.
            for edge,bit in [(0,1),(1,2),(2,4),(3,8)]:
                if bits&bit: continue
                if edge in (0,2):
                    y=.16 if edge==0 else 15.84
                    line('Village edge margin',(.2,y),(15.8,y),.3,.15,'Grass')
                else:
                    x=15.84 if edge==1 else .16
                    line('Village edge margin',(x,.2),(x,15.8),.3,.15,'Grass')

    asset('I07_road_intersection'); road(15,True)
    for bits in range(1,16):
        for urban in (False,True):
            if urban and bits in (1,2,4,8): continue
            asset(f'I10_road_{bits:02d}_{"urban" if urban else "village"}'); road(bits,urban)

    paths=[[(8,0),(8,16)],[(0,8),(16,8)],
           arc(0,0,8,0,math.pi/2),arc(16,16,8,math.pi,math.pi*1.5),
           arc(0,16,8,-math.pi/2,0),arc(16,0,8,math.pi/2,math.pi)]

    def offset(points,distance):
        result=[]
        for i,(x,y) in enumerate(points):
            a=points[max(0,i-1)]; b=points[min(len(points)-1,i+1)]
            length=math.dist(a,b); nx,ny=-(b[1]-a[1])/length,(b[0]-a[0])/length
            result.append((x+nx*distance,y+ny*distance))
        return result

    def track(indices, ballast=True):
        # All beds first, then ties and continuous rail profiles, so branching
        # ballast cannot obscure the neighbouring route's running rails.
        if ballast:
            for layer,idx in enumerate(indices):
                path=paths[idx]
                ribbon('Ballast shoulder',path,3.05,.035+layer*.004,'Ballast R2')
                ribbon('Raised ballast crown',path,2.55,.12+layer*.004,'Ballast R2')
                # Combined angular aggregate mesh, rather than a smooth slab.
                rng=random.Random(170+idx); verts=[]; faces=[]
                for p,q in zip(path,path[1:]):
                    length=math.dist(p,q); ux,uy=(q[0]-p[0])/length,(q[1]-p[1])/length
                    for stone in range(max(1,round(length*22))):
                        t=rng.random(); side=rng.uniform(-2.95,2.95)
                        x=p[0]+(q[0]-p[0])*t-uy*side; y=p[1]+(q[1]-p[1])*t+ux*side
                        r=rng.uniform(.07,.17); z=.12 if abs(side)<2.5 else .035; base=len(verts)
                        verts.extend([(x-r,y,z),(x,y-r*.7,z),(x+r,y,z),(x,y+r*.7,z),(x,y,z+r*.6)])
                        faces.extend([(base,base+1,base+4),(base+1,base+2,base+4),(base+2,base+3,base+4),(base+3,base,base+4)])
                mesh('Angular ballast aggregate',verts,faces,'Ballast R2')
        for layer,idx in enumerate(indices):
            path=paths[idx]; total=0
            for p,q in zip(path,path[1:]):
                length=math.dist(p,q); ux,uy=(q[0]-p[0])/length,(q[1]-p[1])/length
                for j in range(math.floor((total-.5)/1.05)+1,math.floor((total+length-.5)/1.05)+1):
                    t=(j*1.05+.5-total)/length; x=p[0]+(q[0]-p[0])*t; y=p[1]+(q[1]-p[1])*t
                    sleeper=box('Timber sleeper',(x,y,.20),(.32,4.25,.17),'Sleepers R2',.018)
                    sleeper.rotation_euler.z=math.atan2(uy,ux)
                    for side in (-1,1):
                        for off in (-.18,.18):
                            clip=box('Rail fixing',(x-uy*(side*1.04+off),y+ux*(side*1.04+off),.32),(.18,.12,.08),'Iron',.01)
                            clip.rotation_euler.z=math.atan2(uy,ux)
                total+=length
            for side in (-1,1):
                linepath=offset(path,side*1.04)
                ribbon('Oxidised rail foot',linepath,.15,.30+layer*.004,'Rail rust R2')
                ribbon('Rail web',linepath,.045,.39+layer*.004,'Rail rust R2')
                ribbon('Polished running rail',linepath,.085,.49+layer*.004,'Rail head R2')

    asset('I06_track_straight'); track([1])
    for idx in range(6):
        asset(f'I11_track_{idx}'); track([idx])
        asset(f'I11_overlay_{idx}'); track([idx],False)
    for label,indices in [('crossing',[0,1]),('double_n_s',[2,3]),('double_e_w',[4,5])]:
        asset('I11_'+label); track(indices)
    # A source-only, longer turnout shows the intended engineering detail.
    # Shared bearers and one ballast mesh prevent intersecting tile previews.
    asset('I11_turnout')
    def branch_y(x):
        t=max(0,(x-6)/20)
        return 5+8*t*t
    branch=[(x*.5,branch_y(x*.5)) for x in range(53)]
    outline=[(0,1.95),(26,1.95),(26,16.05)]+[(x,y+3.05) for x,y in reversed(branch[:-1])]
    polygon('Single turnout ballast bed',outline,.08,'Ballast R2')
    for x in (j*1.05+.5 for j in range(25)):
        top=branch_y(x)+2.1; bottom=2.9
        box('Common turnout bearer',(x,(top+bottom)/2,.20),(.33,top-bottom,.17),'Sleepers R2',.02)
        for y in (3.96,6.04,branch_y(x)-1.04,branch_y(x)+1.04):
            for off in (-.18,.18): box('Turnout rail fixing',(x,y+off,.32),(.18,.12,.08),'Iron',.01)
    for layer,path in enumerate([[(0,5),(26,5)],branch[12:]]):
        for side in (-1,1):
            linepath=offset(path,side*1.04)
            ribbon('Turnout rail foot',linepath,.15,.30+layer*.006,'Rail rust R2')
            ribbon('Turnout rail web',linepath,.045,.39+layer*.006,'Rail rust R2')
            ribbon('Turnout rail head',linepath,.085,.49+layer*.006,'Rail head R2')
    for y in (4.28,5.72): line('Frog check rail',(15.2,y),(19.2,y),.10,.49,'Rail head R2')
    box('Point motor',(7,1.5,.35),(1.25,.70,.50),'Iron',.08)
    line('Point linkage',(7,1.5),(7,6.2),.12,.29,'Steel')
    return paths
