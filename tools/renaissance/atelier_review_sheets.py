"""Readable review boards assembled from real mesh renders. GPL-2.0-only."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WORK=Path(__file__).resolve().parents[3]; OUT=WORK/'artifacts/atelier-r2'
INK='#243b3c'; MUTED='#637270'; PAPER='#edece5'; CARD='#f6f5ee'; ACCENT='#247b7e'
FONT='C:/Windows/Fonts/segoeui.ttf'; BOLD='C:/Windows/Fonts/seguisb.ttf'
def font(size,bold=False): return ImageFont.truetype(BOLD if bold else FONT,size)
def sheet(title,subtitle,height):
    im=Image.new('RGB',(1800,height),PAPER); d=ImageDraw.Draw(im)
    d.text((56,32),'RENAISSANCE ATELIER   /   REVISION 02',font=font(20,True),fill=ACCENT)
    d.text((54,66),title,font=font(47,True),fill=INK)
    d.text((56,126),subtitle,font=font(23),fill=MUTED)
    d.line((56,height-60,1744,height-60),fill='#cccec5',width=2)
    d.text((56,height-45),'Actual editable Blender models  /  studio views, not gameplay screenshots  /  demo review only',font=font(20),fill=MUTED)
    return im
def card(im,box,title,caption):
    d=ImageDraw.Draw(im); x,y,w,h=box
    d.rounded_rectangle((x,y,x+w,y+h),radius=18,fill=CARD)
    d.text((x+28,y+20),title,font=font(28,True),fill=INK)
    d.text((x+28,y+h-40),caption,font=font(20),fill=MUTED)
def place(im,name,view,box):
    src=Image.open(OUT/'studio'/f'{name}-{view}.png').convert('RGBA')
    src=src.crop(src.getchannel('A').getbbox()); x,y,w,h=box
    src.thumbnail((w,h),Image.Resampling.LANCZOS)
    im.paste(src,(x+(w-src.width)//2,y+(h-src.height)//2),src)

im=sheet('The road proposal','A continuous carriageway, clear kerbs and paving that belongs beside the houses.',1240)
for k,(name,title,caption) in enumerate([
    ('I10_road_10_urban','01  Straight','Regular dash spacing; stone paving and gutter drains'),
    ('I10_road_09_urban','02  Curved corner','Curved inner and outer kerbs; no square elbow'),
    ('I10_road_07_urban','03  T-junction','Rounded corner islands; clear intersection centre'),
    ('I07_road_intersection','04  Four-way junction','Matching road width and footway connections')]):
    x=56+(k%2)*858; y=190+(k//2)*480
    card(im,(x,y,830,452),title,caption); place(im,name,'perspective',(x+45,y+65,740,335))
im.save(OUT/'road-models.png')

im=sheet('The train models','A common cream and teal livery, with distinct locomotive, passenger and freight silhouettes.',1280)
for k,(name,title,caption) in enumerate([
    ('V01_meridian_diesel','01  Meridian diesel','Raised cab, cooling fans, louvres and buffers'),
    ('V02_passenger_coach','02  Passenger coach','Cream body, teal waist and dark continuous roof'),
    ('V03_hopper_empty','03  Empty hopper','Open freight body with external strengthening ribs'),
    ('V03_hopper_loaded','04  Loaded hopper','The same wagon with its visible coal load')]):
    x=56+(k%2)*858; y=190+(k//2)*500
    card(im,(x,y,830,472),title,caption)
    place(im,name,'perspective',(x+35,y+60,760,265))
    place(im,name,'side',(x+125,y+332,580,86))
im.save(OUT/'train-models.png')

im=sheet('The road-vehicle models','The existing demo models, shown clearly from three-quarter and side views.',900)
for k,(name,title,caption) in enumerate([
    ('V04_civic_bus','01  Civic bus','Rounded body, destination panel and passenger doors'),
    ('V05_parcel_truck','02  Parcel truck','Separate cab, box body and rear roller door')]):
    x=56+k*858; y=190
    card(im,(x,y,830,610),title,caption)
    place(im,name,'perspective',(x+35,y+72,760,345)); place(im,name,'side',(x+90,y+435,650,110))
im.save(OUT/'vehicle-models.png')

im=sheet('The railway proposal','Conventional ballasted track: timber sleepers, steel running surfaces and restrained weathering.',1220)
card(im,(56,190,940,930),'01  Turnout source proposal','Point motor and blade detail are proposal-only.')
place(im,'I11_turnout','perspective',(85,290,880,690))
card(im,(1024,190,720,451),'02  Straight','Raised ballast, rail fastenings and timber ties')
place(im,'I06_track_straight','perspective',(1060,255,648,325))
card(im,(1024,669,720,451),'03  Curve','Continuous curved rails and regular sleeper spacing')
place(im,'I11_track_2','perspective',(1060,734,648,325))
im.save(OUT/'railway-proposal.png')

im=sheet('The river-ferry model','An additional vehicle in the demo, shown at source-model scale.',900)
card(im,(56,190,1688,610),'01  River ferry','Passenger salon, upper deck, wheelhouse and deck rails')
place(im,'V06_river_ferry','perspective',(95,260,1000,430)); place(im,'V06_river_ferry','side',(1150,290,530,320))
im.save(OUT/'ferry-model.png')
print('REVIEW_SHEETS_READY',flush=True)
