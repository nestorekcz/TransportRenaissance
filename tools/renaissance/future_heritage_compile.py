"""Pack the supplied fleet sheets into per-engine NewGRF graphics overrides.

Only sprite_id is changed. Native prices, capacities, dates and mechanics remain
inherited. Original meshes and directional sheets are preserved in source/fleet.
"""
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from PIL import Image
from build_assets import fallback, palette_image

WORK=Path(__file__).resolve().parents[3]; OUT=WORK/'artifacts/atelier-future-heritage'
SOURCE=OUT/'source/fleet'; GAME=OUT/'game/future-heritage'; GAME.mkdir(parents=True,exist_ok=True)
records=json.loads((SOURCE/'fleet_manifest.json').read_text())['records']
groups=[]; mapping=[]
for r in records:
    eid=r['engine_id']; lo=r['bounds_metres']['min']; hi=r['bounds_metres']['max']; length=hi[0]-lo[0]; span=max(hi[0]-lo[0],hi[1]-lo[1])
    cat=r['category']
    if cat=='Train': ppm=min(30/length,2.2)
    elif cat=='Carriage': ppm=30/length
    elif cat=='Road': ppm=min(27/length,2.5)
    elif cat=='Ship': ppm=min(62/span,1.6)
    else: ppm=min((30 if eid>=253 else 70)/span,1.15)
    entry={'engine_id':eid,'name':r['name'],'category':cat,'runtime_pixels_per_metre':ppm,'states':{}}
    for state,sheet in r['sprites'].items():
        src=Image.open(SOURCE/sheet['file']).convert('RGBA'); srcmask=Image.open(SOURCE/sheet['company_mask']).convert('L')
        factor=ppm*4/sheet['pixels_per_metre']; cell=sheet['cell_size']; n=round(cell*factor)
        sprites=[]
        for view in sorted(sheet['views'],key=lambda v:v['direction']):
            x,y,w,h=view['rect']; ox,oy=view['origin_px']
            im=src.crop((x,y,x+w,y+h)).resize((n,n),Image.Resampling.LANCZOS)
            mask=srcmask.crop((x,y,x+w,y+h)).resize((n,n),Image.Resampling.LANCZOS)
            anchor=(round((ox-x)*n/cell),round((oy-y)*n/cell))
            bb=im.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox(); assert bb,(eid,state,view['direction'])
            bb=(bb[0]//4*4,bb[1]//4*4,math.ceil(bb[2]/4)*4,math.ceil(bb[3]/4)*4)
            im=im.crop(bb); mask=mask.crop(bb)
            sprites.append({'image':im,'mask':mask,'width':im.width//4,'height':im.height//4,
                            'offset':[round((bb[0]-anchor[0])/4),round((bb[1]-anchor[1])/4)],'direction':view['direction']})
        group={'name':f'fh_{eid:03d}_{state}','engine_id':eid,'state':state,'sprites':sprites,
               'width':sum(s['width']+2 for s in sprites),'height':max(s['height'] for s in sprites)+2}
        groups.append(group); entry['states'][state]=group['name']
    if eid<116: entry.update(feature='FEAT_TRAINS',feature_id=eid,sprite_constant='SPRITE_ID_NEW_TRAIN')
    elif eid<204: entry.update(feature='FEAT_ROADVEHS',feature_id=eid-116,sprite_constant='SPRITE_ID_NEW_ROADVEH')
    elif eid<215: entry.update(feature='FEAT_SHIPS',feature_id=eid-204,sprite_constant='SPRITE_ID_NEW_SHIP')
    else: entry.update(feature='FEAT_AIRCRAFT',feature_id=eid-215,sprite_constant='SPRITE_ID_NEW_AIRCRAFT')
    mapping.append(entry)

page=x=y=rowheight=0
for group in groups:
    assert group['width']<=1024 and group['height']<=128
    if x+group['width']>1024: x=0; y+=rowheight; rowheight=0
    if y+group['height']>1024: page+=1; x=y=rowheight=0
    group['page']=page
    sx=x
    for s in group['sprites']:
        s['rect']=[sx,y,s['width'],s['height'],*s['offset']]; sx+=s['width']+2
    x+=group['width']; rowheight=max(rowheight,group['height'])

for page in range(page+1):
    subset=[g for g in groups if g['page']==page]
    height=max(s['rect'][1]+s['height']+2 for g in subset for s in g['sprites'])
    for scale in (1,2,4):
        im=Image.new('RGBA',(1024*scale,height*scale)); masks=palette_image(im.size)
        for group in subset:
            for s in group['sprites']:
                x,y,w,h,dx,dy=s['rect']; size=(w*scale,h*scale)
                image=s['image'].resize(size,Image.Resampling.LANCZOS)
                mask=s['mask'].resize(size,Image.Resampling.LANCZOS)
                im.paste(image,(x*scale,y*scale))
                pm=palette_image(size); pm.putdata([202 if v>127 else 0 for v in mask.getdata()]); masks.paste(pm,(x*scale,y*scale))
        im.save(GAME/f'fleet-{page}-{scale}x.png'); masks.save(GAME/f'fleet-{page}-mask-{scale}x.png')
        if scale==1:
            fb=fallback(im); fb.putdata([m or v for m,v in zip(masks.getdata(),fb.getdata())]); fb.save(GAME/f'fleet-{page}-8bpp.png')
    print('ATLAS_PAGE',page,flush=True)

(GAME/'lang').mkdir(exist_ok=True)
(GAME/'lang/english.lng').write_text('##grflangid 0x01\nSTR_NAME :TTD Future Heritage - full fleet\nSTR_DESC :Imported 256-vehicle Future Heritage model pack. Graphics-only properties; native vehicle mechanics retained. All climates. Source GLBs and credits supplied.\n')
nml=['grf { grfid: "FH\\01\\01"; name: string(STR_NAME); desc: string(STR_DESC); version: 1; min_compatible_version: 1; }']
palette_image((1,1)).save(GAME/'blank.png')
nml+=['spriteset(fh_baked_rotor, "blank.png") { [0,0,1,1,0,0] }']
for group in groups:
    name=group['name']; page=group['page']
    nml.append(f'spriteset({name}, "fleet-{page}-8bpp.png") {{')
    nml.extend('  ['+', '.join(map(str,s['rect']))+', NOCROP]' for s in group['sprites']); nml.append('}')
    for scale,zoom in ((1,'NORMAL'),(2,'IN_2X'),(4,'IN_4X')):
        nml.append(f'alternative_sprites({name}, ZOOM_LEVEL_{zoom}, BIT_DEPTH_32BPP, "fleet-{page}-{scale}x.png", "fleet-{page}-mask-{scale}x.png") {{')
        nml.extend('  ['+', '.join(str(v*scale) for v in s['rect'])+', NOCROP]' for s in group['sprites']); nml.append('}')
for entry in mapping:
    eid=entry['engine_id']; states=entry['states']
    if 'empty' in states:
        graphic=f'fh_{eid:03d}_cargo'; empty=states['empty']; loaded=states['loaded']
        nml.append(f'spritegroup {graphic} {{ loading: [{empty}, {loaded}]; loaded: [{empty}, {loaded}]; }}')
        purchase=empty
    else: graphic=purchase=states['default']
    nml.append(f'item({entry["feature"]}, fh_vehicle_{eid:03d}, {entry["feature_id"]}) {{')
    nml.append(f'  property {{ sprite_id: {entry["sprite_constant"]}; }}')
    nml.append(f'  graphics {{ default: {graphic}; purchase: {purchase};'+(' rotor: fh_baked_rotor;' if eid>=253 else '')+' }\n}')
(GAME/'future-heritage.nml').write_text('\n'.join(nml)+'\n')
subprocess.run([sys.executable,'-m','nml.main','--grf','future-heritage.grf','future-heritage.nml'],cwd=GAME,check=True)
for group in groups:
    for s in group['sprites']: del s['image'],s['mask']
(OUT/'runtime-mapping.json').write_text(json.dumps(mapping,indent=2))
(OUT/'sprite-manifest.json').write_text(json.dumps(groups,indent=2))
meta={'engines':len(mapping),'states':len(groups),'directions':sum(len(g['sprites']) for g in groups),
      'variants_per_direction':['8bpp normal','RGBA normal','RGBA 2x','RGBA 4x'],
      'grf_bytes':(GAME/'future-heritage.grf').stat().st_size,'sha256':hashlib.sha256((GAME/'future-heritage.grf').read_bytes()).hexdigest(),
      'property_changes':['sprite_id only; existing vehicle IDs'],'helicopter_rotors':'Supplied rotor is baked into the body sheets; duplicate native overlay suppressed. No new rotor animation is claimed.'}
(OUT/'fleet-build.json').write_text(json.dumps(meta,indent=2)); print(json.dumps(meta),flush=True)
