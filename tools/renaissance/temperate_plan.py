"""Finite native sprite assignments for the temperate-world production pass."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT.parent
OUT=WORK/'artifacts/atelier-temperate'

def infrastructure():
    jobs={}
    def add(sid,kind,**kw):
        key=str(sid); jobs[key]={'key':key,'sprite_id':sid,'kind':kind,**kw}
    # Six depth-sorted parts for four depot entrances. Coordinates are from the
    # native draw tables; models use tile coordinates, compiler removes draw origin.
    for family,base,anchors in [('rail',1063,[(2,2),(13,2),(2,2),(2,13),(2,13),(13,2)]),('road',1408,[(0,0),(15,0),(0,0),(0,15),(0,15),(15,0)])]:
        for j,(orientation,part) in enumerate([(0,'rear'),(0,'front'),(-90,'rear'),(-90,'front'),(90,'all'),(180,'all')]):
            add(base+j,'depot',family=family,angle=orientation,part=part,anchor=anchors[j],category='depots')
    # Bay stops: the B layer is a real loading building; the A/C layers are
    # separate back/near details that retain the native vehicle sorting order.
    cargo=[[(0,15),(13,0),(2,0)],[(15,3),(0,0),(0,3)],[(3,0),(0,0),(3,15)],[(0,0),(0,13),(15,2)]]
    bus=[[(2,0),(13,0),(0,13)],[(0,3),(0,0),(13,3)],[(3,15),(0,0),(3,0)],[(15,2),(0,13),(0,0)]]
    for mode,base,anchors in [('cargo',2708,cargo),('bus',2692,bus)]:
        for d in range(4):
            add(base+d,'stop_ground',mode=mode,angle=-90*d,category='road-stops',ground=True)
            for part in range(3): add(base+4+part*4+d,'stop',mode=mode,angle=-90*d,part=part,anchor=anchors[d][part],category='road-stops')
    for i in range(8):
        key=f'ROAD_STOPS:{i}'
        jobs[key]={'key':key,'feature':'ROAD_STOPS','index':i,'kind':'drive_stop','mode':'cargo' if i>=4 else 'bus','layout':i%4,'category':'road-stops'}
    # Continuous sloping approaches. Slope corner bits are the engine's W/S/E/N.
    for urban,base in [(False,1343),(True,1324)]:
        for i,slope in enumerate([12,6,3,9]): add(base+i,'road_slope',slope=slope,axis='x' if slope in (12,3) else 'y',category='roads',ground=True)
    slope_offsets=[14,15,22,13,0,21,17,12,23,0,18,20,19,16]
    for slope,offset in enumerate(slope_offsets,1):
        if offset: add(1011+offset,'rail_slope',slope=slope,category='rails',ground=True)
    for i in range(8): add(1301+i,'rail_fence',variant=i,category='rails')
    for i in range(8):
        add(1370+i,'crossing',axis='y' if i%2==0 else 'x',closed=(i%4)>=2,category='roads',ground=True)
    for i in range(2): add(1406+i,'streetlight',angle=i*90,category='street-details')
    # All built-in bridge families. Later constants intentionally resolve shared
    # sprites (e.g. concrete decks also used by short suspension pieces).
    constants=re.findall(r'static const SpriteID (SPR_BT\w+)\s*=\s*(\d+);',(ROOT/'src/table/sprites.h').read_text())
    for name,num in constants:
        sid=int(num); axis='x' if '_X' in name else 'y'
        style=next((s for k,s in [('BTWDN','timber'),('BTSGA','arch'),('BTSUS','suspension'),('BTCAN','cantilever'),('BTTUB','tubular'),('BTCON','concrete')] if k in name),'concrete')
        family=next((s.lower() for s in ['ROAD','RAIL','MONO','MGLV'] if '_'+s in name),'rail')
        part='pillar' if 'PILLAR' in name else 'front' if 'FRONT' in name else 'deck'
        ramp='RAMP_' in name; elevated='SLOPE_' in name
        slope=(12 if axis=='x' else 9) if name.endswith('_UP') else (3 if axis=='x' else 6)
        add(sid,'bridge',axis=axis,style=style,family=family,part=part,ramp=ramp,elevated=elevated,slope=slope,
            anchor=((0,12) if axis=='x' else (12,0)) if part=='front' else (0,0),category='bridges',symbol=name)
    for family,base in [('rail',2365),('mono',2373),('mglv',2381),('road',2389)]:
        for d in range(4):
            for part in range(2): add(base+d*2+part,'tunnel',family=family,angle=-90*d,part=part,category='tunnels')
    for i in range(6): add(4070+i,'ship_depot',variant=i,category='depots')
    return list(jobs.values())

def world(coverage_path=None):
    import json
    jobs={}
    coverage_path=coverage_path or WORK/'artifacts/atelier-r2/demo-coverage.json'
    preserved={r['sprite_id'] for r in json.loads(coverage_path.read_text()) if r['category'] in ('building','building-ground','tree')}
    text=(ROOT/'src/table/town_land.h').read_text()
    specs=re.findall(r'\tMS\(([\s\S]*?)\), // ([0-9A-F]+)',text)
    rows=[[v.strip() for v in r.split(',')] for r in re.findall(r'^\s*M\((.*)\),',text,re.M)]
    selected={}
    constants={k:int(v) for k,v in re.findall(r'static const SpriteID (\w+)\s*=\s*(\d+);',(ROOT/'src/table/sprites.h').read_text())}
    for s,h in specs:
        if 'ClimateTemperate' not in s:continue
        hid=int(h,16);name=s.split(',')[4].strip().replace('STR_TOWN_BUILDING_NAME_','')
        match=re.search(r'Size(\d)x(\d)',s);count=int(match[1])*int(match[2]) if match else 1
        for k in range(count):selected[hid+k]=(name,hid,k,count)
    for hid,(name,parent,part,count) in selected.items():
        for j,row in enumerate(rows[hid*16:(hid+1)*16]):
            sid=int(row[2],16)
            if sid and sid not in preserved:
                # A reused completed sprite must not be overwritten by an earlier
                # construction stage which happens to reference the same ID.
                stage=max(j%4,jobs.get(str(sid),{}).get('stage',0))
                jobs[str(sid)]={'key':str(sid),'sprite_id':sid,'kind':'town','name':name,'house_id':parent,'part':part,'parts':count,
                    'stage':stage,'anchor':[int(row[4]),int(row[5])],'bounds':[int(row[6]),int(row[7]),int(row[8])],
                    'category':'town-buildings','source_dir':'world'}
            if row[0].startswith('0x') or row[0] in constants:
                ground=int(row[0],16) if row[0].startswith('0x') else constants[row[0]]
                if ground not in preserved and ground not in (3924,3981):jobs.setdefault(str(ground),{'key':str(ground),'sprite_id':ground,'kind':'town_ground','name':name,'part':part,'parts':count,'ground':True,'category':'town-ground','source_dir':'world'})
    itext=(ROOT/'src/table/industry_land.h').read_text().split('static const DrawBuildingsTileStruct _industry_draw_tile_data')[1].split('};')[0]
    irows=[[v.strip() for v in r.split(',')] for r in re.findall(r'^\s*M\((.*)\),',itext,re.M)]
    families=[(2011,2025,'coal-mine'),(2045,2054,'power-plant'),(2061,2071,'sawmill'),(2072,2077,'forest'),(2078,2095,'refinery'),(2096,2105,'oil-rig'),(2106,2117,'farm'),(2118,2145,'steelmill'),(2146,2160,'factory'),(2173,2179,'oil-well'),(2180,2183,'bank')]
    for lo,hi,family in families:
        for sid in range(lo,hi+1):
            refs=[(j,row) for j,row in enumerate(irows) if len(row)>=10 and row[2].split()[0].lower()==hex(sid)]
            grounds=[row for row in irows if row[0].lower()==hex(sid)]
            is_ground=bool(grounds) and not refs
            row=refs[-1][1] if refs else None
            jobs[str(sid)]={'key':str(sid),'sprite_id':sid,'kind':'industry_ground' if is_ground else 'industry','family':family,'variant':sid-lo,
                'stage':max((j%4 for j,r in refs),default=3),'anchor':[int(row[4]),int(row[5])] if row else [0,0],
                'bounds':[int(row[6]),int(row[7]),int(row[8])] if row else [16,16,35],
                'ground':is_ground,'category':'industries','source_dir':'world'}
    # Airports use shared native building and ground pieces; preserve all layouts.
    ground_ids=set(range(2634,2650))|{2667,2669,2670,2671,2672,2673,2674,2675}
    for sid in range(2633,2692):
        if sid in (2663,2664):kind='airport_fence'
        elif sid in ground_ids:kind='airport_ground'
        elif 2676<=sid<=2679:kind='windsock'
        elif 2680<=sid<=2691:kind='radar'
        else:kind='airport'
        anchors={2650:(2,0),2651:(3,3),2652:(0,1),2653:(3,3),2654:(0,3),2655:(14,0),2657:(14,0),2659:(7,11),2660:(2,7),2661:(3,2),2662:(0,8)}
        jobs[str(sid)]={'key':str(sid),'sprite_id':sid,'kind':kind,'variant':sid,'ground':sid in ground_ids,'anchor':anchors.get(sid,(0,0)),'category':'airports','source_dir':'world'}
    # All temperate tree species and their seven native growth/death stages.
    for sid in range(1576,1709):
        if sid not in preserved:jobs[str(sid)]={'key':str(sid),'sprite_id':sid,'kind':'tree','species':(sid-1576)//7,'stage':(sid-1576)%7,'category':'trees','source_dir':'world'}
    jobs['1420']={'key':'1420','sprite_id':1420,'kind':'town_ground','name':'INDUSTRIAL_PAVING','ground':True,'category':'town-ground','source_dir':'world'}
    for i in range(15):
        key=f'AIRPORTS:{i}'
        jobs[key]={'key':key,'feature':'AIRPORTS','index':i,'kind':'airport_extra','variant':i,'ground':i<6 or i>=13,
                   'anchor':(14,0) if i in (6,8,10,11) else (0,1) if i==12 else (0,0),'category':'airports','source_dir':'world'}
    return list(jobs.values())

def details():
    rows=[]
    def add(sid,kind,**kw):rows.append({'key':str(sid),'sprite_id':sid,'kind':kind,'source_dir':'details',**kw})
    for family,base in [('mono',1093),('mglv',1175)]:
        for j in range(26):add(base+j,'guideway',family=family,layout=j,ground=True,category='rails')
        for j in range(6):add(base-6+j,'guideway',family=family,layout=1-j if j<2 else j,overlay=True,category='rails')
    for sid in range(1275,1291):add(sid,'signal',variant=sid-1275,signal_type=0,semaphore=False,category='signals')
    for j in range(240):
        block=j//16
        signal_type=block+1 if block<3 else block-3 if block<7 else block-3 if block<9 else block-7 if block<11 else block-7 if block<13 else 0
        rows.append({'key':f'SIGNALS:{j}','feature':'SIGNALS','index':j,'kind':'signal','source_dir':'details','variant':j%16,
                     'signal_type':signal_type,'semaphore':48<=j<112 or j>=176,'category':'signals'})
    for family,base in [('mono',1382),('mglv',1394)]:
        for i in range(8):add(base+i,'guide_crossing',family=family,axis='y' if i%2==0 else 'x',closed=(i%4)>=2,ground=True,category='roads')
    for sid in range(4090,4126):add(sid,'field_fence',variant=sid-4090,category='landscape')
    for sid in range(2601,2633):add(sid,'landmark',variant=sid,category='civic-details',anchor=(7,7) if sid==2601 else (4,4) if sid==2602 else (0,0))
    add(4790,'landmark',variant=4790,category='civic-details',anchor=(8,8))
    for sid in range(2727,2733):add(sid,'dock',variant=sid-2727,category='water-transport',anchor=(0,4) if (sid-2727)%2==0 else (4,0))
    add(4076,'buoy',category='water-transport')
    for sid in range(1414,1420):add(sid,'roadworks',variant=sid-1414,category='street-details')
    for i in range(4):
        rows.append({'key':f'OTTD_GUI:{78+i}','feature':'OTTD_GUI','index':78+i,'kind':'waypoint','variant':i,'source_dir':'details','category':'stations',
                     'anchor':[(0,0),(0,11),(0,0),(11,0)][i]})
    rows.append({'key':'OTTD_GUI:86','feature':'OTTD_GUI','index':86,'kind':'helipad','source_dir':'details','category':'airports','anchor':(10,6)})
    return rows

if __name__=='__main__':
    import json
    from collections import Counter
    rows=infrastructure(); print(len(rows),dict(Counter(r['category'] for r in rows)))
