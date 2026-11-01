"""Native fixture and verification for the temperate world art update."""
import argparse
import json
from pathlib import Path
import shutil
import re
import atelier_runtime as runtime
import atelier_verify as verify
from temperate_plan import WORK,OUT
RUN=OUT/'runtime';OLD=WORK/'artifacts/atelier-future-heritage/runtime'
runtime.OUT=OUT;runtime.RUN=RUN;verify.OUT=OUT;verify.SOURCE=RUN;verify.RESULTS=OUT/'verification'

def stage():
    if not RUN.exists():shutil.copytree(OLD,RUN)
    shutil.copy2(OUT/'game/temperate-world.grf',RUN/'newgrf/temperate-world.grf')
    cfg=(OLD/'openttd.cfg').read_text()
    (RUN/'before.cfg').write_text(cfg)
    assert '[newgrf-static]' in cfg
    # Later static GRFs win, so append this graphics pack after the older world.
    cfg=cfg.replace('temperate-world.grf =\n','')
    cfg=cfg.replace('renaissance-atelier.grf =','renaissance-atelier.grf =\ntemperate-world.grf =')
    (RUN/'openttd.cfg').write_text(cfg)
    (RUN/'indexed.cfg').write_text(cfg.replace('32bpp-anim','8bpp-optimized'))
    (OUT/'verification').mkdir(exist_ok=True)
    print('TEMPERATE_RUNTIME_STAGED',flush=True)

def capture():
    for label,zoom,x,y in [('cargo-stop',0,69,47),('cargo-stop-west',0,46,57),('road-depot',0,44,47),('rail-depot',0,47,45),('bridge-road',0,61,45),('bridge-river',1,63,64),('rail-river',1,76,66),('cargo-directions',1,19,32),('airport-review',0,93,20),('airfield-review',0,93,93),('sawmill-review',0,14,80),('forest-review',0,33,80),('refinery-review',0,4,80),('steelmill-review',0,14,98),('factory-review',0,74,81),('farm-review',0,38,99),('oil-well-review',0,59,98),('town-gallery',1,28,16),('world-overview',2,56,53)]:runtime.capture(label,zoom,x,y)
    runtime.capture('indexed',2,56,53,'indexed.cfg')

def audit():
    (RUN/'scripts/game_start.scr').write_text('script temperate-fleet-audit.log\natelier_fleet_audit\nscript\nquit\n')
    p=runtime.launch('save/atelier-demo.sav');p.wait(timeout=90);assert p.returncode==0
    rows={}
    for line in (RUN/'temperate-fleet-audit.log').read_text().splitlines():
        if 'FH_ENGINE ' in line:
            fields=dict(re.findall(r'(\w+)=([\w.-]+)',line));rows[int(fields['id'])]=fields
    before=json.loads((WORK/'artifacts/atelier-future-heritage/verification/native-engine-audit.json').read_text())['engines_after']
    assert len(rows)==256
    differences=[(i,k,v,before[str(i)].get(k)) for i,r in rows.items() for k,v in r.items() if v!=before[str(i)].get(k)]
    assert not differences,differences[:5]
    report={'engines':256,'resolved_directions':sum(int(r['valid']) for r in rows.values()),'differences_from_approved_fleet':differences}
    (OUT/'verification/native-engine-audit.json').write_text(json.dumps(report,indent=2));print('TEMPERATE_FLEET_UNCHANGED',flush=True)

def measure(configuration):
    path=OUT/'verification/performance.json'
    results=[r for r in json.loads(path.read_text()) if r['configuration']!=configuration] if path.exists() else []
    for zoom in (2,0):
        run=verify.prepare(f'{configuration}-z{zoom}-0',configuration=='before')
        (run/'scripts/game_start.scr').write_text(f'atelier_view {zoom} 56 53\nunpause\nschedule on-next-calendar-month scripts/measure.scr\n')
        (run/'scripts/measure.scr').write_text('script metrics.log\nfps\nscript\nquit\n')
        result={'configuration':configuration,'zoom':zoom,'repeat':0,**verify.execute(run,(RUN/'save/atelier-demo.sav').resolve())}
        results.append(result);path.write_text(json.dumps(results,indent=2));print('TEMPERATE_MEASURED',configuration,zoom,flush=True)

def baseline():measure('before')
def updated():measure('after')
def performance():baseline();updated()

def compatibility():
    run=verify.prepare('stock-roundtrip')
    shutil.copy2(WORK/'artifacts/baseline-runtime/openttd.exe',run/'openttd.exe')
    shutil.copytree(WORK/'artifacts/baseline-runtime/lang',run/'lang',dirs_exist_ok=True)
    (run/'scripts/autoexec.scr').write_text('')
    (run/'scripts/game_start.scr').write_text('save stock-roundtrip\nquit\n')
    report=verify.execute(run,(RUN/'save/atelier-demo.sav').resolve());report['stock_save_written']=(run/'save/stock-roundtrip.sav').exists();assert report['stock_save_written']
    back=verify.prepare('fork-roundtrip');(back/'scripts/game_start.scr').write_text('quit\n')
    report['fork_reload']=verify.execute(back,(run/'save/stock-roundtrip.sav').resolve())
    (OUT/'verification/compatibility.json').write_text(json.dumps(report,indent=2));print('TEMPERATE_STOCK_ROUNDTRIP_PASS',flush=True)

