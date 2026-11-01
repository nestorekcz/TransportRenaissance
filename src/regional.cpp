/* Transport Renaissance regional development. GPL-2.0-only. */
#include "stdafx.h"
#include "regional.h"
#include "industry.h"
#include "town.h"
#include "town_map.h"
#include "town_cmd.h"
#include "road_map.h"
#include "road_cmd.h"
#include "road_func.h"
#include "tunnelbridge_map.h"
#include "tunnelbridge.h"
#include "bridge_map.h"
#include "landscape.h"
#include "landscape_cmd.h"
#include "command_func.h"
#include "company_base.h"
#include "company_func.h"
#include "settings_type.h"
#include "newgrf_config.h"
#include "cargotype.h"
#include "station_base.h"
#include "station_func.h"
#include "strings_func.h"
#include "window_func.h"
#include "viewport_func.h"
#include "gfx_func.h"
#include "timer/timer_game_tick.h"
#include "timer/timer_game_calendar.h"
#include "console_func.h"
#include "console_type.h"
#include "console_internal.h"
#include "network/network.h"
#include "table/strings.h"
#include "table/sprites.h"
#include "saveload/saveload.h"
#include <queue>
#include <set>
#include "safeguards.h"

using namespace Regional;
std::map<TileIndex, RegionalLot> _regional_lots;
std::map<TownID, RegionalTown> _regional_towns;
uint8_t _regional_overlay = 0;
static const std::array<CargoLabel, None> labels{CT_GRAIN, CT_WOOD, CT_IRON_ORE, CargoLabel{'BMNR'}, CT_OIL, CT_FOOD,
	CargoLabel{'WDPR'}, CT_STEEL, CargoLabel{'BDMT'}, CT_GOODS, CargoLabel{'MACH'}, CargoLabel{'RCYC'}};
static CargoType CargoID(Cargo c) { return c == None ? INVALID_CARGO : GetCargoTypeByLabel(labels[c]); }
bool RegionalEnabled() { return _settings_game.economy.regional_mode != 0; }
bool IsRegionalTown(TownID town) { return _regional_towns.contains(town); }
RegionalLot *GetRegionalLot(TileIndex tile) { auto it = _regional_lots.find(tile); return it == _regional_lots.end() ? nullptr : &it->second; }
RegionalLot *GetRegionalLot(const Industry *ind) {
	if (ind == nullptr) return nullptr;
	auto *lot = GetRegionalLot(ind->location.tile);
	return lot != nullptr && lot->industry == ind->index ? lot : nullptr;
}
void InitializeRegional() { _regional_lots.clear(); _regional_towns.clear(); _regional_overlay = 0; if (_settings_game.economy.regional_mode == 2) _settings_game.difficulty.infinite_money = true; }
uint16_t RegionalStorage(const RegionalLot &l) { return BASE_STORAGE * (1 + l.storage_upgrade); }
uint RegionalInputRoom(const Industry *ind, CargoType cargo) {
	auto a = ind->GetCargoAccepted(cargo);
	if (a == ind->accepted.end()) return 0;
	auto *lot = GetRegionalLot(ind);
	return lot == nullptr ? 65535u - a->waiting : RegionalStorage(*lot) - std::min(RegionalStorage(*lot), a->waiting);
}

/* Connected road components are derived once per economic cycle, never every render frame.
 * Reciprocal road bits are required; bridges/tunnels connect their actual endpoints. */
