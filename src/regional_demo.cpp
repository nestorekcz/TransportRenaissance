/* Transport Renaissance reproducible native example builder. GPL-2.0-only. */
#include "stdafx.h"
#include "regional.h"
#include "command_func.h"
#include "company_base.h"
#include "company_func.h"
#include "town.h"
#include "industry.h"
#include "road_cmd.h"
#include "road_map.h"
#include "station_cmd.h"
#include "station_map.h"
#include "vehicle_cmd.h"
#include "vehicle_base.h"
#include "engine_base.h"
#include "engine_func.h"
#include "order_cmd.h"
#include "order_base.h"
#include "newgrf_roadstop.h"
#include "cargotype.h"
#include "console_func.h"
#include "network/network.h"
#include "landscape.h"
#include "landscape_cmd.h"
#include "viewport_func.h"
#include "timer/timer_game_tick.h"
#include "settings_type.h"
#include "settings_internal.h"
#include "settings_cmd.h"
#include "safeguards.h"

/* This developer/example command is offline-only. All construction uses real tested commands and
 * pays normal company costs. It never seeds freight inventories or fabricates delivery statistics. */
bool BuildRegionalDemo() {
	if (_networking || !RegionalEnabled() || !_regional_lots.empty()) return false;
	if (!Company::IsValidID(_local_company)) {
		extern Company *DoStartupNewCompany(bool is_ai, CompanyID company);
		auto *created = DoStartupNewCompany(false, CompanyID::Invalid());
		if (!created) return false;
		SetLocalCompany(created->index);
	}
	AutoRestoreBackup company(_current_company, _local_company);
	TileIndex origin = INVALID_TILE;
	for (uint y = 8; y + 18 < Map::SizeY() && origin == INVALID_TILE; ++y) for (uint x = 8; x + 46 < Map::SizeX(); ++x) {
		TileIndex town = TileXY(x + 20, y + 6);
		bool clear = true;
		for (const Town *t : Town::Iterate()) if (DistanceManhattan(t->xy, town) < 34) clear = false;
		if (!clear) continue;
		int height = GetTileZ(town);
		for (uint dx = 0; dx <= 42 && clear; ++dx) for (uint dy = 2; dy <= 12; ++dy) {
			TileIndex t = TileXY(x + dx, y + dy);
			if (!IsTileType(t, MP_CLEAR) || GetTileSlope(t) != SLOPE_FLAT || GetTileZ(t) != height) { clear = false; break; }
		}
		if (clear) { origin = TileXY(x, y); break; }
	}
	if (origin == INVALID_TILE) { IConsolePrint(CC_ERROR, "Demo needs a clear flat 43 x 11 area, 34 tiles from existing towns. Use the supplied flat heightmap."); return false; }
	auto tile = [&](int x, int y) { return TileAddXY(origin, x, y); };
	auto pay = [&](CommandCost result) { if (result.Failed()) { IConsolePrint(CC_ERROR, "DEMO command failed: message={} cost={}", result.GetErrorMessage(), result.GetCost()); return false; } return true; };
	if (!pay(Command<CMD_REGIONAL_ACTION>::Do({DoCommandFlag::Execute}, tile(20, 6), uint8_t{7}, uint8_t{0}, uint8_t{0}, std::string("New Haven")))) return false;
	for (int x = 0; x <= 42; ++x) if (!pay(Command<CMD_BUILD_ROAD>::Do({DoCommandFlag::Execute}, tile(x, 6), ROAD_X, ROADTYPE_ROAD, DRD_NONE, TownID::Invalid()))) return false;
	auto build = [&](int x, int y, Regional::Kind kind, uint8_t density = 0) { return pay(Command<CMD_REGIONAL_ACTION>::Do({DoCommandFlag::Execute}, tile(x, y), uint8_t{0}, uint8_t(kind), density, std::string{})); };
	if (!build(2, 5, Regional::Farm) || !build(18, 5, Regional::FoodProcessor) || !build(35, 5, Regional::Shops) || !build(25, 5, Regional::Solar) || !build(26, 5, Regional::Water)) return false;
	for (int x = 29; x <= 34; ++x) if (!build(x, 7, Regional::Housing)) return false;
	if (!build(37, 7, Regional::Park) || !build(38, 7, Regional::School) || !build(39, 7, Regional::Health) || !build(40, 7, Regional::Fire) || !build(41, 7, Regional::Waste)) return false;
	for (int x : {2, 18, 35}) if (!pay(Command<CMD_BUILD_ROAD_STOP>::Do({DoCommandFlag::Execute}, tile(x, 6), uint8_t{1}, uint8_t{1}, RoadStopType::Truck, true, DIAGDIR_NE, ROADTYPE_ROAD, ROADSTOP_CLASS_DFLT, uint16_t{0}, StationID::Invalid(), true))) return false;
	TileIndex depot = tile(8, 7);
	if (!pay(Command<CMD_BUILD_ROAD_DEPOT>::Do({DoCommandFlag::Execute}, depot, ROADTYPE_ROAD, DIAGDIR_NW))) return false;
	if (!pay(Command<CMD_BUILD_ROAD>::Do({DoCommandFlag::Execute}, tile(8, 6), ROAD_SE, ROADTYPE_ROAD, DRD_NONE, TownID::Invalid()))) return false;
	for (int route = 0; route < 2; ++route) {
		CargoType cargo = GetCargoTypeByLabel(route == 0 ? CT_GRAIN : CT_FOOD);
		EngineID engine = EngineID::Invalid(); uint32_t best_score = 0;
		for (const Engine *e : Engine::Iterate()) if (e->type == VEH_ROAD && IsEngineBuildable(e->index, VEH_ROAD, _current_company) && (e->info.cargo_type == cargo || HasBit(e->info.refit_mask, cargo))) { uint32_t score = (e->info.cargo_type == cargo ? 10000 : 0) + e->VehInfo<RoadVehicleInfo>().capacity * 100 + e->VehInfo<RoadVehicleInfo>().max_speed; if (score > best_score) { engine = e->index; best_score = score; } }
		if (!Engine::IsValidID(engine)) { IConsolePrint(CC_ERROR, "No suitable freight truck available."); return false; }
		for (int n = 0; n < 2; ++n) {
			auto [cost, vehicle, cap, mailcap, capacities] = Command<CMD_BUILD_VEHICLE>::Do({DoCommandFlag::Execute}, depot, engine, false, cargo, INVALID_CLIENT_ID);
			if (!pay(cost)) return false;
			Order from; from.MakeGoToStation(GetStationIndex(tile(route == 0 ? 2 : 18, 6))); from.SetStopLocation(OrderStopLocation::FarEnd); from.SetLoadType(route == 0 ? OrderLoadType::FullLoad : OrderLoadType::LoadIfPossible); from.SetNonStopType(OrderNonStopFlag::NoIntermediate);
			Order to; to.MakeGoToStation(GetStationIndex(tile(route == 0 ? 18 : 35, 6))); to.SetStopLocation(OrderStopLocation::FarEnd); to.SetLoadType(OrderLoadType::NoLoad); to.SetNonStopType(OrderNonStopFlag::NoIntermediate);
			if (!pay(Command<CMD_INSERT_ORDER>::Do({DoCommandFlag::Execute}, vehicle, VehicleOrderID{0}, from)) || !pay(Command<CMD_INSERT_ORDER>::Do({DoCommandFlag::Execute}, vehicle, VehicleOrderID{1}, to)) || !pay(Command<CMD_START_STOP_VEHICLE>::Do({DoCommandFlag::Execute}, vehicle, false))) return false;
		}
	}
	ScrollMainWindowToTile(tile(25, 6));
	IConsolePrint(CC_INFO, "REGIONAL_DEMO_READY origin={} town={} farm={} processor={} shops={} | 4 trucks, 2 real freight routes, zero seeded cargo", origin.base(), tile(20, 6).base(), tile(2, 5).base(), tile(18, 5).base(), tile(35, 5).base());
	return true;
}

