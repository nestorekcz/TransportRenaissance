/* Transport Renaissance regional development. GPL-2.0-only. */
#ifndef REGIONAL_ECONOMY_H
#define REGIONAL_ECONOMY_H

#include <array>
#include <algorithm>
#include <cstdint>
#include <string_view>

namespace Regional {
/* Quantities are whole cargo units. A cycle is 2048 authoritative game ticks. */
constexpr uint32_t CYCLE_TICKS = 2048;
constexpr uint16_t BASE_STORAGE = 256;
constexpr uint32_t MAX_LOTS = 8192;
enum Cargo : uint8_t { Produce, Timber, Ore, Minerals, Fuel, Food, WoodProducts, Metals, Materials, Goods, Machinery, Recyclables, None };
enum Kind : uint8_t { Housing, Shops, LightZone, HeavyZone, CivicZone, Park, Solar, Water, Waste, Fire, Health, School,
	Farm, FoodProcessor, Forest, Sawmill, Furniture, Mine, Quarry, Metalworks, MaterialPlant, Factory, MachineryWorks, FuelSupplier, FuelPlant, Recycler, Distribution, End };
enum Service : uint8_t { Power, WaterService, WasteService, FireService, HealthService, Education, Recreation, ServiceEnd, NoService = 255 };
struct Input { Cargo cargo = None; uint16_t units = 0; };
struct Definition {
	std::string_view name;
	int32_t cost, upkeep;
	std::array<Input, 2> inputs;
	Cargo output;
	uint16_t batches, yield, jobs, power, water, pollution;
	Service service = NoService;
	uint16_t capacity = 0;
};
/* No processing recipe increases material mass. Machinery is consumed, never a requirement. */
inline constexpr std::array<Definition, End> definitions{{
	{"Housing", 120, 2, {}, None, 0, 0, 0, 4, 4, 0},
	{"Shops", 180, 3, {}, Recyclables, 0, 0, 20, 6, 6, 0},
	{"Light industrial zone", 6500, 6, {}, None, 0, 0, 0, 4, 4, 2},
	{"Heavy industrial zone", 9000, 8, {}, None, 0, 0, 0, 8, 8, 8},
	{"Civic zone", 3500, 5, {}, None, 0, 0, 8, 4, 4, 0},
	{"Park", 600, 8, {}, None, 0, 0, 2, 0, 2, 0, Recreation, 160},
	{"Renewable power", 5000, 60, {}, None, 0, 0, 6, 0, 0, 0, Power, 160},
	{"Water pump & treatment", 3500, 45, {}, None, 0, 0, 6, 0, 0, 0, WaterService, 160},
	{"Waste collection", 2500, 35, {}, None, 0, 0, 10, 4, 2, 4, WasteService, 240},
	{"Fire station", 3000, 45, {}, None, 0, 0, 12, 4, 6, 0, FireService, 300},
	{"Clinic", 4000, 60, {}, None, 0, 0, 20, 8, 8, 0, HealthService, 240},
	{"School", 3500, 50, {}, None, 0, 0, 15, 6, 4, 0, Education, 240},
	{"Farm", 3000, 30, {}, Produce, 32, 2, 20, 2, 8, 1},
	{"Food processor", 6000, 65, {{{Produce, 2}, {None, 0}}}, Food, 24, 1, 36, 12, 12, 2},
	{"Forest operation", 3500, 35, {}, Timber, 24, 2, 20, 2, 2, 0},
	{"Sawmill", 5500, 55, {{{Timber, 2}, {None, 0}}}, WoodProducts, 20, 1, 30, 10, 4, 3},
	{"Furniture workshop", 6500, 60, {{{WoodProducts, 2}, {None, 0}}}, Goods, 16, 1, 40, 10, 4, 1},
	{"Ore mine", 6500, 65, {}, Ore, 24, 2, 30, 8, 8, 12},
	{"Quarry", 4500, 45, {}, Minerals, 28, 2, 24, 6, 4, 10},
	{"Metalworks", 9000, 90, {{{Ore, 2}, {None, 0}}}, Metals, 20, 1, 45, 20, 16, 16},
	{"Building-material plant", 6000, 60, {{{Minerals, 2}, {None, 0}}}, Materials, 24, 1, 30, 12, 8, 8},
	{"Factory", 10000, 100, {{{Metals, 1}, {WoodProducts, 1}}}, Goods, 20, 1, 60, 18, 10, 6},
	{"Machinery works", 9000, 90, {{{Metals, 2}, {None, 0}}}, Machinery, 12, 1, 45, 16, 8, 4},
	{"Fuel supplier", 7000, 70, {}, Fuel, 24, 1, 24, 6, 4, 10},
	{"Fuel power plant", 7000, 80, {{{Fuel, 1}, {None, 0}}}, None, 8, 0, 20, 0, 8, 16, Power, 400},
	{"Recycling plant", 8000, 80, {{{Recyclables, 4}, {None, 0}}}, Minerals, 16, 1, 32, 12, 8, 4},
	{"Distribution centre", 5000, 50, {}, Recyclables, 0, 0, 45, 8, 6, 1},
}};
struct ProductionResult { uint16_t batches = 0, output = 0, productivity = 0; uint8_t limit = 0; };
/* limit: 0 operating, 1 input, 2 storage, 3 power, 4 water, 5 access, 6 finance, 7 construction. */
inline ProductionResult Process(const Definition &d, std::array<uint16_t, None> &inventory, uint16_t &output,
	uint16_t storage, uint16_t power, uint16_t water, uint8_t capacity, uint8_t efficiency, bool connected, bool funded)
{
	ProductionResult r;
	if (!connected) { r.limit = 5; return r; }
	if (!funded) { r.limit = 6; return r; }
	uint32_t maximum = d.batches * (1 + capacity);
	if (maximum == 0) return r;
	uint32_t count = maximum;
	if (d.power && power < 100) { count = count * power / 100; r.limit = 3; }
	if (d.water && water < (d.power ? power : 100)) { count = maximum * water / 100; r.limit = 4; }
	for (auto input : d.inputs) if (input.cargo != None && inventory[input.cargo] / input.units < count) {
		count = inventory[input.cargo] / input.units; r.limit = 1;
	}
	if (d.yield && uint32_t(storage - std::min(storage, output)) / d.yield < count) {
		count = (storage - std::min(storage, output)) / d.yield; r.limit = 2;
	}
	/* An efficiency upgrade saves utility demand elsewhere; machinery adds at most 25% throughput.
	 * Bonus batches consume the same required inputs and fit the same storage constraints. */
	if (count == maximum && efficiency && inventory[Machinery] && d.output != Machinery && d.output != None) {
		uint32_t bonus = maximum / 4;
		for (auto input : d.inputs) if (input.cargo != None) bonus = std::min(bonus, uint32_t(inventory[input.cargo] / input.units - count));
		bonus = std::min(bonus, uint32_t((storage - output) / d.yield - count));
		if (bonus) { --inventory[Machinery]; count += bonus; }
	}
	for (auto input : d.inputs) if (input.cargo != None) inventory[input.cargo] -= count * input.units;
	r.batches = count; r.output = count * d.yield;
	output += r.output;
	r.productivity = count * 100 / maximum;
	return r;
}
inline uint16_t HousingCapacity(uint8_t density) { return std::array<uint16_t, 3>{24, 64, 160}[std::min<uint8_t>(density, 2)]; }
inline uint16_t OccupancyTarget(uint16_t capacity, uint16_t power, uint16_t water, uint16_t jobs, uint16_t food, uint16_t services, uint16_t environment, uint16_t transport)
{
	/* Basic settlement remains possible. Better factors smoothly fill the remaining housing. */
	uint32_t score = 10 + power / 10 + water / 5 + jobs / 5 + food / 5 + services / 10 + environment / 20 + transport / 20;
	return capacity * std::min<uint32_t>(100, score) / 100;
}
inline uint16_t Approach(uint16_t current, uint16_t target) {
	if (current == target) return current;
	uint16_t step = std::max<uint16_t>(1, (current > target ? current - target : target - current) / 8);
	return current < target ? std::min<uint16_t>(target, current + step) : std::max<uint16_t>(target, current - step);
}
inline constexpr std::array<uint32_t, 4> growth_thresholds{100, 500, 2000, 10000};
inline std::string_view SettlementStage(uint32_t population) {
	return std::array<std::string_view, 5>{"Village", "Small town", "Town", "City", "Metropolitan centre"}[
		std::upper_bound(growth_thresholds.begin(), growth_thresholds.end(), population) - growth_thresholds.begin()];
}
constexpr bool ValidateRecipes() {
	for (const auto &d : definitions) {
		uint32_t required = 0;
		for (auto input : d.inputs) { if (input.cargo != None && input.units == 0) return false; required += input.units; }
		if (required && d.yield > required) return false;
		if (d.output == Recyclables && d.batches) return false;
	}
	return true;
}
static_assert(ValidateRecipes());
}
#endif