struct Component {
	std::array<uint32_t, ServiceEnd> capacity{};
	uint32_t power_demand = 0, water_demand = 0, residents = 0, jobs = 0, food = 0;
};
struct Networks {
	std::map<TileIndex, uint32_t> roads;
	std::map<TileIndex, uint32_t> lots;
	std::vector<Component> components{1};
	uint32_t Flood(TileIndex start) {
		if (auto it = roads.find(start); it != roads.end()) return it->second;
		uint32_t id = components.size(); components.emplace_back();
		std::queue<TileIndex> pending; pending.push(start); roads.emplace(start, id);
		while (!pending.empty()) {
			TileIndex tile = pending.front(); pending.pop();
			auto add = [&](TileIndex next) { if (IsValidTile(next) && roads.emplace(next, id).second) pending.push(next); };
			RoadBits bits = GetAnyRoadBits(tile, RTT_ROAD);
			for (DiagDirection dir = DIAGDIR_BEGIN; dir < DIAGDIR_END; dir++) {
				TileIndex next = TileAddByDiagDir(tile, dir);
				if ((bits & DiagDirToRoadBits(dir)) && IsValidTile(next) && (GetAnyRoadBits(next, RTT_ROAD) & DiagDirToRoadBits(ReverseDiagDir(dir)))) add(next);
			}
			if (IsTileType(tile, MP_TUNNELBRIDGE) && GetTunnelBridgeTransportType(tile) == TRANSPORT_ROAD) add(GetOtherTunnelBridgeEnd(tile));
		}
		return id;
	}
	Networks() {
		for (const auto &[tile, lot] : _regional_lots) {
			uint32_t id = 0;
			for (DiagDirection dir = DIAGDIR_BEGIN; dir < DIAGDIR_END; dir++) {
				TileIndex next = TileAddByDiagDir(tile, dir);
				if (IsValidTile(next) && GetAnyRoadBits(next, RTT_ROAD) != ROAD_NONE) { id = Flood(next); break; }
			}
			lots.emplace(tile, id);
		}
	}
};
template <typename F> static void ForNearbyLots(TileIndex tile, uint radius, F callback) {
	uint left = TileX(tile) > radius ? TileX(tile) - radius : 0;
	uint right = std::min<uint>(Map::SizeX() - 1, TileX(tile) + radius);
	uint top = TileY(tile) > radius ? TileY(tile) - radius : 0;
	uint bottom = std::min<uint>(Map::SizeY() - 1, TileY(tile) + radius);
	for (uint y = top; y <= bottom; ++y) {
		auto end = _regional_lots.upper_bound(TileXY(right, y));
		for (auto it = _regional_lots.lower_bound(TileXY(left, y)); it != end; ++it) callback(it->first, it->second);
	}
}
static uint16_t Ratio(uint32_t supply, uint32_t demand) { return demand ? std::min<uint32_t>(100, supply * 100 / demand) : 100; }
static uint16_t Demand(uint16_t base, const RegionalLot &l) { return base * (1 + l.capacity_upgrade) * (100 - 15 * l.efficiency_upgrade) / 100; }
static uint16_t Waiting(const Industry *i, Cargo cargo) {
	if (!i) return 0;
	auto a = i->GetCargoAccepted(CargoID(cargo)); return a == i->accepted.end() ? 0 : a->waiting;
}
static void SetWaiting(Industry *i, Cargo cargo, uint16_t value) {
	auto a = i->GetCargoAccepted(CargoID(cargo)); if (a != i->accepted.end()) a->waiting = value;
}
static bool Active(const RegionalLot &l) { return l.stage == 3 && Industry::IsValidID(l.industry); }
static int64_t Upkeep(const RegionalLot &l) { if (_settings_game.economy.regional_mode == 2) return 0; return definitions[l.kind].upkeep * (1 + l.capacity_upgrade) + l.storage_upgrade * 5 + l.clean_upgrade * 5; }

static void ConfigureIndustry(RegionalLot &l) {
	auto *i = CreateRegionalIndustry(l.tile, l.town, l.owner); l.industry = i->index;
	auto accept = [&](CargoType cargo) {
		if (IsValidCargoType(cargo) && i->GetCargoAccepted(cargo) == i->accepted.end()) { auto &a = i->accepted.emplace_back(); a.cargo = cargo; }
	};
	auto produce = [&](CargoType cargo) { if (IsValidCargoType(cargo)) { auto &p = i->produced.emplace_back(); p.cargo = cargo; } };
	const auto &d = definitions[l.kind];
	for (auto input : d.inputs) accept(CargoID(input.cargo));
	if (l.kind == Shops || l.kind == Distribution) { accept(CargoID(Food)); accept(CargoID(Goods)); }
	accept(CargoID(Materials));
	if (d.batches && d.output != Machinery) accept(CargoID(Machinery));
	produce(CargoID(d.output));
	if (l.kind == Housing) {
		accept(GetCargoTypeByLabel(CT_PASSENGERS)); accept(GetCargoTypeByLabel(CT_MAIL));
		produce(GetCargoTypeByLabel(CT_PASSENGERS)); produce(GetCargoTypeByLabel(CT_MAIL));
	}
	i->cached_name.clear();
}

