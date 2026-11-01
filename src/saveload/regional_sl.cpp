/* Transport Renaissance regional development. GPL-2.0-only. */
#include "../stdafx.h"
#include "saveload.h"
#include "../regional.h"
#include "../safeguards.h"

struct RGLTChunkHandler : ChunkHandler {
	RGLTChunkHandler() : ChunkHandler('RGLT', CH_TABLE) {}
	static inline const SaveLoad description[] = {
		SLE_VAR(RegionalLot, tile, SLE_UINT32), SLE_VAR(RegionalLot, town, SLE_UINT16), SLE_VAR(RegionalLot, industry, SLE_UINT16), SLE_VAR(RegionalLot, owner, SLE_UINT8),
		SLE_VAR(RegionalLot, kind, SLE_UINT8), SLE_VAR(RegionalLot, density, SLE_UINT8), SLE_VAR(RegionalLot, stage, SLE_UINT8), SLE_VAR(RegionalLot, age, SLE_UINT8),
		SLE_VAR(RegionalLot, capacity_upgrade, SLE_UINT8), SLE_VAR(RegionalLot, efficiency_upgrade, SLE_UINT8), SLE_VAR(RegionalLot, storage_upgrade, SLE_UINT8), SLE_VAR(RegionalLot, clean_upgrade, SLE_UINT8),
		SLE_VAR(RegionalLot, residents, SLE_UINT16), SLE_VAR(RegionalLot, power, SLE_UINT16), SLE_VAR(RegionalLot, water, SLE_UINT16), SLE_VAR(RegionalLot, food, SLE_UINT16),
		SLE_VAR(RegionalLot, jobs, SLE_UINT16), SLE_VAR(RegionalLot, services, SLE_UINT16), SLE_VAR(RegionalLot, environment, SLE_UINT16), SLE_VAR(RegionalLot, accessibility, SLE_UINT16),
		SLE_VAR(RegionalLot, productivity, SLE_UINT16), SLE_VAR(RegionalLot, last_output, SLE_UINT16), SLE_VAR(RegionalLot, consumed, SLE_UINT16), SLE_VAR(RegionalLot, limit, SLE_UINT8),
		SLE_VAR(RegionalLot, coverage, SLE_UINT8), SLE_VAR(RegionalLot, power_supply, SLE_UINT32), SLE_VAR(RegionalLot, power_demand, SLE_UINT32),
		SLE_VAR(RegionalLot, water_supply, SLE_UINT32), SLE_VAR(RegionalLot, water_demand, SLE_UINT32), SLE_VAR(RegionalLot, job_capacity, SLE_UINT32),
		SLE_VAR(RegionalLot, investment, SLE_INT64), SLE_VAR(RegionalLot, maintenance, SLE_INT64),
	};
	void Save() const override {
		SlTableHeader(description); for (auto &[tile, lot] : _regional_lots) { SlSetArrayIndex(tile.base()); SlObject(&lot, description); }
	}
	void Load() const override {
		auto table = SlTableHeader(description); int index;
		while ((index = SlIterateArray()) != -1) {
			if (_regional_lots.size() >= Regional::MAX_LOTS) SlErrorCorrupt("Too many regional lots");
			RegionalLot lot; SlObject(&lot, table);
			if (lot.tile.base() != static_cast<uint32_t>(index) || !_regional_lots.emplace(lot.tile, lot).second) SlErrorCorrupt("Duplicate regional lot");
		}
	}
};
struct RGTWChunkHandler : ChunkHandler {
	RGTWChunkHandler() : ChunkHandler('RGTW', CH_TABLE) {}
	static inline const SaveLoad description[] = {
		SLE_VAR(RegionalTown, town, SLE_UINT16), SLE_VAR(RegionalTown, owner, SLE_UINT8),
		SLE_VAR(RegionalTown, population, SLE_UINT32), SLE_VAR(RegionalTown, growth, SLE_INT32),
	};
	void Save() const override {
		SlTableHeader(description); for (auto &[id, town] : _regional_towns) { SlSetArrayIndex(id.base()); SlObject(&town, description); }
	}
	void Load() const override {
		auto table = SlTableHeader(description); int index;
		while ((index = SlIterateArray()) != -1) {
			RegionalTown town; SlObject(&town, table);
			if (town.town.base() != index || !_regional_towns.emplace(town.town, town).second) SlErrorCorrupt("Duplicate regional town");
		}
	}
};
static const RGLTChunkHandler RGLT;
static const RGTWChunkHandler RGTW;
static const ChunkHandlerRef handlers[]{RGLT, RGTW};
extern const ChunkHandlerTable _regional_chunk_handlers(handlers);
