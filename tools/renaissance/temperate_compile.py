"""Compile exact native sprite assignments, with separate sorting layers and zooms."""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from PIL import Image,ImageChops
from build_assets import fallback,palette_image
from temperate_plan import WORK,OUT,infrastructure,world,details
from temperate_surfaces import surfaces

p=argparse.ArgumentParser();p.add_argument('--partial',action='store_true');opt=p.parse_args()
GAME=OUT/'game';GAME.mkdir(parents=True,exist_ok=True)
def save_png(im,path):
    data=io.BytesIO();im.save(data,format='PNG');blob=data.getvalue()
    if not path.exists() or path.read_bytes()!=blob:path.write_bytes(blob)
original={}
for line in (WORK/'artifacts/opengfx-base.nfo').read_text().splitlines():
    m=re.match(r'^(\d+) (\S+\.png) 8bpp (-?\d+) (-?\d+) (\d+) (\d+) (-?\d+) (-?\d+) normal',line)
    if m:original[int(m[1])]={'file':m[2],'rect':list(map(int,m.groups()[2:]))}
records={('',r['id']):r for r in json.loads((OUT/'renders.json').read_text())}
airport_original=[]
for m in re.finditer(r'\[\s*(-?\d+),\s*(-?\d+),\s*(\d+),\s*(\d+),\s*(-?\d+),\s*(-?\d+),[^\]]*"([^"]+)"\]',(WORK/'tools/sources/opengfx/sprites/extra/extra-openttd-airport.pnml').read_text()):
    airport_original.append({'file':m[7],'rect':[int(m[k]) for k in range(1,7)]})
for directory in ('world','details'):
    if (OUT/directory/'renders.json').exists():
        records.update({(directory,r['id']):r for r in json.loads((OUT/directory/'renders.json').read_text())})