static bool RegionalContentSupported() {
	if (_settings_game.game_creation.landscape != LandscapeType::Temperate) return false;
	for (const auto &grf : _grfconfig) if (!grf->flags.Test(GRFConfigFlag::Static)) return false;
	return true;
}
std::string RegionalPlacementError(TileIndex tile, uint8_t kind) {
	if (!RegionalEnabled()) return "Transport Classic: use existing town funding and industries. Choose Regional Builder before generating a new world.";
	if (!RegionalContentSupported()) return "Regional Builder requires temperate default gameplay content. Static visual packs are supported.";
	if (kind >= End) return "Unknown development type.";
	if (!IsValidTile(tile) || TileX(tile) < 2 || TileY(tile) < 2 || TileX(tile) + 2 >= Map::SizeX() || TileY(tile) + 2 >= Map::SizeY()) return "Keep two tiles clear of the map boundary.";
	if (_regional_lots.contains(tile)) return "This lot is already reserved. Inspect it or use Remove zone / Demolish.";
	if (!IsTileType(tile, MP_CLEAR)) return "Use empty grass or bare land. Zoning never demolishes structures or trees.";
	if (GetTileSlope(tile) != SLOPE_FLAT) return "Level this tile before development.";
	if (IsBridgeAbove(tile)) return "A bridge crosses this lot. Choose another location.";
	if (_regional_lots.size() >= MAX_LOTS || !Industry::CanAllocateItem()) return "Regional development limit reached.";
	auto *town = ClosestTownFromTile(tile, 48);
	if (!town || !IsRegionalTown(town->index)) return "Found a regional town within 48 tiles first.";
	if (_regional_towns.at(town->index).owner != _current_company) return "This settlement is managed by another company.";
	if (definitions[kind].pollution >= 8 || kind == HeavyZone) {
		for (const auto &[other, lot] : _regional_lots) if (lot.kind == Housing && DistanceManhattan(tile, other) < 5) return "Polluting facilities need at least five tiles of separation from housing.";
	}
	if (kind == Housing) for (const auto &[other, lot] : _regional_lots) if (definitions[lot.kind].pollution >= 8 && DistanceManhattan(tile, other) < 5) return "Housing needs at least five tiles of separation from heavy industry.";
	return {};
}

std::string RegionalFoundingError(TileIndex tile, const std::string &name) {
	if (!RegionalEnabled()) return "Choose Regional Builder before generating a new world.";
	if (!RegionalContentSupported()) return "Regional Builder requires temperate default gameplay content. Static visual packs are supported.";
	if (!Town::CanAllocateItem()) return "The world has reached its settlement limit.";
	if (name.empty() || name.size() > 60) return "Enter a shorter, non-empty town name.";
	if (!IsValidTile(tile) || TileX(tile) < 6 || TileY(tile) < 6 || TileX(tile) + 6 >= Map::SizeX() || TileY(tile) + 6 >= Map::SizeY()) return "Keep the founding area six tiles from the map edge.";
	for (const Town *t : Town::Iterate()) {
		if (t->name == name) return "A settlement already uses that name.";
		if (DistanceManhattan(t->xy, tile) < 32) return "Place the town centre at least 32 tiles from existing towns.";
	}
	for (int x = -4; x <= 4; ++x) for (int y = -2; y <= 2; ++y) {
		TileIndex t = TileAddXY(tile, x, y);
		if (!IsTileType(t, MP_CLEAR) || GetRegionalLot(t)) return "The entire 9 x 5 founding area must be empty grass or bare land.";
		if (GetTileSlope(t) != SLOPE_FLAT || GetTileZ(t) != GetTileZ(tile)) return "Level the entire 9 x 5 founding area to one height.";
		if (IsBridgeAbove(t)) return "A bridge crosses the founding area; choose another location.";
	}
	return {};
}

CommandCost CmdRegionalAction(DoCommandFlags flags, TileIndex tile, uint8_t action, uint8_t kind, uint8_t density, const std::string &name) {
	if (!Company::IsValidID(_current_company) || !RegionalEnabled() || action > 7 || density > 2) return CMD_ERROR;
	bool execute = flags.Test(DoCommandFlag::Execute), sandbox = _settings_game.economy.regional_mode == 2;
	int64_t cost = 0;
	if (action == 7) {
		if (!RegionalFoundingError(tile, name).empty()) return CommandCost(STR_REGIONAL_BAD_TOWN);
		cost = 5000;
		if (kind) for (int x = -4; x <= 4; ++x) {
			auto r = Command<CMD_BUILD_ROAD>::Do({}, TileAddXY(tile, x, 0), ROAD_X, ROADTYPE_ROAD, DRD_NONE, TownID::Invalid());
			if (r.Failed()) return r; cost += r.GetCost();
		}
		if (execute) {
			CreateRegionalTown(tile, name);
			if (kind) for (int x = -4; x <= 4; ++x) Command<CMD_BUILD_ROAD>::Do({DoCommandFlag::Execute}, TileAddXY(tile, x, 0), ROAD_X, ROADTYPE_ROAD, DRD_NONE, TownID::Invalid());
		}
	} else if (action == 0) {
		if (!RegionalPlacementError(tile, kind).empty()) return CommandCost(STR_REGIONAL_INVALID_SITE);
		const auto &d = definitions[kind];
		cost = d.cost * (kind == Housing ? 1 + density : 1);
		if (execute) {
			RegionalLot l; l.tile = tile; l.kind = kind; l.density = kind == Housing ? density : 0; l.owner = _current_company;
			l.town = ClosestTownFromTile(tile, 48)->index; l.investment = sandbox ? 0 : cost;
			_regional_lots.emplace(tile, l);
		}
	} else {
		auto *l = GetRegionalLot(tile);
		if (!l || l->owner != _current_company) return CMD_ERROR;
		if (action <= 2) {
			if (action == 1 && l->stage) return CommandCost(STR_REGIONAL_USE_DEMOLISH);
			cost = action == 1 ? 0 : std::max<int64_t>(20, l->investment / 10);
			if (execute) {
				if (Industry::IsValidID(l->industry)) delete Industry::Get(l->industry);
				_regional_lots.erase(tile); RegionalRecountPopulation();
			}
		} else {
			if (!Active(*l)) return CommandCost(STR_REGIONAL_UNFINISHED);
			uint8_t *level = action == 3 ? &l->capacity_upgrade : action == 4 ? &l->efficiency_upgrade : action == 5 ? &l->storage_upgrade : &l->clean_upgrade;
			if (*level >= 2) return CommandCost(STR_REGIONAL_UPGRADE_MAX);
			cost = definitions[l->kind].cost * (1 + *level) / 2;
			auto *i = Industry::Get(l->industry);
			uint16_t materials = std::min<uint16_t>(20, Waiting(i, Materials));
			cost -= cost * materials / 100; // at most 20%, never free construction goods
			if (execute) { ++*level; SetWaiting(i, Materials, Waiting(i, Materials) - materials); l->investment += sandbox ? 0 : cost; }
		}
	}
	if (execute) { MarkWholeScreenDirty(); InvalidateWindowData(WC_REGIONAL, 0); }
	return CommandCost(EXPENSES_CONSTRUCTION, Money{sandbox ? 0 : cost});
}

