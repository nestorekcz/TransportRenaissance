"""Isolated native import checks and a playable fleet-enabled art demo."""
import argparse
import json
from pathlib import Path
import re
import shutil
import time
import atelier_runtime as runtime
import atelier_verify as verify

WORK=Path(__file__).resolve().parents[3]; OUT=WORK/'artifacts/atelier-future-heritage'; RUN=OUT/'runtime'
runtime.OUT=OUT; runtime.RUN=RUN
verify.OUT=OUT; verify.SOURCE=RUN; verify.RESULTS=OUT/'verification'
verify.RESULTS.mkdir(exist_ok=True)

def stage():
    shutil.copy2(WORK/'artifacts/atelier-engine-build/openttd.exe',RUN/'openttd.exe')
    shutil.copy2(OUT/'game/future-heritage/future-heritage.grf',RUN/'newgrf/future-heritage.grf')
    cfg=(WORK/'artifacts/atelier-r2/runtime/openttd.cfg').read_text()
    (RUN/'before.cfg').write_text(cfg)
    cfg+='\n[newgrf]\nfuture-heritage.grf =\n'
    (RUN/'openttd.cfg').write_text(cfg)
    (RUN/'indexed.cfg').write_text(cfg.replace('32bpp-anim','8bpp-optimized'))
    script=(WORK/'TransportRenaissance/media/renaissance/atelier-demo/main.nut').read_text()
    script=script.replace('GSCompany.SetName("Aurelia Regional Transport");','GSCompany.SetName("Aurelia Regional Transport");\n            GSCompany.SetPrimaryLiveryColour(GSCompany.LS_DEFAULT, GSCompany.COLOUR_DARK_BLUE);')
    (RUN/'game/atelier/main.nut').write_text(script)
    (RUN/'scripts/game_start.scr').write_text('unpause\nschedule on-next-calendar-month scripts/finish.scr\n')
    print('FLEET_RUNTIME_STAGED',flush=True)

def generate(): runtime.generate()

def audit_one(label,save,config):
    log=RUN/(label+'.log')
    (RUN/'scripts/game_start.scr').write_text(f'script {label}.log\natelier_fleet_audit\nscript\nquit\n')
    p=runtime.launch(save,config)
    p.wait(timeout=90)
    assert p.returncode==0,(label,(RUN/'stderr.log').read_text())
    text=log.read_text(); data={}
    for line in text.splitlines():
        if 'FH_ENGINE ' not in line: continue
        fields=dict(re.findall(r'(\w+)=([\w.-]+)',line)); data[int(fields['id'])]=fields
    assert len(data)==256,(label,len(data))
    shutil.copy2(log,OUT/'verification'/log.name)
    return data

def audit():
    before=audit_one('baseline-fleet-audit','save/atelier-roads-r2.sav','before.cfg')
    after=audit_one('imported-fleet-audit','save/atelier-demo.sav','openttd.cfg')
    mismatches=[]
    for eid,row in after.items():
        assert row['valid']=='8',(eid,row)
        assert row['provider']=='01014846',(eid,row['provider'])
        for field,value in row.items():
            if field not in ('provider','valid') and value!=before[eid][field]: mismatches.append([eid,field,before[eid][field],value])
    result={'engines':len(after),'resolved_directions':sum(int(r['valid']) for r in after.values()),'non_graphics_property_differences':mismatches,'engines_after':after}
    (OUT/'verification/native-engine-audit.json').write_text(json.dumps(result,indent=2))
    assert not mismatches,mismatches[:20]
    print('NATIVE_ENGINE_AUDIT_PASS',len(after),flush=True)

def capture():
    for label,zoom,x,y in [('fleet-overview',2,56,53),('fleet-trains',0,65,44),('fleet-road-vehicles',0,64,57),('fleet-ferry',0,68,64),('fleet-houses',0,55,52),('fleet-diesel',0,59,44),('fleet-freight',0,73,43)]:
        runtime.capture(label,zoom,x,y)
    runtime.capture('fleet-indexed',2,56,53,'indexed.cfg')
    for typ,label in [(0,'train-purchase'),(1,'road-purchase'),(2,'ship-purchase'),(3,'aircraft-purchase')]:
        target=RUN/'screenshot'/f'{label}.png'
        if target.exists(): target.unlink()
        (RUN/'scripts/game_start.scr').write_text(f'pause\natelier_view 2 56 53\natelier_fleet_shop {typ}\nscreenshot viewport no_con {label}\n')
        p=runtime.launch('save/atelier-demo.sav')
        try:
            for k in range(300):
                if target.exists():
                    time.sleep(.5); shutil.copy2(target,OUT/target.name); break
                if p.poll() is not None: raise RuntimeError((RUN/'stderr.log').read_text())
                time.sleep(.1)
            else: raise RuntimeError('Missing '+label)
        finally: p.terminate(); p.wait(timeout=15)
        print('CAPTURED',label,flush=True)

def performance():
    rows=[]
    for zoom in (2,0):
        run=verify.prepare(f'fleet-z{zoom}')
        (run/'scripts/game_start.scr').write_text(f'atelier_view {zoom} 56 53\nunpause\nschedule on-next-calendar-month scripts/measure.scr\n')
        (run/'scripts/measure.scr').write_text('script metrics.log\nfps\nscript\nquit\n')
        rows.append({'zoom':zoom,**verify.execute(run,(RUN/'save/atelier-demo.sav').resolve())})
        (OUT/'verification/performance.json').write_text(json.dumps(rows,indent=2)); print('PERFORMANCE_SAMPLE',zoom,flush=True)

def compatibility():
    verify.compatibility()

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['stage','generate','audit','capture','performance','compatibility']); args=p.parse_args()
    globals()[args.action]()
