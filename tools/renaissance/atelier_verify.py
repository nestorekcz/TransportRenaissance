"""Paired, native performance and save-compatibility checks. GPL-2.0-only."""
import ctypes
import argparse
from ctypes import wintypes
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
from verify_runtime import MemoryCounters

ROOT=Path(__file__).resolve().parents[2]; WORK=ROOT.parent
OUT=WORK/'artifacts/atelier'; SOURCE=OUT/'runtime'; RESULTS=OUT/'verification'
RESULTS.mkdir(exist_ok=True)

def prepare(name,baseline=False):
    run=RESULTS/name; run.mkdir(exist_ok=True)
    for folder in ('baseset','lang','newgrf','game'):
        shutil.copytree(SOURCE/folder,run/folder,dirs_exist_ok=True)
    for name in ('openttd.exe','libunwind.dll','libc++.dll','libwinpthread-1.dll'):
        if (SOURCE/name).exists(): shutil.copy2(SOURCE/name,run/name)
    shutil.copy2(SOURCE/('before.cfg' if baseline else 'openttd.cfg'),run/'openttd.cfg')
    (run/'scripts').mkdir(exist_ok=True); (run/'save').mkdir(exist_ok=True)
    return run

def execute(run,scene,timeout=150):
    peak=0; begin=time.perf_counter()
    with (run/'stdout.log').open('w') as out,(run/'stderr.log').open('w') as err:
        p=subprocess.Popen([str(run/'openttd.exe'),'-X','-x','-c','openttd.cfg','-g',str(scene),'-d','script=4'],cwd=run,stdout=out,stderr=err)
        while p.poll() is None:
            c=MemoryCounters(); c.cb=ctypes.sizeof(c)
            if ctypes.windll.psapi.GetProcessMemoryInfo(wintypes.HANDLE(p._handle),ctypes.byref(c),c.cb): peak=max(peak,c.PeakWorkingSetSize)
            if time.perf_counter()-begin>timeout:
                p.terminate(); p.wait(); raise RuntimeError('Timed out: '+str(run))
            time.sleep(.1)
    log=(run/'stderr.log').read_text(errors='replace')
    if p.returncode or 'Your script made an error' in log: raise RuntimeError(log[-3000:])
    movement={}
    for v,t in re.findall(r'ATELIER_TRAFFIC (\d+) tile=(\d+)',log): movement.setdefault(v,set()).add(int(t))
    return {'exit_code':p.returncode,'wall_seconds':round(time.perf_counter()-begin,3),'peak_working_set_bytes':peak,
            'metrics':(run/'metrics.log').read_text() if (run/'metrics.log').exists() else '',
            'distinct_tiles_per_powered_vehicle':{v:len(t) for v,t in movement.items()}}

def performance(repeats=2):
    results=[]; scene=(SOURCE/'save/atelier-demo.sav').resolve()
    for zoom,repeat in [(2,n) for n in range(repeats)]+[(0,0)]:
        for name in ('before','after'):
            run=prepare(f'{name}-z{zoom}-{repeat}',name=='before')
            (run/'scripts/game_start.scr').write_text(f'atelier_view {zoom} 56 53\nunpause\nschedule on-next-calendar-month scripts/measure.scr\n')
            (run/'scripts/measure.scr').write_text('script metrics.log\nfps\nscript\nquit\n')
            r={'configuration':name,'zoom':zoom,'repeat':repeat,**execute(run,scene)}
            results.append(r); (RESULTS/'performance.json').write_text(json.dumps(results,indent=2)); print(json.dumps(r),flush=True)

def compatibility():
    run=prepare('stock-roundtrip',True)
    shutil.copy2(WORK/'artifacts/baseline-runtime/openttd.exe',run/'openttd.exe')
    shutil.copytree(WORK/'artifacts/baseline-runtime/lang',run/'lang',dirs_exist_ok=True)
    (run/'scripts/autoexec.scr').write_text('')
    (run/'scripts/game_start.scr').write_text('script compatibility.log\necho ATELIER_STOCK_LOADED\nsave stock-roundtrip\nscript\nunpause\nschedule on-next-calendar-month scripts/quit.scr\n')
    (run/'scripts/quit.scr').write_text('quit\n')
    result=execute(run,(SOURCE/'save/atelier-demo.sav').resolve())
    result['stock_save_written']=(run/'save/stock-roundtrip.sav').exists()
    assert result['stock_save_written']
    back=prepare('fork-roundtrip')
    (back/'scripts/game_start.scr').write_text('script compatibility.log\necho ATELIER_FORK_RELOADED\nscript\nquit\n')
    result['fork_reload']=execute(back,(run/'save/stock-roundtrip.sav').resolve())
    (RESULTS/'compatibility.json').write_text(json.dumps(result,indent=2)); print('SAVE_ROUNDTRIP_OK',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path); parser.add_argument('--repeats',type=int,default=2)
    args=parser.parse_args()
    if args.output: RESULTS=args.output.resolve(); RESULTS.mkdir(parents=True,exist_ok=True)
    performance(args.repeats); compatibility()