uint MoveRegionalGoodsToStation(CargoType cargo, uint amount, Source source, const StationList &stations, Owner exclusivity);

void RegionalTransport(Industry *i) {
	auto *l = GetRegionalLot(i); if (!l || !Active(*l)) return;
	for (auto &p : i->produced) {
		if (!p.waiting) continue;
		uint offered = std::min<uint>(p.waiting, 64);
		uint moved = MoveRegionalGoodsToStation(p.cargo, offered, {i->index, SourceType::Industry}, i->stations_near, i->exclusive_consumer);
		/* Native station ratings may accept only part of the offered quantity. Retain the rest. */
		p.waiting -= moved; p.history[THIS_MONTH].transported += moved;
	}
}

void RegionalRecountPopulation() {
	for (auto &[id, r] : _regional_towns) {
		auto *t = Town::GetIfValid(id); if (!t) continue;
		uint32_t count = 0, houses = 0;
		for (const auto &[tile, l] : _regional_lots) if (l.town == id) { count += l.residents; if (Active(l) && l.kind == Housing) houses++; }
		r.growth = int32_t(count) - int32_t(r.population); r.population = count;
		t->cache.population = count; t->cache.num_houses = houses;
		UpdateTownRadius(t); UpdateTownMaxPass(t); t->UpdateVirtCoord();
	}
}