def fixture():
    # Preserve the fleet checkpoint inside this isolated delivery before adding
    # a rail bridge, traffic over the river, facilities and a review district.
    if not (RUN/'save/fleet-checkpoint.sav').exists():shutil.copy2(RUN/'save/atelier-demo.sav',RUN/'save/fleet-checkpoint.sav')
    cfg=(RUN/'openttd.cfg').read_text()
    if 'never_expire_airports' not in cfg:(RUN/'openttd.cfg').write_text(cfg+'\n[station]\nnever_expire_airports = true\n')
    script=(OLD/'game/atelier/main.nut').read_text()
    extra='''
        {
            local company=GSCompanyMode(0);
            GSRail.SetCurrentRailType(0);
            this.Check(GSRail.BuildRailStation(this.T(76,55),GSRail.RAILTRACK_NW_SE,1,3,GSStation.STATION_NEW),"bridge north station");
            this.Check(GSRail.BuildRailStation(this.T(76,73),GSRail.RAILTRACK_NW_SE,1,3,GSStation.STATION_NEW),"bridge south station");
            foreach(y in [58,59,60,72]) this.Check(GSRail.BuildRailTrack(this.T(76,y),GSRail.RAILTRACK_NW_SE),"bridge approach rail");
            this.Check(GSRail.BuildRailDepot(this.T(76,54),this.T(76,55)),"bridge train depot");
            local railbridges=GSBridgeList_Length(11);local railbridge=railbridges.Begin();
            this.Check(GSBridge.BuildBridge(GSVehicle.VT_RAIL,railbridge,this.T(76,61),this.T(76,71)),"connected railway river bridge");
            this.Train(this.T(76,54),13,27,this.T(76,55),this.T(76,73),"River connection");
            GSRoad.SetCurrentRoadType(GSRoad.ROADTYPE_ROAD);
            this.Road(63,73,68,73);
            this.Check(GSRoad.BuildRoadStation(this.T(67,72),this.T(67,73),GSRoad.ROADVEHTYPE_BUS,GSStation.STATION_NEW),"south river bus stop");
            this.Road(67,72,67,73);
            local bus=GSVehicle.BuildVehicle(this.T(44,47),116);this.Check(GSVehicle.IsValidVehicle(bus),"river bus");
            GSOrder.AppendOrder(bus,this.T(46,47),GSOrder.OF_NONE);GSOrder.AppendOrder(bus,this.T(67,72),GSOrder.OF_NONE);GSVehicle.StartStopVehicle(bus);
            // Four bay/depot entrance directions on separate, connected spurs.
            this.Road(10,35,28,35);this.Road(10,29,28,29);
            this.Road(10,29,10,35);this.Road(28,29,28,35);
            foreach(p in [[12,30,12,29],[16,34,16,35],[11,32,10,32],[27,32,28,32]]) {
                this.Check(GSRoad.BuildRoadStation(this.T(p[0],p[1]),this.T(p[2],p[3]),GSRoad.ROADVEHTYPE_TRUCK,GSStation.STATION_NEW),"cargo orientation");
                this.Road(p[0],p[1],p[2],p[3]);
            }
            foreach(p in [[20,30,20,29],[24,34,24,35],[11,33,10,33],[27,33,28,33]]) {
                this.Check(GSRoad.BuildRoadDepot(this.T(p[0],p[1]),this.T(p[2],p[3])),"depot orientation");this.Road(p[0],p[1],p[2],p[3]);
            }
            this.Check(GSRoad.BuildDriveThroughRoadStation(this.T(18,29),this.T(19,29),GSRoad.ROADVEHTYPE_TRUCK,GSStation.STATION_NEW),"through cargo building");
            this.Check(GSRoad.BuildDriveThroughRoadStation(this.T(10,31),this.T(10,32),GSRoad.ROADVEHTYPE_BUS,GSStation.STATION_NEW),"through bus building");
            this.Check(GSAirport.BuildAirport(this.T(91,18),GSAirport.AT_LARGE,GSStation.STATION_NEW),"airport review");
            this.Check(GSAirport.BuildAirport(this.T(91,91),GSAirport.AT_SMALL,GSStation.STATION_NEW),"airfield review");
        }
        foreach(p in [[2,12,79],[3,31,79],[4,2,79],[6,72,79],[8,12,96],[9,35,96],[11,57,96]]) {
            this.Check(GSIndustryType.BuildIndustry(p[0],this.T(p[1],p[2])),"industry review "+p[0]);
        }
'''
    script=script.replace('        foreach(x in [42,47,52,57,62,67,71])',extra+'\n        foreach(x in [42,47,52,57,62,67,71])')
    (RUN/'game/atelier/main.nut').write_text(script)
    from temperate_plan import world
    house_ids=sorted({r['house_id'] for r in world() if r['kind']=='town'})
    finish=(OLD/'scripts/finish.scr').read_text()
    more='\n'.join(f'atelier_house {12+(i%9)*5} {10+(i//9)*5} {hid}' for i,hid in enumerate(house_ids))
    finish=finish.replace('zoomto 2',more+'\nzoomto 2')
    (RUN/'scripts/finish.scr').write_text(finish)
    (RUN/'scripts/game_start.scr').write_text('unpause\nschedule on-next-calendar-month scripts/finish.scr\n')
    for f in (RUN/'save/atelier-demo.sav',RUN/'screenshot/atelier-first.png'):
        if f.exists():f.unlink()
    runtime.generate()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['stage','capture','fixture','audit','performance','baseline','updated','compatibility']);a=p.parse_args();globals()[a.action]()
