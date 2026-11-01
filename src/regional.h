/* Transport Renaissance regional development. GPL-2.0-only. */
#ifndef REGIONAL_H
#define REGIONAL_H
#include "regional_economy.h"
#include "command_type.h"
#include "industry_type.h"
#include "town_type.h"
#include "tile_type.h"
#include "company_type.h"
#include "cargo_type.h"
#include <map>

struct TileInfo;
struct RegionalLot {
	TileIndex tile = INVALID_TILE;
	TownID town = TownID::Invalid();
	IndustryID industry = IndustryID::Invalid();
	CompanyID owner = CompanyID::Invalid();
	uint8_t kind = 0, density = 0, stage = 0, age = 0;
	uint8_t capacity_upgrade = 0, efficiency_upgrade = 0, storage_upgrade = 0, clean_upgrade = 0;
	uint16_t residents = 0, power = 0, water = 0, food = 0, jobs = 0, services = 0, environment = 100, accessibility = 0;
	uint16_t productivity = 0, last_output = 0, consumed = 0;
	uint8_t limit = 7, coverage = 0;
	uint32_t power_supply = 0, power_demand = 0, water_supply = 0, water_demand = 0, job_capacity = 0;
	int64_t investment = 0, maintenance = 0;
};
struct RegionalTown {
	TownID town = TownID::Invalid();
	CompanyID owner = CompanyID::Invalid();
	uint32_t population = 0;
	int32_t growth = 0;
};
extern std::map<TileIndex, RegionalLot> _regional_lots;
extern std::map<TownID, RegionalTown> _regional_towns;
extern uint8_t _regional_overlay;
RegionalLot *GetRegionalLot(TileIndex tile);
RegionalLot *GetRegionalLot(const Industry *ind);
bool RegionalEnabled();
bool IsRegionalTown(TownID town);
void InitializeRegional();
void RegionalTick();
void RegionalAfterLoad();
void RegionalRecountPopulation();
uint16_t RegionalStorage(const RegionalLot &lot);
uint RegionalInputRoom(const Industry *ind, CargoType cargo);
void RegionalTransport(Industry *ind);
void RegionalSetupCargo();
void RegionalDrawHouse(TileInfo *ti, uint8_t kind, uint8_t density, uint8_t stage);
bool RegionalDrawTile(TileInfo *ti);
uint8_t RegionalOverlayColour(TileIndex tile);
Industry *CreateRegionalIndustry(TileIndex tile, TownID town, CompanyID owner);
TownID CreateRegionalTown(TileIndex tile, const std::string &name);
std::string RegionalDescribe(const RegionalLot &lot);
std::string RegionalOverview();
std::string RegionalMoney(int64_t amount);
std::string RegionalPlacementError(TileIndex tile, uint8_t kind);
std::string RegionalFoundingError(TileIndex tile, const std::string &name);
void ShowRegionalWindow(TileIndex tile = INVALID_TILE);
void RegisterRegionalConsole();

/* 0 build/zone, 1 erase empty reservation, 2 demolish, 3..6 upgrades, 7 found town (arg selects starter road). */
CommandCost CmdRegionalAction(DoCommandFlags flags, TileIndex tile, uint8_t action, uint8_t kind, uint8_t density, const std::string &name);
DEF_CMD_TRAIT(CMD_REGIONAL_ACTION, CmdRegionalAction, {}, CommandType::LandscapeConstruction)
#endif
