/* Original approval fixture. Existing commands and vehicle IDs; GPL-2.0-only. */
class AtelierDemo extends GSController {
    complete = false;
    function Save() { return { complete = this.complete }; }
    function Load(v,d) { this.complete = d.rawin("complete") && d.complete; }
    function T(x,y) { return GSMap.GetTileIndex(x,y); }
    function Observe() {
        while (true) {
            local company=GSCompanyMode(0);
            foreach (v,_ in GSVehicleList()) {
                local tile=GSVehicle.GetLocation(v);
                GSLog.Info("ATELIER_TRAFFIC "+v+" tile="+tile+" speed="+GSVehicle.GetCurrentSpeed(v)+" state="+GSVehicle.GetState(v));
            }
            this.Sleep(200);
        }
    }
    function Check(ok,label) { if (!ok) throw label+": "+GSError.GetLastErrorString(); GSLog.Info("ATELIER_PASS "+label); }
    function Road(x1,y1,x2,y2) { local r=GSRoad.BuildRoad(this.T(x1,y1),this.T(x2,y2)); this.Check(r || GSError.GetLastError()==GSError.ERR_ALREADY_BUILT,"road "+x1+","+y1); }
    function Train(depot,engine,wagon,a,b,name) {
        local v=GSVehicle.BuildVehicle(depot,engine); this.Check(GSVehicle.IsValidVehicle(v),name);
        for (local k=0;k<2;k++) { local w=GSVehicle.BuildVehicle(depot,wagon); this.Check(GSVehicle.IsValidVehicle(w),"wagon"); this.Check(GSVehicle.MoveWagon(w,0,v,k),"couple"); }
        this.Check(GSOrder.AppendOrder(v,a,GSOrder.OF_NONE),"rail origin");
        this.Check(GSOrder.AppendOrder(v,b,GSOrder.OF_NONE),"rail destination");
        GSVehicle.SetName(v,name); this.Check(GSVehicle.StartStopVehicle(v),"dispatch "+name);
    }
    function Start() {
        if (this.complete) { this.Observe(); }
        while (GSCompany.ResolveCompanyID(0)!=0) this.Sleep(1);
        GSCompany.ChangeBankBalance(0,5000000,GSCompany.EXPENSES_OTHER,GSMap.TILE_INVALID);
        {
            local company=GSCompanyMode(0); GSRoad.SetCurrentRoadType(GSRoad.ROADTYPE_ROAD);
            GSCompany.SetName("Aurelia Regional Transport");
            foreach(y in [48,53,58]) this.Road(43,y,70,y);
            foreach(x in [43,48,53,58,63,68]) this.Road(x,46,x,61);
        }
        this.Check(GSTown.FoundTown(this.T(55,55),GSTown.TOWN_SIZE_SMALL,false,GSTown.ROAD_LAYOUT_2x2,"Aurelia"),"town");
        this.Check(GSIndustryType.BuildIndustry(0,this.T(37,39)),"coal mine");
        this.Check(GSIndustryType.BuildIndustry(1,this.T(73,39)),"power works");
        {
            local company=GSCompanyMode(0); GSRail.SetCurrentRailType(0);
            // Two independent functioning routes keep fixture routing unambiguous.
            foreach(y in [43,45]) {
                local start=y==43?38:48; local finish=y==43?73:65;
                this.Check(GSRail.BuildRailStation(this.T(start,y),GSRail.RAILTRACK_NE_SW,1,3,GSStation.STATION_NEW),"west platform");
                this.Check(GSRail.BuildRailStation(this.T(finish,y),GSRail.RAILTRACK_NE_SW,1,3,GSStation.STATION_NEW),"east platform");
                for(local x=start+3;x<finish;x++) this.Check(GSRail.BuildRailTrack(this.T(x,y),GSRail.RAILTRACK_NE_SW),"rail");
                this.Check(GSRail.BuildRailDepot(this.T(start-1,y),this.T(start,y)),"rail depot");
                this.Train(this.T(start-1,y),13,y==43?29:27,this.T(start,y),this.T(finish,y),y==43?"Meridian Coal":"Aurelia Local");
            }
            // A short, connected branch exposes switch overlays and curved track.
            this.Check(GSRail.BuildRailTrack(this.T(59,43),GSRail.RAILTRACK_NE_SE),"junction");
            this.Check(GSRail.BuildRailTrack(this.T(59,44),GSRail.RAILTRACK_NW_SE),"branch");
            this.Check(GSRail.BuildRailTrack(this.T(59,45),GSRail.RAILTRACK_NW_SW),"curve");
            foreach(y in [43,45]) {
                this.Check(GSRail.BuildSignal(this.T(58,y),this.T(57,y),GSRail.SIGNALTYPE_PBS),"west junction signal");
                this.Check(GSRail.BuildSignal(this.T(60,y),this.T(61,y),GSRail.SIGNALTYPE_PBS),"east junction signal");
            }
            GSRoad.SetCurrentRoadType(GSRoad.ROADTYPE_ROAD);
            this.Check(GSRoad.BuildRoadDepot(this.T(44,47),this.T(44,48)),"bus depot");
            this.Check(GSRoad.BuildRoadStation(this.T(46,47),this.T(46,48),GSRoad.ROADVEHTYPE_BUS,GSStation.STATION_NEW),"bus stop west");
            this.Check(GSRoad.BuildRoadStation(this.T(66,57),this.T(66,58),GSRoad.ROADVEHTYPE_BUS,GSStation.STATION_NEW),"bus stop east");
            this.Road(44,47,44,48); this.Road(46,47,46,48); this.Road(66,57,66,58);
            for(local k=0;k<3;k++) {
                local v=GSVehicle.BuildVehicle(this.T(44,47),116); this.Check(GSVehicle.IsValidVehicle(v),"bus");
                this.Check(GSOrder.AppendOrder(v,this.T(46,47),GSOrder.OF_NONE),"bus west order"); this.Check(GSOrder.AppendOrder(v,this.T(66,57),GSOrder.OF_NONE),"bus east order"); this.Check(GSVehicle.StartStopVehicle(v),"bus dispatch");
            }
            this.Check(GSRoad.BuildRoadStation(this.T(69,47),this.T(69,48),GSRoad.ROADVEHTYPE_TRUCK,GSStation.STATION_NEW),"goods dock");
            this.Check(GSRoad.BuildRoadStation(this.T(46,57),this.T(46,58),GSRoad.ROADVEHTYPE_TRUCK,GSStation.STATION_NEW),"goods destination");
            this.Road(69,47,69,48); this.Road(46,57,46,58);
            local truck=GSVehicle.BuildVehicle(this.T(44,47),138); this.Check(GSVehicle.IsValidVehicle(truck),"delivery truck");
            this.Check(GSOrder.AppendOrder(truck,this.T(69,47),GSOrder.OF_NONE),"truck origin"); this.Check(GSOrder.AppendOrder(truck,this.T(46,57),GSOrder.OF_NONE),"truck destination"); this.Check(GSVehicle.StartStopVehicle(truck),"truck dispatch");
            // Concrete road bridge, slope approaches and broad river shore.
            this.Road(63,58,63,61);
            local bridges=GSBridgeList_Length(11); local bridge=-1;
            foreach(id,v in bridges) { if(id==1) bridge=id; }
            if(bridge==-1) bridge=bridges.Begin();
            this.Check(GSBridge.BuildBridge(GSVehicle.VT_ROAD,bridge,this.T(63,61),this.T(63,71)),"river bridge");
            this.Road(63,71,63,73);
            this.Check(GSBridge.BuildBridge(GSVehicle.VT_ROAD,1,this.T(61,44),this.T(61,47)),"concrete rail overpass");
            this.Road(61,41,61,44);
            this.Road(61,47,61,48);
            // A ferry in the river is a functioning vehicle; no tram roster exists.
            this.Check(GSMarine.BuildWaterDepot(this.T(51,66),this.T(52,66)),"ferry depot");
            local ferry=GSVehicle.BuildVehicle(this.T(51,66),206); this.Check(GSVehicle.IsValidVehicle(ferry),"ferry");
            this.Check(GSMarine.BuildBuoy(this.T(43,66)),"west buoy");
            this.Check(GSMarine.BuildBuoy(this.T(72,66)),"east buoy");
            GSOrder.AppendOrder(ferry,this.T(43,66),GSOrder.OF_NONE); GSOrder.AppendOrder(ferry,this.T(72,66),GSOrder.OF_NONE); GSVehicle.StartStopVehicle(ferry);
        }
        foreach(x in [42,47,52,57,62,67,71]) foreach(y in [41,60,72]) GSTile.PlantTree(this.T(x,y));
        GSViewport.ScrollTo(this.T(56,53)); this.complete=true;
        GSLog.Info("ATELIER_READY"); this.Observe();
    }
}
