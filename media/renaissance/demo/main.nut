/* Transport Renaissance demonstration. GPL-2.0-only. */
class RenaissanceDemo extends GSController {
    complete = false;
    function Save() { return { complete = this.complete }; }
    function Load(version, data) { this.complete = data.rawin("complete") && data.complete; }
    function T(x, y) { return GSMap.GetTileIndex(x, y); }
    function Check(ok, label) {
        if (!ok) throw label + ": " + GSError.GetLastErrorString();
        GSLog.Info("PASS: " + label);
    }
    function Start() {
        if (this.complete) { while (true) this.Sleep(1000); }
        while (GSCompany.ResolveCompanyID(0) != 0) this.Sleep(1);
        GSLog.Info("Renaissance Coast construction begins");
        GSCompany.ChangeBankBalance(0, 2000000, GSCompany.EXPENSES_OTHER, GSMap.TILE_INVALID);
        // Towns and industries are created through the supported deity API.
        this.Check(GSTown.FoundTown(this.T(48, 52), GSTown.TOWN_SIZE_MEDIUM, false, GSTown.ROAD_LAYOUT_2x2, "Port Aurelia"), "town");
        this.Check(GSIndustryType.BuildIndustry(0, this.T(32, 38)), "coal mine");
        this.Check(GSIndustryType.BuildIndustry(1, this.T(69, 38)), "power station");
        {
            local company = GSCompanyMode(0);
            GSCompany.SetName("Renaissance Coastal Railway");
            GSRail.SetCurrentRailType(0);
            this.Check(GSRail.BuildRailStation(this.T(32, 42), GSRail.RAILTRACK_NE_SW, 1, 3, GSStation.STATION_NEW), "mine platforms");
            this.Check(GSRail.BuildRailStation(this.T(68, 42), GSRail.RAILTRACK_NE_SW, 1, 3, GSStation.STATION_NEW), "harbour platforms");
            for (local x = 35; x < 68; x++) this.Check(GSRail.BuildRailTrack(this.T(x, 42), GSRail.RAILTRACK_NE_SW), "rail " + x);
            this.Check(GSRail.BuildRailDepot(this.T(31, 42), this.T(32, 42)), "rail depot");
            GSRoad.SetCurrentRoadType(GSRoad.ROADTYPE_ROAD);
            this.Check(GSRoad.BuildRoad(this.T(31, 46), this.T(72, 46)), "coast road");
            local connected = GSRoad.BuildRoad(this.T(48, 46), this.T(48, 50));
            this.Check(connected || GSError.GetLastError() == GSError.ERR_ALREADY_BUILT, "town connection");
            this.Check(GSRoad.BuildRoadDepot(this.T(35, 47), this.T(35, 46)), "road depot");
            GSStation.SetName(GSStation.GetStationID(this.T(32, 42)), "Aurelia Colliery");
            GSStation.SetName(GSStation.GetStationID(this.T(68, 42)), "Aurelia Power Wharf");
            local engines = GSEngineList(GSVehicle.VT_RAIL);
            local engine = -1;
            local wagon = -1;
            foreach (id, unused in engines) {
                if (!GSEngine.IsBuildable(id) || GSEngine.GetRailType(id) != 0) continue;
                if (!GSEngine.IsWagon(id) && engine == -1) engine = id;
                if (GSEngine.IsWagon(id) && GSEngine.GetCargoType(id) == 1) wagon = id;
            }
            if (engine == -1 || wagon == -1) throw "Required steam locomotive / coal wagon unavailable";
            local train = GSVehicle.BuildVehicle(this.T(31, 42), engine);
            this.Check(GSVehicle.IsValidVehicle(train), "locomotive");
            for (local i = 0; i < 3; i++) {
                local car = GSVehicle.BuildVehicle(this.T(31, 42), wagon);
                this.Check(GSVehicle.IsValidVehicle(car), "coal wagon");
                this.Check(GSVehicle.MoveWagon(car, 0, train, i), "coupling");
            }
            this.Check(GSOrder.AppendOrder(train, this.T(32, 42), GSOrder.OF_FULL_LOAD_ANY), "mine order");
            this.Check(GSOrder.AppendOrder(train, this.T(68, 42), GSOrder.OF_UNLOAD | GSOrder.OF_NO_LOAD), "power order");
            GSVehicle.SetName(train, "Coastal Coal No. 1");
            this.Check(GSVehicle.StartStopVehicle(train), "dispatch train");
            GSSign.BuildSign(this.T(45, 43), "Renaissance Coast - independent OpenTTD fork");
        }
        GSViewport.ScrollTo(this.T(49, 42));
        this.complete = true;
        GSLog.Info("RENAISSANCE_DEMO_READY");
        while (true) this.Sleep(1000);
    }
}