void AuditRegionalWorld() {
	uint32_t errors = 0, residents = 0, delivered_produce = 0, delivered_food = 0, vehicles = 0;
	uint64_t digest = 1469598103934665603ULL;
	auto hash = [&](uint64_t value) { digest = (digest ^ value) * 1099511628211ULL; };
	for (const auto &[tile, l] : _regional_lots) {
		residents += l.residents; hash(tile.base()); hash(l.kind); hash(l.stage); hash(l.residents); hash(l.investment); hash(l.maintenance); hash(l.age); hash(l.density); hash(l.capacity_upgrade); hash(l.efficiency_upgrade); hash(l.storage_upgrade); hash(l.clean_upgrade); hash(l.power); hash(l.water); hash(l.food); hash(l.jobs); hash(l.services); hash(l.environment); hash(l.accessibility); hash(l.productivity); hash(l.last_output); hash(l.consumed); hash(l.limit); hash(l.coverage); hash(l.power_supply); hash(l.power_demand); hash(l.water_supply); hash(l.water_demand); hash(l.job_capacity);
		if (l.residents > Regional::HousingCapacity(l.density) * (1 + l.capacity_upgrade)) errors++;
		if (auto *i = Industry::GetIfValid(l.industry)) {
			for (const auto &a : i->accepted) {
				if (a.waiting > RegionalStorage(l)) errors++;
				hash(a.cargo); hash(a.waiting);
				if (a.history) for (const auto &h : *a.history) {
					if (l.kind == Regional::FoodProcessor && a.cargo == GetCargoTypeByLabel(CT_GRAIN)) delivered_produce += h.accepted;
					if (l.kind == Regional::Shops && a.cargo == GetCargoTypeByLabel(CT_FOOD)) delivered_food += h.accepted;
				}
			}
			for (const auto &p : i->produced) { if (p.waiting > RegionalStorage(l)) errors++; hash(p.cargo); hash(p.waiting); }
		}
	}
	for (const auto &[id, t] : _regional_towns) { hash(id.base()); hash(t.population); hash(t.growth); }
	for (const Vehicle *v : Vehicle::Iterate()) if (v->type == VEH_ROAD && v->IsPrimaryVehicle()) vehicles++;
	IConsolePrint(CC_INFO, "REGIONAL_AUDIT ticks={} lots={} population={} produce_delivered={} food_delivered={} vehicles={} inventory_errors={} hash={}", TimerGameTick::counter, _regional_lots.size(), residents, delivered_produce, delivered_food, vehicles, errors, digest);
}

