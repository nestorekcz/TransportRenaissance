"""Stage and verify the road revision without modifying the approved v1 bundle."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT.parent
OLD=WORK/'artifacts/atelier'
OUT=WORK/'artifacts/atelier-r2'


def stage():
    OUT.mkdir(exist_ok=True)
    for folder in ('renders','masks','source','runtime'):
        shutil.copytree(OLD/folder,OUT/folder,dirs_exist_ok=True)
    for name in ('renders.json','scene-validation.json','scene-placements.json','tree-placements.json','hardware.json'):
        shutil.copy2(OLD/name,OUT/name)
    # Snapshot old art under another filename for an exact same-save comparison.
    runtime=OUT/'runtime'
    shutil.copy2(OLD/'game/renaissance-atelier.grf',runtime/'newgrf/atelier-v1.grf')
    cfg=(OLD/'runtime/openttd.cfg').read_text()
    (runtime/'before.cfg').write_text(cfg.replace('renaissance-atelier.grf =','atelier-v1.grf ='))
    print('REVISION_STAGED',OUT,flush=True)


def capture():
    import atelier_runtime as runtime
    runtime.OUT=OUT; runtime.RUN=OUT/'runtime'
    shutil.copy2(OUT/'game/renaissance-atelier.grf',runtime.RUN/'newgrf/renaissance-atelier.grf')
    for item in [('road-before',0,64,57,'before.cfg'),('road-after',0,64,57,'openttd.cfg'),
                 ('town-after',0,55,52,'openttd.cfg'),('overview-after',2,56,53,'openttd.cfg'),
                 ('rail-before',0,59,44,'before.cfg'),('rail-after',0,59,44,'openttd.cfg'),
                 ('vehicles-after',0,65,44,'openttd.cfg'),('indexed-after',2,56,53,'indexed.cfg')]:
        runtime.capture(*item)


def verify():
    import atelier_verify as verify
    verify.OUT=OUT; verify.SOURCE=OUT/'runtime'; verify.RESULTS=OUT/'verification'
    verify.RESULTS.mkdir(exist_ok=True)
    verify.performance(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('action',choices=['stage','capture','verify']); options=parser.parse_args()
    globals()[options.action]()