void RegionalTick() {
	if (_game_mode != GM_NORMAL || !RegionalEnabled() || _regional_lots.empty() || TimerGameTick::counter % CYCLE_TICKS) return;
	Networks network;
	std::set<TileIndex> funded;
	/* Settle bills in stable tile order. An unaffordable facility pauses without debt or negative inventories. */
	for (auto &[tile, l] : _regional_lots) {
		auto *company = Company::GetIfValid(l.owner);
		if (!company) { l.limit = 6; continue; }
		int64_t bill = _settings_game.economy.regional_mode == 2 ? 0 : Upkeep(l);
		if (!_settings_game.difficulty.infinite_money && bill > 0 && company->money < Money{bill}) { l.limit = 6; continue; }
		Backup<CompanyID> owner(_current_company, l.owner);
		SubtractMoneyFromCompany(CommandCost(EXPENSES_PROPERTY, Money{bill})); owner.Restore();
		l.maintenance += bill; funded.insert(tile);
	}
	for (auto &[tile, l] : _regional_lots) {
		auto id = network.lots.at(tile); if (!id || !Active(l) || !funded.contains(tile)) continue;
		auto &c = network.components[id]; const auto &d = definitions[l.kind];
		uint16_t scale = l.kind == Housing ? 1 + l.density : 1;
		c.power_demand += Demand(d.power, l) * scale; c.water_demand += Demand(d.water, l) * scale;
		c.residents += l.residents; c.jobs += d.jobs * (1 + l.capacity_upgrade);
		if (d.service != NoService) {
			uint32_t capacity = d.capacity * (1 + l.capacity_upgrade);
			if (l.kind == FuelPlant) capacity = capacity * std::min<uint16_t>(8 * (1 + l.capacity_upgrade), Waiting(Industry::Get(l.industry), Fuel)) / (8 * (1 + l.capacity_upgrade));
			c.capacity[d.service] += capacity;
		}
	}
	for (const auto &[tile, l] : _regional_lots) {
		uint32_t id = network.lots.at(tile);
		if (!id || !Active(l) || !funded.contains(tile) || l.kind != FuelPlant) continue;
		auto &c = network.components[id];
		uint32_t batches = 8 * (1 + l.capacity_upgrade);
		uint32_t fuel = std::min<uint32_t>(batches, Waiting(Industry::Get(l.industry), Fuel));
		uint32_t max_capacity = definitions[FuelPlant].capacity * (1 + l.capacity_upgrade);
		c.capacity[Power] -= max_capacity * fuel / batches;
		c.capacity[Power] += max_capacity * std::min(fuel, batches * Ratio(c.capacity[WaterService], c.water_demand) / 100) / batches;
	}
	/* Consume only goods actually unloaded to urban freight catchments. Food is a final local sale,
 * not an industry-to-industry shipment; its benefit is shared only by the connected neighborhood. */
	for (auto &[tile, l] : _regional_lots) {
		l.consumed = 0;
		uint32_t id = network.lots.at(tile);
		if (!id || !Active(l) || !funded.contains(tile) || (l.kind != Shops && l.kind != Distribution)) continue;
		auto &c = network.components[id]; auto *i = Industry::Get(l.industry);
		uint16_t needed = std::max<uint32_t>(4, c.residents / 8 + 2);
		uint16_t used = std::min(needed, Waiting(i, Food));
		SetWaiting(i, Food, Waiting(i, Food) - used);
		uint16_t goods = std::min<uint16_t>(needed / 2, Waiting(i, Goods)); SetWaiting(i, Goods, Waiting(i, Goods) - goods);
		c.food += used * 8; l.consumed = used + goods;
		auto p = i->GetCargoProduced(CargoID(Recyclables));
		if (p != i->produced.end()) { uint16_t amount = std::min<uint16_t>((used + goods) / 4, RegionalStorage(l) - p->waiting); p->waiting += amount; p->history[THIS_MONTH].production += amount; }
	}
	for (auto &[tile, l] : _regional_lots) {
		uint32_t id = network.lots.at(tile); auto &c = network.components[id];
		const auto &d = definitions[l.kind];
		l.power = id ? Ratio(c.capacity[Power], c.power_demand + (Active(l) ? 0 : d.power)) : 0;
		l.water = id ? Ratio(c.capacity[WaterService], c.water_demand + (Active(l) ? 0 : d.water)) : 0;
		l.jobs = Ratio(c.jobs * 2, std::max<uint32_t>(24, c.residents));
		l.food = Ratio(c.food, std::max<uint32_t>(24, c.residents));
		l.power_supply = c.capacity[Power]; l.power_demand = c.power_demand;
		l.water_supply = c.capacity[WaterService]; l.water_demand = c.water_demand; l.job_capacity = c.jobs;
		l.services = 0; l.environment = 100; l.coverage = 0;
		std::array<uint32_t, ServiceEnd> local_capacity{};
		ForNearbyLots(tile, 12, [&](TileIndex other, const RegionalLot &facility) {
			if (!Active(facility) || DistanceManhattan(tile, other) > 12) return;
			const auto &fd = definitions[facility.kind];
			uint32_t distance = DistanceManhattan(tile, other);
			if (fd.pollution && distance < 8) l.environment -= std::min<uint16_t>(l.environment, fd.pollution * (8 - distance) / (1 + facility.clean_upgrade) / 4);
			if (id && network.lots.at(other) == id && fd.service >= WasteService && fd.service < ServiceEnd && funded.contains(other))
				{ l.coverage |= 1 << fd.service; uint16_t availability = std::min(fd.power ? Ratio(c.capacity[Power], c.power_demand) : uint16_t{100}, fd.water ? Ratio(c.capacity[WaterService], c.water_demand) : uint16_t{100}); local_capacity[fd.service] += fd.capacity * (1 + facility.capacity_upgrade) * availability / 100; }
		});
		for (uint8_t service = WasteService; service < ServiceEnd; ++service) l.services += Ratio(local_capacity[service], std::max<uint32_t>(1, c.residents)) / 5;
		l.accessibility = 0;
		if (Industry::IsValidID(l.industry)) for (const Station *s : Industry::Get(l.industry)->stations_near) {
			/* Recent passenger vehicle visit, not a fabricated individual commute/congestion model. */
			if (s->time_since_load < 40 || s->time_since_unload < 40) l.accessibility = 100;
		}
		if (!funded.contains(tile)) { l.limit = 6; continue; }
		if (!id) { l.limit = 5; continue; }
		if (l.stage < 3) {
			if (!l.stage && !IsTileType(tile, MP_CLEAR)) { l.limit = 7; continue; }
			/* Utilities and source facilities bootstrap for money. Residential development needs both. */
			if (l.kind == Housing || l.kind == Shops || l.kind == LightZone || l.kind == HeavyZone) {
				if (!l.power) { l.limit = 3; continue; } if (!l.water) { l.limit = 4; continue; }
			}
			if (!l.stage) {
				if (!Industry::CanAllocateItem()) continue;
				if (l.kind == LightZone) l.kind = Furniture;
				if (l.kind == HeavyZone) l.kind = Metalworks;
				if (l.kind == CivicZone) l.kind = School;
				ConfigureIndustry(l);
			}
			++l.stage; l.limit = 7;
			SetIndustryConstructionStage(tile, l.stage); if (l.stage == 3) SetIndustryCompleted(tile);
			MarkTileDirtyByTile(tile); continue;
		}
		auto *i = Industry::GetIfValid(l.industry); if (!i) continue;
		l.last_output = 0; l.productivity = 0; l.limit = 0;
		if (l.kind == Housing) {
			/* Arrivals have reached their final destination through native vehicle unloading.
			 * Clear bounded arrival queues once per cycle; never convert arrivals into departures. */
			for (auto &a : i->accepted) if (a.cargo == GetCargoTypeByLabel(CT_PASSENGERS) || a.cargo == GetCargoTypeByLabel(CT_MAIL)) a.waiting = 0;
			uint16_t target = OccupancyTarget(HousingCapacity(l.density) * (1 + l.capacity_upgrade), l.power, l.water, l.jobs, l.food, l.services, l.environment, l.accessibility);
			l.residents = Approach(l.residents, target);
			for (auto &p : i->produced) { uint16_t generated = l.residents / (p.cargo == GetCargoTypeByLabel(CT_PASSENGERS) ? 6 : 12); uint16_t amount = std::min<uint16_t>(generated, RegionalStorage(l) - p.waiting); p.waiting += amount; p.history[THIS_MONTH].production += amount; }
			/* Stable density upgrades only after eight well-served cycles; never oscillate downward. */
			if (l.density < 2 && l.food >= 60 && l.water >= 80 && l.power >= 80 && l.jobs >= 60) {
				if (++l.age >= 8) { ++l.density; l.age = 0; MarkTileDirtyByTile(tile); }
			} else l.age = 0;
		} else if (d.batches) {
			std::array<uint16_t, None> inputs{}; for (uint8_t cargo = 0; cargo < None; ++cargo) inputs[cargo] = Waiting(i, static_cast<Cargo>(cargo));
			uint16_t output = i->produced.empty() ? 0 : i->produced[0].waiting;
			auto r = Process(d, inputs, output, RegionalStorage(l), l.power, l.water, l.capacity_upgrade, l.efficiency_upgrade, true, true);
			for (uint8_t cargo = 0; cargo < None; ++cargo) SetWaiting(i, static_cast<Cargo>(cargo), inputs[cargo]);
			if (!i->produced.empty()) { i->produced[0].waiting = output; i->produced[0].history[THIS_MONTH].production += r.output; }
			l.last_output = r.output; l.productivity = r.productivity; l.limit = r.limit;
		}
		RegionalTransport(i);
	}
	RegionalRecountPopulation(); InvalidateWindowData(WC_REGIONAL, 0); MarkWholeScreenDirty();
}

