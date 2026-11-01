"""Compile the approval demo: Blender renders -> GRF v2, exact stable IDs.
GPL-2.0-only. Geometry is in atelier_models.py; no gameplay properties change.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import re
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageChops
from build_assets import fallback, palette_image

ROOT=Path(__file__).resolve().parents[2]; WORK=ROOT.parent
parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path,default=WORK/'artifacts/atelier'); args=parser.parse_args()
OUT=args.output.resolve(); GAME=OUT/'game'; GAME.mkdir(exist_ok=True,parents=True)
OG=WORK/'tools/sources/opengfx'
S=4
original={}
for line in (WORK/'artifacts/opengfx-base.nfo').read_text().splitlines():
    m=re.match(r'^(\d+) (\S+\.png) 8bpp (-?\d+) (-?\d+) (\d+) (\d+) (-?\d+) (-?\d+) normal',line)
    if m:
        i=int(m[1]); vals=list(map(int,m.groups()[2:])); original[i]={'file':m[2],'rect':vals}

entries={}
def put(i,im,offset,source,category,state='complete',mask=None):
    assert i not in entries, ('duplicate',i)
    entries[i]={'image':im,'offset':offset,'source':source,'category':category,'state':state,'mask':mask}

renders={(r['id'],r['direction']):r for r in json.loads((OUT/'renders.json').read_text())}
def render(name,d=0,dx=0,dy=0,size=1):
    r=renders[name,d]; im=Image.open(OUT/'renders'/r['file']).convert('RGBA')
    origin=tuple(r['origin_px'])
    # Camera local X is (-X + Y): already OpenTTD's screen projection.
    im=im.resize((round(im.width*S/6*size),round(im.height*S/6*size)),Image.Resampling.LANCZOS)
    origin=(round(origin[0]*S/6*size),round(origin[1]*S/6*size))
    bbox=im.getchannel('A').getbbox(); assert bbox, name
    # Crop to whole base pixels so all zoom anchors agree exactly.
    bbox=(bbox[0]//S*S,bbox[1]//S*S,math.ceil(bbox[2]/S)*S,math.ceil(bbox[3]/S)*S)
    maskpath=OUT/'masks'/f'{name}-{d}-0001.png'
    mask=None
    if maskpath.exists():
        mask=Image.open(maskpath).convert('L').resize(im.size,Image.Resampling.LANCZOS).crop(bbox)
    im=im.crop(bbox)
    offset=((bbox[0]-origin[0])/S-2*(dy-dx),(bbox[1]-origin[1])/S-dx-dy)
    return im,tuple(round(v) for v in offset),mask

def model(i,name,category,dx=0,dy=0,d=0,size=1,state='complete',company=False):
    im,off,mask=render(name,d,dx,dy,size)
    put(i,im,off,name,category,state,mask if company else None)

def point(x,y,z=0): return ((31+2*(y-x))*S,(x+y-z)*S)
def poly(draw,verts,fill): draw.polygon([point(*v) for v in verts],fill=fill)
def ground(kind='grass',slope=0,stage=3):
    sid=(3924+stage*19+slope) if kind in ('grass','soil') else (4023+slope if kind=='rock' else 4000+slope)
    row=original[sid]; x,y,w,h,dx,dy=row['rect']; src=Image.open(OG/row['file'])
    rgb=src.convert('RGB')
    mask=src.crop((x,y,x+w,y+h)).point(lambda a:255 if a else 0,'L').resize((w*S,h*S),Image.Resampling.NEAREST)
    im=Image.new('RGBA',mask.size); p=im.load(); mp=mask.load()
    for yy in range(im.height):
        for xx in range(im.width):
            if not mp[xx,yy]: continue
            u=(xx/S-31)/32; v=(yy/S+dy)/16; a=(u+v)/2; b=(v-u)/2
            n=math.sin(a*math.tau*3)*math.cos(b*math.tau*2)*2+math.sin((a+b)*math.tau*7)*.8
            grain=((xx*73856093^yy*19349663)%101)/100-.5
            shade=.93+(sum(rgb.getpixel((x+xx//S,y+yy//S)))/765)*.12 if slope else 1
            g=(104+n+grain*4,125+n+grain*4,76+n+grain*3)
            soil=(133+n,112+n,84+n)
            t=stage/3 if kind=='grass' else (0 if kind=='soil' else 1)
            p[xx,yy]=tuple(round((s*(1-t)+v*t)*shade) for v,s in zip(g,soil))+(255,)
    if kind=='rock':
        dr=ImageDraw.Draw(im); rng=random.Random(41+slope)
        for k in range(20):
            xx=rng.randrange(20,230); yy=rng.randrange(15,im.height-5); r=rng.randrange(3,10)
            if mp[xx,yy]:
                dr.polygon([(xx-r,yy),(xx,yy-r),(xx+r,yy),(xx+r*.5,yy+r*.5),(xx-r*.7,yy+r*.4)],fill=(145,142,126,255))
                dr.line([(xx-r,yy),(xx,yy-r),(xx+r,yy)],fill=(181,177,156,255),width=2)
        im.putalpha(mask)
    return im,(dx,dy)

flat,flat_off=ground()
def lot():
    im=flat.copy(); dr=ImageDraw.Draw(im)
    poly(dr,[(0,14),(16,14),(16,16),(0,16)],(161,157,140,255))
    poly(dr,[(7,8),(9,8),(9,16),(7,16)],(174,167,146,255))
    return im

# Exact house IDs and construction/variation references from town_land.h.
house_groups={
    'B01_linden_house':[1444,1445,1446,1502,1504,1506],
    'B02_orchard_villa':[1500,1508,1510,1512,1571,1573,1575],
    'B03_historic_terrace':[1514,1516,1518],
    'B04_courtyard_apartments':[1537,1539],
    'B05_riverside_office':[1541,1543,1545],
    'B06_corner_cafe':[1461,1462,1463],
    'B07_goods_warehouse':[1473,1474,1475],
}
rows=re.findall(r'^\s*M\((.*?)\),',(ROOT/'src/table/town_land.h').read_text(),re.M)
for name,ids in house_groups.items():
    for i in ids:
        match=next(([v.strip() for v in r.split(',')] for r in rows if r.split(',')[2].strip()==hex(i)),None)
        dx,dy=(int(match[4]),int(match[5])) if match else (0,0)
        model(i,name,'building',dx,dy)
        # Existing construction stages retain a visibly unfinished state.
        stage=max((idx%4 for idx,r in enumerate(rows) if r.split(',')[2].strip()==hex(i)),default=3)
        if stage in (0,1):
            e=entries[i]; im=e['image']; dr=ImageDraw.Draw(im)
            # Cut the upper part for foundations; timber scaffolds for stage two.
            if stage==0:
                dr.rectangle((0,0,im.width,im.height*.7),fill=(0,0,0,0))
                e['state']='construction-foundation'
            else: e['state']='construction-scaffold'
            for xx in range(S*2,im.width,S*7):
                dr.line((xx,im.height*.35,xx,im.height-4),fill=(125,103,70,255),width=2)
            for yy in range(int(im.height*.5),im.height,S*5): dr.line((0,yy,im.width,yy),fill=(125,103,70,255),width=2)
for i in [1447,1497,1498,1499,1501,1503,1505,1507,1509,1511,1513,1515,1517,1536,1538,1540,1542,1544,1570,1572,1574]:
    put(i,lot(),flat_off,'courtyard-lot','building-ground')

for i,name in [(1069,'I03_platform_y'),(1070,'I01_platform_x'),(1071,'I03_platform_y'),(1072,'I01_platform_x'),(1073,'I02_station_x'),(1074,'I04_station_y'),(1075,'I03_platform_y'),(1076,'I01_platform_x'),(1077,'I03_platform_y'),(1078,'I01_platform_x')]:
    model(i,name,'station')
for i,name in [(1079,'I09_station_canopy_x'),(1080,'I09_station_canopy_y'),(1081,'I09_station_canopy_x'),(1082,'I09_station_canopy_y')]:
    model(i,name,'station-canopy')
for i in (1083,1084,1085,1086): put(i,Image.new('RGBA',(4,4)),(0,0),'integrated-canopy-glazing','station-canopy')
for n,(dx,dy) in enumerate([(2,0),(0,3),(3,15),(15,2)]):
    model(2696+n,'I05_bus_shelter','bus-terminal',dx,dy,d=[1,0,3,2][n])
    for i in (2700+n,2704+n): put(i,Image.new('RGBA',(4,4)),(0,0),'bus-terminal-unneeded-overlay','bus-terminal')
    im=flat.copy(); dr=ImageDraw.Draw(im)
    poly(dr,[(0,0),(16,0),(16,16),(0,16)],(161,157,140,255))
    poly(dr,[(3,3),(13,3),(13,16),(3,16)],(70,76,75,255))
    im.putalpha(flat.getchannel('A')); put(2692+n,im,flat_off,'bus-terminal-apron','bus-terminal')
for i,name in [(2495,'I08_deck_x'),(2496,'I08_deck_y'),(2497,'I08_front_x'),(2498,'I08_front_y'),(2505,'I08_pier_x'),(2506,'I08_pier_y')]:
    model(i,name,'concrete-bridge',dx=12 if i==2498 else 0,dy=12 if i==2497 else 0)
    if i<2505:
        e=entries[i]; e['offset']=(e['offset'][0],e['offset'][1]-3)

for base,name,count in [(2929,'V01_meridian_diesel',4),(2733,'V02_passenger_coach',4),(2737,'V03_hopper_empty',4),(2781,'V03_hopper_loaded',4),(3284,'V04_civic_bus',8),(3324,'V05_parcel_truck',8),(3685,'V06_river_ferry',8)]:
    for d in range(count): model(base+d,name,'vehicle',d=d,company=True)

for base,name in [(0x652,'N01_oak'),(0x660,'N02_lime'),(0x675,'N03_pine')]:
    for stage in range(7):
        model(base+stage,name,'tree',size=[.30,.55,.78,1,1,.9,.8][stage],state=['sapling','young','growing','mature','mature','dying','dead'][stage])
        if stage>=5:
            e=entries[base+stage]; a=e['image'].getchannel('A'); e['image']=ImageEnhance.Color(e['image']).enhance(.22 if stage==5 else 0); e['image'].putalpha(a)

for stage in range(4):
    for slope in range(19):
        im,off=ground('grass',slope,stage); put(3924+stage*19+slope,im,off,'temperate-meadow','terrain',f'growth-{stage}/slope-{slope}')
for slope in range(19):
    im,off=ground('rock',slope); put(4023+slope,im,off,'limestone-outcrop','terrain',f'slope-{slope}')
for slope in range(23):
    im,off=ground('rough',slope if slope<19 else 0); put(4000+slope,im,off,'rough-meadow','terrain',f'variant-{slope}')

def ground_model(name, transparent=False):
    """Composite the mesh bake using its recorded origin, then clip the tile."""
    road=name.startswith('I10_')
    im=Image.new('RGBA',flat.size) if transparent or road else flat.copy()
    rendered,offset,_=render(name)
    im.alpha_composite(rendered,((offset[0]-flat_off[0])*S,(offset[1]-flat_off[1])*S))
    if road:
        # These meshes cover the entire tile. Edge antialiasing is a sampling
        # boundary, not a strip of grass between adjacent pieces. Extrapolate
        # edge colours before applying the engine's exact opaque diamond.
        pixels=im.load(); alpha=flat.getchannel('A').load()
        # Very low-alpha Lanczos samples have unstable unpremultiplied RGB.
        # Only fully covered pixels may seed the boundary colour extension.
        for yy in range(im.height):
            for xx in range(im.width):
                if pixels[xx,yy][3]<250: pixels[xx,yy]=(0,0,0,0)
        for repeat in range(16):
            updates=[]
            for yy in range(im.height):
                for xx in range(im.width):
                    if not alpha[xx,yy] or pixels[xx,yy][3]: continue
                    neighbours=[pixels[x,y] for x,y in ((xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)) if 0<=x<im.width and 0<=y<im.height and pixels[x,y][3]]
                    if neighbours: updates.append((xx,yy,(*[round(sum(p[c] for p in neighbours)/len(neighbours)) for c in range(3)],255)))
            for xx,yy,colour in updates: pixels[xx,yy]=colour
            if not updates: break
        assert all(pixels[x,y][3] for y in range(im.height) for x in range(im.width) if alpha[x,y]),name
    im.putalpha(ImageChops.multiply(im.getchannel('A'),flat.getchannel('A')) if transparent else flat.getchannel('A'))
    return im

for j in range(12):
    if j<6:
        name=f'I11_track_{j}'; im=ground_model(name)
    elif j==6:
        name='I11_crossing'; im=ground_model(name)
    else:
        name='rail-junction-substrate'; im=flat.copy()
        dr=ImageDraw.Draw(im); poly(dr,[(2,2),(14,2),(14,14),(2,14)],(126,124,111,255))
    put(1011+j,im,flat_off,name,'rail',f'track-layout-{j}')
for j in range(6):
    name=f'I11_overlay_{1-j if j<2 else j}'
    put(1005+j,ground_model(name,True),flat_off,name,'rail',f'junction-overlay-{j}')
for i,name in ((1035,'I11_double_n_s'),(1036,'I11_double_e_w')):
    put(i,ground_model(name),flat_off,name,'rail')

road_ids=[0,1350,1349,1339,1348,1332,1342,1337,1347,1340,1333,1336,1341,1335,1338,1334]
for bits,i in enumerate(road_ids):
    if not i: continue
    for urban in (False,True):
        if urban and i>=1347: continue
        name=f'I10_road_{bits:02d}_{"urban" if urban else "village"}'
        put(i-19 if urban else i,ground_model(name),flat_off,name,'road',f'roadbits-{bits}')

# Water and shore keep exact masks, slope outlines and palette-water identity.
for i in range(4061,4070):
    row=original[i]; x,y,w,h,dx,dy=row['rect']; src=Image.open(OG/row['file']); rgb=src.convert('RGB')
    im=Image.new('RGBA',(w*S,h*S)); pix=im.load()
    for yy in range(h*S):
        for xx in range(w*S):
            idx=src.getpixel((x+xx//S,y+yy//S)); col=rgb.getpixel((x+xx//S,y+yy//S))
            if idx==0: continue
            n=math.sin(xx/S*.5+yy/S*.8)*1.5
            if col[2]>col[0]*1.3: c=(66+n,112+n,129+n)
            elif col[1]>col[0]*1.15: c=(104+n,125+n,76+n)
            else: c=(171+n,160+n,129+n)
            pix[xx,yy]=(*map(round,c),255)
    put(i,im,(dx,dy),'river-shore','water',f'shore-{i-4061}')

# Compile atlas pages at all supported zooms with stable rectangle origins.
ids=sorted(entries); cellw=128; cellh=128; cols=12; pageh=math.ceil(len(ids)/cols)*cellh
for scale in (1,2,4):
    atlas=Image.new('RGBA',(cellw*cols*scale,pageh*scale))
    masks=palette_image(atlas.size)
    for j,i in enumerate(ids):
        e=entries[i]; im=e['image'].resize((e['image'].width*scale//4,e['image'].height*scale//4),Image.Resampling.LANCZOS)
        if e['category'] in ('terrain','road','water','building-ground') or (e['category']=='rail' and not 1005<=i<=1010):
            im.putalpha(e['image'].getchannel('A').resize(im.size,Image.Resampling.NEAREST))
        assert im.width<=cellw*scale and im.height<=cellh*scale, (i,im.size)
        x,y=(j%cols)*cellw*scale,(j//cols)*cellh*scale; atlas.paste(im,(x,y))
        if e['mask'] is not None:
            m=e['mask'].resize(im.size,Image.Resampling.LANCZOS)
            mi=palette_image(im.size); mi.putdata([202 if v>127 else 0 for v in m.getdata()]); masks.paste(mi,(x,y))
        if scale==1: e['atlas']=[j%cols*cellw,j//cols*cellh,im.width,im.height,*e['offset']]
    atlas.save(GAME/f'atelier-{scale}x.png'); masks.save(GAME/f'atelier-mask-{scale}x.png')
    if scale==1:
        fb=fallback(atlas)
        mp=masks.load(); fp=fb.load()
        for yy in range(masks.height):
            for xx in range(masks.width):
                if mp[xx,yy]: fp[xx,yy]=mp[xx,yy]
        fb.save(GAME/'atelier-8bpp.png')

(GAME/'lang').mkdir(exist_ok=True)
(GAME/'lang/english.lng').write_text('##grflangid 0x01\nSTR_NAME :Renaissance Atelier - roads revision 2\nSTR_DESC :Original miniature-world sprite demo. Editable Blender sources. Temperate only. GPL v2. Not the full library.\n')
nml=['grf { grfid: "TR\\02\\01"; name: string(STR_NAME); desc: string(STR_DESC); version: 2; min_compatible_version: 1; }','if (climate == CLIMATE_TEMPERATE) {']
for i in ids:
    e=entries[i]; r=e['atlas']; name=f'a_{i}'
    nml += [f'replace {name}({i}, "atelier-8bpp.png") {{ [{", ".join(map(str,r))}, NOCROP] }}']
    for s,z in ((1,'NORMAL'),(2,'IN_2X'),(4,'IN_4X')):
        r2=[v*s for v in r]
        nml += [f'alternative_sprites({name}, ZOOM_LEVEL_{z}, BIT_DEPTH_32BPP, "atelier-{s}x.png", "atelier-mask-{s}x.png") {{ [{", ".join(map(str,r2))}, NOCROP] }}']
nml.append('}')
(GAME/'renaissance-atelier.nml').write_text('\n'.join(nml)+'\n')
subprocess.run([sys.executable,'-m','nml.main','--grf','renaissance-atelier.grf','renaissance-atelier.nml'],cwd=GAME,check=True)
coverage=[]
for i,e in entries.items():
    coverage.append({'sprite_id':i,'stable_id':f'opengfx:base:{i}','source_asset':e['source'],'category':e['category'],'state':e['state'],'legacy':original.get(i),'export_rect':e['atlas'],'company_mask':e['mask'] is not None,'zoom_scales':[1,2,4],'indexed_fallback':True,'integration':'compiled; runtime review pending'})
(OUT/'demo-coverage.json').write_text(json.dumps(coverage,indent=2))
meta={'sprite_count':len(entries),'encoded_variants':len(entries)*4,'grf_bytes':(GAME/'renaissance-atelier.grf').stat().st_size,'grf_sha256':hashlib.sha256((GAME/'renaissance-atelier.grf').read_bytes()).hexdigest(),'scope':'approval demo only','palette':'DOS','source':'atelier_models.py + atelier_compile.py'}
(OUT/'build.json').write_text(json.dumps(meta,indent=2)); print(json.dumps(meta))

# This is explicitly an asset contact sheet, not an in-engine screenshot.
fontpath='C:/Windows/Fonts/segoeui.ttf'; font=ImageFont.truetype(fontpath,18); small=ImageFont.truetype(fontpath,13)
names=list(dict.fromkeys(r['id'] for r in renders.values())); sheet=Image.new('RGB',(1200,100+math.ceil(len(names)/5)*215),(232,230,220)); dr=ImageDraw.Draw(sheet)
dr.text((28,20),'RENAISSANCE ATELIER / DEMO ASSET CONTACT SHEET',fill=(35,54,53),font=font)
dr.text((28,50),'Original Blender source models. Sprite renders; this sheet is not a game screenshot.',fill=(80,92,85),font=small)
for k,name in enumerate(names):
    x,y=(k%5)*240,(k//5)*215+90
    im=Image.open(OUT/'renders'/renders[name,2 if name.startswith('V') else 0]['file']).convert('RGBA'); im=im.crop(im.getchannel('A').getbbox()); im.thumbnail((218,173),Image.Resampling.LANCZOS)
    sheet.paste(im,(x+(240-im.width)//2,y+175-im.height),im)
    dr.text((x+12,y+182),name.replace('_',' '),font=small,fill=(35,54,53))
sheet.save(OUT/'contact-sheet.png')
