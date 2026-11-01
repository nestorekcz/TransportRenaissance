"""Import the user-supplied complete fleet without modifying its source files."""
import hashlib
import argparse
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT.parent
OUT=WORK/'artifacts/atelier-future-heritage'
RECEIPT=ROOT/'media/renaissance/atelier-demo/fleet-input.json'
receipt=json.loads(RECEIPT.read_text())
p=argparse.ArgumentParser(); p.add_argument('--archive',type=Path)
p.add_argument('--assets-only',action='store_true',help='Import source assets without copying a previously staged review runtime.')
args=p.parse_args()
candidates=[WORK/receipt['archive'],OUT/'imports'/receipt['archive']]
archive=args.archive.resolve() if args.archive else next((path for path in candidates if path.exists()),None)
if archive is None or not archive.is_file():
    p.error('Supply the original TTD_Future_Heritage_Full_Fleet.zip with --archive; see fleet-input.json for its checksum.')
assert archive.name=='TTD_Future_Heritage_Full_Fleet.zip'
sha=hashlib.sha256(archive.read_bytes()).hexdigest()
assert sha==receipt['sha256'],'Archive differs from its recorded delivery checksum'
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'imports').mkdir(exist_ok=True)
if archive.resolve()!=(OUT/'imports'/archive.name).resolve(): shutil.copy2(archive,OUT/'imports'/archive.name)
FLEET=OUT/'source/fleet'; FLEET.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None,'Archive CRC failure'
    for info in z.infolist():
        target=(FLEET/info.filename).resolve()
        assert target==FLEET.resolve() or FLEET.resolve() in target.parents,'Unsafe archive member'
    z.extractall(FLEET)
manifest=json.loads((FLEET/'fleet_manifest.json').read_text())
assert len(manifest['records'])==256
models=[]
for r in manifest['records']:
    model=FLEET/r['model']
    assert hashlib.sha256(model.read_bytes()).hexdigest()==r['sha256'],r['engine_id']
    for state,key in [('default','model'),('empty','empty_model')]:
        if r.get(key):
            path=FLEET/r[key]
            models.append({'engine_id':r['engine_id'],'name':r['name'],'category':r['category'],
                           'state':state,'file':r[key],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
assert len(models)==344
(OUT/'import-manifest.json').write_text(json.dumps({'archive':archive.name,'archive_sha256':sha,
    'original_archive':str(archive),'base_models':256,'empty_variants':88,'imported_models':models,
    'source_preservation':'All GLBs, materials, sprites, masks, metadata and source documents extracted unchanged.'},indent=2))
if not args.assets_only and not (OUT/'runtime/save/atelier-roads-r2.sav').exists():
    for folder in ('runtime','game'):
        shutil.copytree(WORK/'artifacts/atelier-r2'/folder,OUT/folder,dirs_exist_ok=True)
    # Retain the previous save; a new fleet-enabled demo gets its own save file.
    save=OUT/'runtime/save/atelier-demo.sav'
    if save.exists(): shutil.move(str(save),str(OUT/'runtime/save/atelier-roads-r2.sav'))
print('IMPORTED',len(models),'models from',archive.name,flush=True)