void RegionalAfterLoad() {
	if (IsSavegameVersionBefore(SLV_REGIONAL_DEVELOPMENT)) { InitializeRegional(); _settings_game.economy.regional_mode = 0; return; }
	for (const auto &[id, r] : _regional_towns) if (!Town::IsValidID(id)) SlErrorCorrupt("Invalid regional town");
	for (auto &[tile, l] : _regional_lots) {
		if (!IsValidTile(tile) || l.tile != tile || l.kind >= End || l.stage > 3 || l.density > 2 || l.capacity_upgrade > 2 || l.efficiency_upgrade > 2 || l.storage_upgrade > 2 || l.clean_upgrade > 2 || !Town::IsValidID(l.town)) SlErrorCorrupt("Invalid regional lot");
		if (l.stage && (!Industry::IsValidID(l.industry) || !IsTileType(tile, MP_INDUSTRY) || GetIndustryIndex(tile) != l.industry)) SlErrorCorrupt("Missing regional industry");
	}
	/* Population is a derived town cache; authoritative occupancy is saved in the lots. */
	// RebuildTownCaches already restored derived occupancy; retain saved growth history.
}

bool RegionalDrawTile(TileInfo *ti) {
	auto *l = GetRegionalLot(ti->tile); if (!l) return false;
	if (l->kind <= School || l->kind == Distribution) { RegionalDrawHouse(ti, l->kind, l->density, l->stage); return true; }
	return false;
}
uint8_t RegionalOverlayColour(TileIndex tile) {
	auto *l = GetRegionalLot(tile); if (!l) return 0;
	if (!_regional_overlay) return l->stage ? 0 : 1;
	switch (_regional_overlay) {
		case 1: return l->kind == Housing ? 2 : (l->kind == Shops ? 3 : 1);
		case 2: return l->power >= 100 ? 2 : 4;
		case 3: return l->water >= 100 ? 3 : 4;
		case 4: return l->services >= 50 ? 2 : 4;
		case 5: return l->environment >= 80 ? 2 : 4;
		case 6: return l->limit == 1 || l->limit == 2 ? 4 : 2;
		case 7: return l->accessibility ? 2 : 4;
	}
	return 0;
}