entries=[]
for job in infrastructure()+world()+details():
    name='W_'+job['key'].replace(':','_')
    record_key=(job.get('source_dir',''),name)
    if record_key not in records:
        if opt.partial:continue
        raise RuntimeError('Missing '+name)
    row=records[record_key];source=OUT/job.get('source_dir','');im=Image.open(source/'renders'/row['file']).convert('RGBA')
    im=im.resize((384,384),Image.Resampling.LANCZOS)
    origin=[round(v*4/6) for v in row['origin_px']]
    mask=Image.open(source/'masks'/f'{name}-0001.png').convert('L').resize(im.size,Image.Resampling.LANCZOS)
    bounds=im.getchannel('A').getbbox();assert bounds,name
    bounds=(bounds[0]//4*4,bounds[1]//4*4,math.ceil(bounds[2]/4)*4,math.ceil(bounds[3]/4)*4)
    im=im.crop(bounds);mask=mask.crop(bounds)
    offset=[(bounds[0]-origin[0])//4,(bounds[1]-origin[1])//4]
    if job.get('sprite_id')==1442:
        # The lift is positioned relative to its parent sprite's top-left.
        # Retain that screen-space reference while changing the office mesh.
        x,y,w,h,ox,oy=original[1442]['rect'];canvas=Image.new('RGBA',(w*4,h*4));cc=Image.new('L',canvas.size)
        canvas.alpha_composite(im,((offset[0]-ox)*4,(offset[1]-oy)*4));cc.paste(mask,((offset[0]-ox)*4,(offset[1]-oy)*4))
        im,mask,offset=canvas,cc,[ox,oy]
    dx,dy=job.get('anchor',(0,0));offset[0]-=2*(dy-dx);offset[1]-=dx+dy
    if job.get('feature')=='ROAD_STOPS':
        dx,dy=[(13,0),(0,0),(0,0),(0,13)][job['layout']]
        offset[0]-=2*(dy-dx);offset[1]-=dx+dy
    if job.get('ground'):
        src=airport_original[job['index']] if job.get('feature')=='AIRPORTS' else original[job['sprite_id']];x,y,w,h,ox,oy=src['rect']
        raw=Image.open(WORK/'tools/sources/opengfx'/src['file']).crop((x,y,x+w,y+h))
        alpha=raw.point(lambda v:255 if v else 0,'L').resize((w*4,h*4),Image.Resampling.NEAREST)
        paved=job['kind'] in ('airport_ground','town_ground','industry_ground') and job.get('family') not in ('forest','farm') and 'STADIUM' not in job.get('name','')
        bg=Image.new('RGBA',alpha.size,(184,190,187,255) if paved else (104,125,76,255))
        bg.alpha_composite(im,((offset[0]-ox)*4,(offset[1]-oy)*4));bg.putalpha(alpha)
        if job.get('sprite_id') in (2077,2669,2670,2671,2672):
            # Reuse the approved Meadow material instead of exposing a lighter
            # Blender preview ground at the boundary of forests and airfields.
            meadow=Image.open(WORK/'artifacts/assets/meadow-4x.png').convert('RGBA').crop((0,147*4,64*4,178*4))
            bg=meadow.resize(alpha.size,Image.Resampling.LANCZOS);bg.putalpha(alpha)
        im=bg;mask=Image.new('L',im.size);offset=[ox,oy]
    entries.append({**job,'source_model':name,'image':im,'mask':mask,'offset':offset})

# Native technology variants share the same approved station/depot buildings.
# Keep their separate sprite IDs, including the intentional transparent layers.
by_id={e.get('sprite_id'):e for e in entries if 'sprite_id' in e}
old=json.loads((WORK/'artifacts/atelier-r2/demo-coverage.json').read_text());old={r['sprite_id']:r for r in old}
old_atlas=Image.open(WORK/'artifacts/atelier-r2/game/atelier-4x.png').convert('RGBA')
alias={**{i:i+19 for i in range(1328,1332)},**{i:1063+i-base for base in (1145,1227) for i in range(base,base+6)},**{i:1069+i-base for base in (1151,1233) for i in range(base,base+18)}}
for sid,source_id in alias.items():
    if source_id in by_id:
        e={**by_id[source_id],'key':str(sid),'sprite_id':sid,'source_sprite':source_id};entries.append(e)
    elif source_id in old:
        r=old[source_id];x,y,w,h,dx,dy=r['export_rect'];im=old_atlas.crop((x*4,y*4,(x+w)*4,(y+h)*4))
        entries.append({'key':str(sid),'sprite_id':sid,'source_model':r['source_asset'],'source_sprite':source_id,'image':im,'mask':Image.new('L',im.size),'offset':[dx,dy],'category':'station-and-road-variants'})
entries.extend(surfaces(original))
assert len({e['key'] for e in entries})==len(entries),'Duplicate target sprite'

pages=[]
for e in entries:
    w,h=e['image'].width//4,e['image'].height//4
    if not pages or pages[-1]['x']+w+2>1024:
        if pages:
            pages[-1]['y']+=pages[-1]['rowh']+2;pages[-1]['x']=0;pages[-1]['rowh']=0
    if not pages or pages[-1]['y']+h+2>1024:
        pages.append({'x':0,'y':0,'rowh':0,'entries':[]})
    page=pages[-1];e['rect']=[page['x'],page['y'],w,h,*e['offset']];e['page']=len(pages)-1
    page['entries'].append(e);page['x']+=w+2;page['rowh']=max(page['rowh'],h)
for index,page in enumerate(pages):
    ph=page['y']+page['rowh']+2
    for scale in (1,2,4):
        atlas=Image.new('RGBA',(1024*scale,ph*scale));masks=palette_image(atlas.size)
        for e in page['entries']:
            x,y,w,h,*_=e['rect'];size=(w*scale,h*scale)
            im=e['image'].resize(size,Image.Resampling.LANCZOS)
            if e.get('ground'):im.putalpha(e['image'].getchannel('A').resize(size,Image.Resampling.NEAREST))
            atlas.paste(im,(x*scale,y*scale))
            m=e['mask'].resize(size,Image.Resampling.LANCZOS);mi=palette_image(size);mi.putdata([202 if v>127 else 0 for v in m.getdata()]);masks.paste(mi,(x*scale,y*scale))
        save_png(atlas,GAME/f'world-{index}-{scale}x.png');save_png(masks,GAME/f'world-{index}-mask-{scale}x.png')
        if scale==1:
            fb=fallback(atlas);fb.paste(masks,(0,0),masks.point(lambda v:255 if v else 0,'L'));save_png(fb,GAME/f'world-{index}-8bpp.png')
# The game's buoy station draws the shared icon (693), not the unused legacy
# buoy slot (4076). Reuse its new model pixels with the station's (4,-1) origin.
buoy=next(e for e in entries if e.get('sprite_id')==4076)
buoy_rect=list(buoy['rect']);buoy_rect[4]+=10;buoy_rect[5]+=13
entries.append({**buoy,'key':'693','sprite_id':693,'source_sprite':4076,'rect':buoy_rect,'offset':buoy_rect[4:],'category':'water-transport'})
(GAME/'lang').mkdir(exist_ok=True)
(GAME/'lang/english.lng').write_text('##grflangid 0x01\nSTR_NAME :Renaissance - Temperate world\nSTR_DESC :Editable models, connected infrastructure and exact native sprite layers. Graphics only.\n')
nml=['grf { grfid: "TW\\01\\01"; name: string(STR_NAME); desc: string(STR_DESC); version: 1; min_compatible_version: 1; }','if (climate == CLIMATE_TEMPERATE) {']
for e in entries:
    name='sp_'+e['key'].replace(':','_');page=e['page'];r=e['rect'];coords=', '.join(map(str,r))
    if e.get('feature')=='COAST_TILES_BASEGFX':continue
    if 'feature' in e:begin=f'replacenew {name}({e["feature"]}, "world-{page}-8bpp.png", {e["index"]})'
    else:begin=f'replace {name}({e["sprite_id"]}, "world-{page}-8bpp.png")'
    nml.append(begin+' { ['+coords+', NOCROP] }')
    for scale,zoom in [(1,'NORMAL'),(2,'IN_2X'),(4,'IN_4X')]:
        coords=', '.join(str(v*scale) for v in r)
        nml.append(f'alternative_sprites({name}, ZOOM_LEVEL_{zoom}, BIT_DEPTH_32BPP, "world-{page}-{scale}x.png", "world-{page}-mask-{scale}x.png") {{ [{coords}, NOCROP] }}')
coasts=sorted((e for e in entries if e.get('feature')=='COAST_TILES_BASEGFX'),key=lambda e:e['index'])
if coasts:
    assert len(coasts)==10
    nml.append('replacenew shore_bundle(COAST_TILES_BASEGFX, "") {')
    for e in coasts:nml.append('['+', '.join(map(str,e['rect']))+f', NOCROP, "world-{e["page"]}-8bpp.png"]')
    nml.append('}')
    for scale,zoom in [(1,'NORMAL'),(2,'IN_2X'),(4,'IN_4X')]:
        nml.append(f'alternative_sprites(shore_bundle, ZOOM_LEVEL_{zoom}, BIT_DEPTH_32BPP, "") {{')
        for e in coasts:nml.append('['+', '.join(str(v*scale) for v in e['rect'])+f', NOCROP, "world-{e["page"]}-{scale}x.png"]')
        nml.append('}')
nml.append('}')
(GAME/'temperate-world.nml').write_text('\n'.join(nml)+'\n')
subprocess.run([sys.executable,'-m','nml.main','--grf','temperate-world.grf','temperate-world.nml'],cwd=GAME,check=True)
for e in entries:del e['image'],e['mask']
(OUT/'coverage.json').write_text(json.dumps(entries,indent=2))
report={'sprites':len(entries),'partial':opt.partial,'pages':len(pages),'sha256':hashlib.sha256((GAME/'temperate-world.grf').read_bytes()).hexdigest(),'grf_bytes':(GAME/'temperate-world.grf').stat().st_size}
(OUT/'build.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