/* A bounded offline load fixture. Sandbox must be selected before generating the world. */
bool BuildRegionalStress(uint32_t target) {
	if (_networking || _settings_game.economy.regional_mode != 2 || _regional_towns.empty() || target > 2000 || !Company::IsValidID(_local_company)) return false;
	AutoRestoreBackup company(_current_company, _local_company);
	const Town *town = Town::Get(_regional_towns.begin()->first);
	uint cx = TileX(town->xy), cy = TileY(town->xy);
	uint left = cx > 42 ? cx - 42 : 3, right = std::min<uint>(Map::SizeX() - 4, cx + 42);
	uint top = cy > 42 ? cy - 42 : 3, bottom = std::min<uint>(Map::SizeY() - 4, cy + 42);
	for (uint y = top; y <= bottom; ++y) for (uint x = left; x <= right; ++x) {
		TileIndex tile = TileXY(x, y);
		if (DistanceManhattan(tile, town->xy) >= 45 || GetRegionalLot(tile)) continue;
		if (y % 3 == 0 || x == cx) {
			if (!IsTileType(tile, MP_CLEAR) && !IsTileType(tile, MP_ROAD)) continue;
			RoadBits bits = x == cx ? ROAD_Y : ROAD_X;
			if (y % 3 == 0 && x == cx) bits = ROAD_ALL;
			Command<CMD_BUILD_ROAD>::Do({DoCommandFlag::Execute}, tile, bits, ROADTYPE_ROAD, DRD_NONE, TownID::Invalid());
		}
	}
	const std::array<Regional::Kind, 12> types{Regional::Housing, Regional::Housing, Regional::Housing, Regional::Solar, Regional::Water, Regional::Farm, Regional::Shops, Regional::School, Regional::Health, Regional::Fire, Regional::Park, Regional::Forest};
	for (uint y = top; y <= bottom && _regional_lots.size() < target; ++y) for (uint x = left; x <= right && _regional_lots.size() < target; ++x) {
		TileIndex tile = TileXY(x, y); uint8_t kind = types[_regional_lots.size() % types.size()];
		if (!RegionalPlacementError(tile, kind).empty()) continue;
		Command<CMD_REGIONAL_ACTION>::Do({DoCommandFlag::Execute}, tile, uint8_t{0}, kind, uint8_t{2}, std::string{});
	}
	IConsolePrint(CC_INFO, "REGIONAL_STRESS_READY lots={}", _regional_lots.size());
	return _regional_lots.size() == target;
}

