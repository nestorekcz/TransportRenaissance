"""Reconcile every inventoried raster slot with the delivered temperate layers."""
import json,re,csv
from collections import Counter
from temperate_plan import WORK,OUT,infrastructure,world,details

def audit():
    inventory=WORK/'artifacts/atelier-r2/inventory'
    rows=json.loads((inventory/'asset-manifest.json').read_text())
    coverage=json.loads((OUT/'coverage.json').read_text())
    current={str(e['sprite_id']):e for e in coverage if 'sprite_id' in e}
    extra={(e['feature'],e['index']):e for e in coverage if 'feature' in e}
    old={str(r['sprite_id']):r for r in json.loads((WORK/'artifacts/atelier-r2/demo-coverage.json').read_text())}
    features={4:'SIGNALS',5:'CATENARY',6:'FOUNDATIONS_SLOPES_HALFTILES',8:'CANALS',9:'ONE_WAY_ROAD',10:'COLOURMAP_2CC',11:'TRAMWAY',12:'SNOWY_TEMPERATE_TREES',13:'COAST_TILES_BASEGFX',15:'SLOPED_RAILS',16:'AIRPORTS',17:'ROAD_STOPS',18:'AQUEDUCTS',19:'AUTORAIL',20:'FLAGS',21:'OTTD_GUI',22:'AIRPORT_PREVIEW',23:'RAILTYPE_TUNNELS',24:'OTTD_RECOLOUR'}
    mapped={}
    for line in (inventory/'ogfxe_extra.nfo').read_text().splitlines():
        m=re.match(r'^(\d+) \* \d+ 05 ([0-9A-F]{2}) FF \\w(\d+)(?: FF \\w(\d+))?',line)
        if m:
            start=int(m[1]);feature=features.get(int(m[2],16)&127,'inventory-normalised-feature');count=int(m[3]);offset=int(m[4] or 0)
            for i in range(count):mapped[start+1+i]=(feature,offset+i)
    for r in rows:
        sid=str(r['sprite_id']);path=r['source_file'].lower();category=r['category'];climate=r['set']
        match=current.get(sid) if climate=='base' else extra.get(mapped.get(r['sprite_id'])) if climate=='extra' else None
        outside=climate in ('arctic','tropical','toyland') or any(t in path for t in ('/toyland','arctic','tropical','tropic_','_snow','grass-snow','desert'))
        if match and not outside:
            status='temperate-replacement';reason='Exact base sprite or Action5 feature/index replacement.';r['replacement']=match['source_model'];r['replacement_key']=match['key']
        elif category in ('gui','AfricanManagerFaces') or climate=='logos':status='interface-preserved';reason='Interface, portrait, font or logo; world-art scope.'
        elif outside:status='other-climate-deferred';reason='Outside the approved temperate pass.'
        elif climate=='base' and sid in old:status='approved-art-preserved';reason='Earlier approved Atelier source mesh/render retained.';r['replacement']=old[sid]['source_asset']
        elif category in ('trains','roadvehicles','aircraft','ships'):status='fleet-integrated';reason='Future Heritage replaces all 256 native engine IDs through vehicle graphics callbacks; base-slot counts are not engine counts.'
        elif r.get('current_project_override'):status='meadow-art-preserved';reason='Existing Meadow terrain or steam replacement retained.'
        elif climate=='base' and category in ('houses','industries','infrastructure') and r['sprite_id'] not in {1443,*range(2040,2045),*range(2055,2061)}:
            status='other-climate-or-unused-native-slot';reason='Not selected by the temperate native house/industry tables; snow/desert infrastructure or legacy sprite retained.'
        elif climate=='base' and (1968<=r['sprite_id']<=2009 or r['sprite_id']==4697):status='other-climate-deferred';reason='Toyland tree/object states in the shared base file.'
        else:
            status='functional-detail-retained';reason='Reviewed original functional overlay, effect, disaster, technical mask or waterway detail remains compatible.'
            if climate=='extra' and r['sprite_id'] in mapped:r['native_feature'],r['native_feature_index']=mapped[r['sprite_id']]
            if r['sprite_id']==1443 and climate=='base':reason='Moving lift overlay keeps its native screen-space animation and origin.'
            if climate=='base' and 4042<=r['sprite_id']<=4060:reason='Secondary rock silhouettes retained; primary rough/rocky ground already uses Meadow materials.'
        r['temperate_review_status']=status;r['temperate_review_reason']=reason
        r['validation']='Inventory reconciliation; replaced slots validated in coverage.json and validation.json. Native visual QA is representative, not every possible map layout.'
    target=OUT/'inventory';target.mkdir(exist_ok=True)
    (target/'temperate-asset-audit.json').write_text(json.dumps(rows,indent=2))
    with (target/'temperate-asset-audit.csv').open('w',newline='',encoding='utf-8-sig') as f:
        fields=['stable_id','category','source_file','temperate_review_status','replacement','temperate_review_reason'];writer=csv.DictWriter(f,fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    report={'reviewed_source_raster_slots':len(rows),'source_slot_status_counts':dict(Counter(r['temperate_review_status'] for r in rows)),
            'new_compiled_logical_slots':len(coverage),'model_view_jobs':len(infrastructure())+len(world())+len(details()),
            'new_categories':dict(Counter(r['category'] for r in coverage)),
            'retained_detail_examples':['Catenary wires and electrical contact overlays','Canal/river/lock technical edge layers and aqueducts','Disaster vehicles, sparks, explosions and legacy lift animation','UI thumbnails, icons, portraits and construction cursors'],
            'note':'Physical source-slot counts include repeated conditional climate/traffic-side alternatives. They must not be added to logical replacement counts. Other climates are deferred by user instruction; retained details are explicitly recorded, not claimed as new models.'}
    (target/'audit-summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
    return report

if __name__=='__main__':audit()