std::string RegionalMoney(int64_t amount) { return GetString(STR_REGIONAL_MONEY, Money{amount}); }
std::string RegionalDescribe(const RegionalLot &l) {
	const auto &d = definitions[l.kind];
	std::string s = fmt::format("{} | {} | density {}\nConstruction {} / 3 | Road-linked power {}%, water {}%\n", d.name, GetString(STR_TOWN_NAME, l.town), l.density + 1, l.stage, l.power, l.water);
	if (l.kind == Housing) s += fmt::format("Residents {} / {} capacity | accessible jobs {}% (aggregate)\nFood supply {}% | services {}% | environment {}% | recent station service {}%\n", l.residents, HousingCapacity(l.density) * (1 + l.capacity_upgrade), l.jobs, l.food, l.services, l.environment, l.accessibility);
	s += fmt::format("Connected grid: power {} / {} demand; water {} / {} demand\n", l.power_supply, l.power_demand, l.water_supply, l.water_demand);
	s += fmt::format("Road-network jobs capacity {} | public coverage: {} of 5 services\n", l.job_capacity, std::popcount(unsigned(l.coverage)));
	s += fmt::format("Jobs capacity {} | utility demand: power {}, water {} units/cycle\n", d.jobs * (1 + l.capacity_upgrade), Demand(d.power, l), Demand(d.water, l));
	if (d.service != NoService) s += fmt::format("Service capacity {} units | public service reach: 12 tiles on connected roads\n", d.capacity * (1 + l.capacity_upgrade));
	s += fmt::format("Upkeep {} / 2048-tick cycle | invested {} | upkeep paid {}\n", RegionalMoney(Upkeep(l)), RegionalMoney(l.investment), RegionalMoney(l.maintenance));
	if (auto *i = Industry::GetIfValid(l.industry)) {
		if (l.kind == Housing) s += "Residents generate and receive passengers/mail through nearby stations.\n";
		else if (l.kind == Shops || l.kind == Distribution) s += "Food supports 8 residents/unit; 4 consumed food/goods units return 1 recyclable.\n";
		else { s += "Recipe: ";
		for (auto input : d.inputs) if (input.cargo != None) s += fmt::format("{} {} + ", input.units, GetString(CargoSpec::Get(CargoID(input.cargo))->name));
		s += d.output != None ? fmt::format("-> {} {} per batch | up to {} units/cycle\n", d.yield, GetString(CargoSpec::Get(CargoID(d.output))->name), d.batches * d.yield * (1 + l.capacity_upgrade)) : "utility / urban service\n";
		}
		s += "Inventories (cargo units):\n";
		for (const auto &a : i->accepted) s += fmt::format("  {}: {} / {} stored\n", GetString(CargoSpec::Get(a.cargo)->name), a.waiting, RegionalStorage(l));
		for (const auto &p : i->produced) s += fmt::format("  Output {}: {} / {} waiting for collection\n", GetString(CargoSpec::Get(p.cargo)->name), p.waiting, RegionalStorage(l));
		if (d.batches) s += fmt::format("Last cycle: {} produced ({}% throughput) | {} nearby stations\n", l.last_output, l.productivity, i->stations_near.size());
		else s += fmt::format("Last cycle: {} cargo units consumed | {} nearby stations\n", l.consumed, i->stations_near.size());
	}
	static constexpr std::array<std::string_view, 8> limits{"Operating. Connect more markets to grow.", "Missing required inputs: deliver the recipe cargo by freight.", "Output storage full: collect cargo or upgrade storage.", "Power shortage: connect or expand generation.", "Water shortage: connect or expand a water pump.", "No road frontage: connect this lot to a road network.", "Cannot afford upkeep: restore the owner's company funds.", "Awaiting development / construction: allow economic cycles to pass."};
	s += fmt::format("{}\n", limits[std::min<uint8_t>(l.limit, 7)]);
	if (l.kind == Housing && l.stage == 3) {
		if (l.food < 50) s += "Growth constraint: deliver food to shops on this road network.\n";
		if (l.jobs < 50) s += "Growth constraint: few accessible jobs; build workplaces.\n";
		if (l.residents >= HousingCapacity(l.density) * (1 + l.capacity_upgrade) * 9 / 10) s += "Housing nearly full: zone more land or upgrade capacity.\n";
	}
	return s;
}
std::string RegionalOverview() {
	std::string s = RegionalEnabled() ? "REGIONAL BUILDER | one company budget\n" : "TRANSPORT CLASSIC | autonomous towns\n";
	s += "Basic construction is paid in money. Delivered materials discount upgrades.\nFreight earns native delivery income once; no separate production sale income.\n";
	for (const auto &[id, r] : _regional_towns) s += fmt::format("{}: {} | {} residents ({:+} last cycle)\n", GetString(STR_TOWN_NAME, id), SettlementStage(r.population), r.population, r.growth);
	int64_t bills = 0, spent = 0; uint32_t shortages = 0, excess = 0;
	for (const auto &[tile, l] : _regional_lots) { bills += Upkeep(l); spent += l.investment + l.maintenance; shortages += l.limit == 1; excess += l.limit == 2; }
	s += fmt::format("{} reserved lots | regional upkeep {} / cycle | total spent {}\n{} input shortages | {} full output stores\n", _regional_lots.size(), RegionalMoney(bills), RegionalMoney(spent), shortages, excess);
	s += "Select a tool, then click the map. Inspect any developed lot by clicking it.\nNative roads, rail, bridges, tunnels, stations and transfer orders remain available.\nWarehouses: use station cargo buffers and Transfer orders; no extra delivery payment.\nDevelopment artwork uses inherited base-set buildings; final assets await art approval.\n";
	return s;
}