/* Destructive offline integration fixture, only run in a disposable copy of the example save.
 * Financial balances/material stocks below are test setup, never part of the playable demo. */
bool VerifyRegionalCommands()
{
	if (_networking || _settings_game.economy.regional_mode != 1 || _regional_towns.size() != 1 || !Company::IsValidID(_local_company)) return false;
	AutoRestoreBackup owner(_current_company, _local_company);
	uint32_t passed = 0;
	auto check = [&](bool result, std::string_view name) {
		IConsolePrint(result ? CC_INFO : CC_ERROR, "REGIONAL_CHECK {} {}", result ? "PASS" : "FAIL", name);
		if (result) passed++;
		return result;
	};
	auto command = [&](DoCommandFlags flags, TileIndex tile, uint8_t action, uint8_t kind = 0, uint8_t density = 0) {
		return Command<CMD_REGIONAL_ACTION>::Do(flags, tile, action, kind, density, std::string{});
	};
	const auto *mode_setting = GetSettingFromName("economy.regional_mode");
	bool editable_in_menu = false;
	if (mode_setting != nullptr) {
		AutoRestoreBackup game_mode(_game_mode, GM_MENU);
		editable_in_menu = mode_setting->IsEditable();
	}
	if (!check(editable_in_menu && !mode_setting->IsEditable() && Command<CMD_CHANGE_SETTING>::Do({}, std::string("economy.regional_mode"), int32_t{0}).Failed() && _settings_game.economy.regional_mode == 1,
		"mode is selectable before world creation and locked in an existing game")) return false;
	auto *company = Company::Get(_local_company);
	company->money = Money{1000000};
	_regional_overlay = 0;
	TileIndex farm = INVALID_TILE, house = INVALID_TILE, pump = INVALID_TILE;
	for (const auto &[tile, lot] : _regional_lots) {
		if (lot.kind == Regional::Farm) farm = tile;
		if (lot.kind == Regional::Housing) house = tile;
		if (lot.kind == Regional::Water) pump = tile;
	}
	if (farm == INVALID_TILE || house == INVALID_TILE || pump == INVALID_TILE) return false;
	auto *housing = Industry::Get(GetRegionalLot(house)->industry);
	if (!check(housing->GetCargoAccepted(GetCargoTypeByLabel(CT_PASSENGERS)) != housing->accepted.end() && housing->GetCargoAccepted(GetCargoTypeByLabel(CT_MAIL)) != housing->accepted.end(), "housing accepts inbound passengers and mail")) return false;
	TileIndex empty = TileAddXY(house, 0, 1);
	auto count = _regional_lots.size(); Money before = company->money;
	auto quote = command({}, empty, 0, Regional::Housing, 2);
	if (!check(quote.Succeeded() && quote.GetCost() == Money{360} && count == _regional_lots.size() && company->money == before, "quote has no side effects")) return false;
	auto built = command({DoCommandFlag::Execute}, empty, 0, Regional::Housing, 2);
	if (!check(built.Succeeded() && before - company->money == quote.GetCost() && GetRegionalLot(empty)->stage == 0 && GetRegionalLot(empty)->residents == 0, "reservation charged exactly once; no instant residents")) return false;
	before = company->money;
	if (!check(command({DoCommandFlag::Execute}, empty, 0).Failed() && company->money == before && _regional_lots.size() == count + 1, "occupied reservation rejects construction without payment")) return false;
	if (!check(command({}, TileIndex{0}, 0).Failed() && !RegionalPlacementError(TileIndex{0}, Regional::Housing).empty(), "map boundary explains invalid placement")) return false;
	if (!check(command({}, TileAddXY(house, 1, 1), 0, Regional::Metalworks).Failed(), "heavy industry rejects housing conflict")) return false;
	auto *town = Town::Get(_regional_towns.begin()->first);
	if (!check(Command<CMD_REGIONAL_ACTION>::Do({}, town->xy, uint8_t{7}, uint8_t{1}, uint8_t{0}, std::string("Conflicting town")).Failed(), "founding rejects conflicting town footprint")) return false;
	if (!check(command({DoCommandFlag::Execute}, empty, 1).Succeeded() && !GetRegionalLot(empty) && company->money == before, "remove empty zone gives no construction refund")) return false;
	if (!check(command({}, farm, 1).Failed(), "developed site requires demolition")) return false;
	auto *lot = GetRegionalLot(farm); auto *industry = Industry::Get(lot->industry);
	auto materials = industry->GetCargoAccepted(GetCargoTypeByLabel(CargoLabel{'BDMT'}));
	if (materials == industry->accepted.end()) return false;
	materials->waiting = 20;
	before = company->money;
	quote = command({}, farm, 5);
	if (!check(quote.Succeeded() && quote.GetCost() == Money{1200} && materials->waiting == 20 && lot->storage_upgrade == 0, "material discount preview preserves stock")) return false;
	if (!check(command({DoCommandFlag::Execute}, farm, 5).Succeeded() && before - company->money == quote.GetCost() && materials->waiting == 0 && lot->storage_upgrade == 1, "upgrade consumes materials and charges once")) return false;
	if (!check(command({DoCommandFlag::Execute}, farm, 5).Succeeded() && command({}, farm, 5).Failed(), "upgrade level capped at two")) return false;
	/* Exercise the real road graph and facility billing with fixed economic-cycle boundaries. */
	AutoRestoreBackup tick(TimerGameTick::counter, uint64_t{Regional::CYCLE_TICKS});
	TileIndex cut = TileAddXY(pump, -2, 1);
	if (!check(Command<CMD_LANDSCAPE_CLEAR>::Do({DoCommandFlag::Execute}, cut).Succeeded(), "disconnect real road tile")) return false;
	RegionalTick();
	if (!check(GetRegionalLot(farm)->water == 0 && GetRegionalLot(farm)->power == 0 && GetRegionalLot(farm)->last_output == 0, "disconnected industry loses utilities and stops production")) return false;
	if (!check(Command<CMD_BUILD_ROAD>::Do({DoCommandFlag::Execute}, cut, ROAD_X, ROADTYPE_ROAD, DRD_NONE, TownID::Invalid()).Succeeded(), "reconnect real road tile")) return false;
	RegionalTick();
	if (!check(GetRegionalLot(farm)->water > 0 && GetRegionalLot(farm)->power > 0, "utility network recovers after reconnection")) return false;
	company->money = Money{0};
	uint64_t inventory_before = 0;
	for (const auto &a : industry->accepted) inventory_before += a.waiting;
	for (const auto &p : industry->produced) inventory_before += p.waiting;
	RegionalTick();
	uint64_t inventory_after = 0;
	for (const auto &a : industry->accepted) inventory_after += a.waiting;
	for (const auto &p : industry->produced) inventory_after += p.waiting;
	if (!check(lot->limit == 6 && company->money == Money{0} && inventory_before == inventory_after, "unaffordable upkeep pauses without negative money or inventory")) return false;
	company->money = Money{1000000}; RegionalTick();
	if (!check(lot->limit != 6, "operation recovers when funded")) return false;
	quote = command({}, farm, 2);
	before = company->money;
	if (!check(quote.Succeeded() && quote.GetCost() > Money{0} && command({DoCommandFlag::Execute}, farm, 2).Succeeded() && before - company->money == quote.GetCost() && !GetRegionalLot(farm), "demolition charges cost and removes inventory without refund")) return false;
	IConsolePrint(CC_INFO, "REGIONAL_CHECKS_OK count={}", passed);
	return true;
}
