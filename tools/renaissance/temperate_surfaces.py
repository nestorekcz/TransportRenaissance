"""Editable procedural materials for fields and retaining-wall sprite masks.
Native masks/anchors are retained under the supplied OpenGFX GPL provenance.
"""
import math
import re
from PIL import Image,ImageFilter
from temperate_plan import WORK

def surfaces(original):
    cache={};rows=[]
    def tile(key,rec,category,field_stage=None,**target):
        if rec['file'] not in cache:cache[rec['file']]=Image.open(WORK/'tools/sources/opengfx'/rec['file'])
        src=cache[rec['file']];x,y,w,h,dx,dy=rec['rect']
        raw=src.crop((x,y,x+w,y+h));alpha=raw.point(lambda v:255 if v else 0,'L').resize((w*4,h*4),Image.Resampling.NEAREST)
        shade=raw.convert('RGB').resize(alpha.size,Image.Resampling.BILINEAR);im=Image.new('RGBA',alpha.size);p=im.load();a=alpha.load();q=shade.load()
        for yy in range(im.height):
            for xx in range(im.width):
                if not a[xx,yy]:continue
                u=(xx/4+dx)/2;v=yy/4+dy;tx=(v-u)/2;ty=(v+u)/2
                grain=((xx*73856093^yy*19349663)%127)/127-.5
                if field_stage is not None:
                    stage=field_stage;soil=(129,109,78);crop=(100+stage*9,119+stage*5,60+stage*3)
                    if stage<2:crop=(133,112,79)
                    row=math.cos(ty*math.tau/1.6);t=.25+.55*max(0,row)
                    colour=[soil[k]*(1-t)+crop[k]*t for k in range(3)]
                    colour=[c+grain*4 for c in colour]
                else:
                    # Match the pale concrete used by the modeled bridge piers.
                    light=sum(q[xx,yy])/765;shade_factor=.72+.32*light
                    joint=(yy%18<1 or (xx+(yy//18%2)*13)%28<1)
                    colour=[c*shade_factor+grain*3-(13 if joint else 0) for c in (173,170,154)]
                p[xx,yy]=(*[max(0,min(255,round(c))) for c in colour],255)
        rows.append({'key':key,'kind':'procedural-material','category':category,'source_model':'field-soil-crop-material' if field_stage is not None else 'retaining-wall-material',
                     'legacy':rec,'image':im,'mask':Image.new('L',im.size),'offset':[dx,dy],**target})
    for sid in range(4126,4297):tile(str(sid),original[sid],'farmland',field_stage=(sid-4126)//19,sprite_id=sid,ground=True)
    for sid in list(range(990,1004))+list(range(1821,1947))+list(range(1954,1961))+list(range(1975,1989)):
        tile(str(sid),original[sid],'foundations',sprite_id=sid)
    text=(WORK/'tools/sources/opengfx/sprites/extra/extra-foundations.pnml').read_text().split('if (climate == CLIMATE_ARCTIC)')[0]
    pattern=r'\[\s*(-?\d+),\s*(-?\d+),\s*(\d+),\s*(\d+),\s*(-?\d+),\s*(-?\d+),[^\]]*"([^"]+)"\]'
    for i,m in enumerate(re.finditer(pattern,text)):
        rec={'file':m[7],'rect':[int(m[k]) for k in range(1,7)]}
        tile(f'FOUNDATIONS_SLOPES_HALFTILES:{i}',rec,'foundations',feature='FOUNDATIONS_SLOPES_HALFTILES',index=i)
    # Calm, blended banks remove isolated beach/water pixels at maximum zoom.
    # Preserve the native alpha geometry and draw origins, including steep shores.
    def shore(key,rec,**target):
        x,y,w,h,dx,dy=rec['rect'];raw=Image.open(WORK/'tools/sources/opengfx'/rec['file']).crop((x,y,x+w,y+h))
        alpha=raw.point(lambda v:255 if v else 0,'L').resize((w*4,h*4),Image.Resampling.NEAREST)
        rgb=raw.convert('RGB');water=Image.new('L',raw.size);grass=Image.new('L',raw.size)
        water.putdata([255 if idx and b>r*1.3 else 0 for idx,(r,g,b) in zip(raw.getdata(),rgb.getdata())]);grass.putdata([255 if idx and g>r*1.15 and b<g*.9 else 0 for idx,(r,g,b) in zip(raw.getdata(),rgb.getdata())])
        valid=raw.point(lambda v:255 if v else 0,'L').filter(ImageFilter.GaussianBlur(.8))
        def normalised_blur(mask):
            blur=mask.filter(ImageFilter.GaussianBlur(.8));blur.putdata([min(255,round(v*255/max(1,a))) for v,a in zip(blur.getdata(),valid.getdata())]);return blur.resize(alpha.size,Image.Resampling.BICUBIC)
        water=normalised_blur(water);grass=normalised_blur(grass)
        im=Image.new('RGBA',alpha.size);pixels=[]
        for i,(a,b,opacity) in enumerate(zip(water.getdata(),grass.getdata(),alpha.getdata())):
            wa=a/255;gr=b/255;total=max(1,wa+gr);wa/=total;gr/=total;be=1-wa-gr
            noise=math.sin((i%im.width)/4*.5+(i//im.width)/4*.8)*1.2
            pixels.append((*[round(wa*c+gr*d+be*e+noise) for c,d,e in zip((66,112,129),(104,125,76),(160,151,116))],opacity))
        im.putdata(pixels)
        rows.append({'key':key,'kind':'procedural-material','category':'shorelines','source_model':'shore-grass-sand-water-material','legacy':rec,
                     'image':im,'mask':Image.new('L',im.size),'offset':[dx,dy],'ground':True,**target})
    for sid in range(4062,4070):shore(str(sid),original[sid],sprite_id=sid)
    for i,(x,h,dy) in enumerate([(1276,15,0),(1356,31,-8),(558,23,0),(1196,47,-16),(878,31,-8),(1038,39,-8),(1118,31,-8),(1436,31,-8),(398,31,0),(798,31,0)]):
        shore(f'COAST_TILES_BASEGFX:{i}',{'file':'sprites/png/terrain/waterfeatures/seashore_temperate.gimp.png','rect':[x+1,1,64,h,-31,dy]},feature='COAST_TILES_BASEGFX',index=i)
    return rows