bool BuildRegionalDemo();
bool BuildRegionalStress(uint32_t target);
bool VerifyRegionalCommands();
void AuditRegionalWorld();

static bool ConRegional(std::span<std::string_view> argv)
{
	if (argv.size() <= 1) { IConsolePrint(CC_HELP, "regional: open planner | regional status | regional inspect TILE | regional build TILE KIND DENSITY | regional found TILE NAME | regional upgrade TILE ACTION"); if (argv.size() == 1 && !_network_dedicated) ShowRegionalWindow(); return true; }
	if (argv[1] == "stress") return BuildRegionalStress(1000);
	if (argv[1] == "verify") return VerifyRegionalCommands();
	if (argv[1] == "demo") return BuildRegionalDemo();
	if (argv[1] == "audit") { AuditRegionalWorld(); return true; }
	if (argv[1] == "status") { IConsolePrint(CC_INFO, RegionalOverview()); return true; }
	if (argv.size() < 3) return false;
	auto number = [](std::string_view text) { uint64_t n = 0; if (text.empty()) return UINT32_MAX; for (char c : text) { if (c < '0' || c > '9') return UINT32_MAX; n = n * 10 + c - '0'; if (n >= UINT32_MAX) return UINT32_MAX; } return uint32_t(n); };
	TileIndex tile{number(argv[2])};
	if (!IsValidTile(tile)) return false;
	/* Explicit dedicated-server fixture: serialize an owner-scoped upgrade through the real
	 * network command queue. It is not available to clients or offline worlds. */
	if (argv[1] == "netverify" && _networking && _network_server && _network_dedicated) {
		auto *lot = GetRegionalLot(tile); if (!lot || !Company::IsValidID(lot->owner)) return false;
		Command<CMD_REGIONAL_ACTION>::SendNet(STR_REGIONAL_ERROR, lot->owner, tile, uint8_t{5}, uint8_t{0}, uint8_t{0}, std::string{});
		return true;
	}
	if (argv[1] == "view" && !_network_dedicated) { ShowRegionalWindow(tile); return true; }
	if (argv[1] == "inspect") { if (auto *l = GetRegionalLot(tile)) IConsolePrint(CC_INFO, RegionalDescribe(*l)); return true; }
	if (argv[1] == "build" && argv.size() == 5) {
		uint32_t kind = number(argv[3]), density = number(argv[4]); if (kind >= End || density > 2) return false;
		auto error = RegionalPlacementError(tile, kind); if (!error.empty()) { IConsolePrint(CC_ERROR, error); return true; }
		Command<CMD_REGIONAL_ACTION>::Post(STR_REGIONAL_ERROR, tile, uint8_t{0}, uint8_t(kind), uint8_t(density), std::string{}); return true;
	}
	if (argv[1] == "found" && argv.size() == 4) { Command<CMD_REGIONAL_ACTION>::Post(STR_REGIONAL_ERROR, tile, uint8_t{7}, uint8_t{1}, uint8_t{0}, std::string(argv[3])); return true; }
	if (argv[1] == "upgrade" && argv.size() == 4) { uint32_t a = number(argv[3]); if (a < 3 || a > 6) return false; Command<CMD_REGIONAL_ACTION>::Post(STR_REGIONAL_ERROR, tile, uint8_t(a), uint8_t{0}, uint8_t{0}, std::string{}); return true; }
	return false;
}
void RegisterRegionalConsole() { IConsole::CmdRegister("regional", ConRegional); }
