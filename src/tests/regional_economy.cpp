/* Transport Renaissance regional development. GPL-2.0-only. */
#include "../stdafx.h"
#include "../3rdparty/catch2/catch.hpp"
#include "../regional_economy.h"
#include "../safeguards.h"
using namespace Regional;

TEST_CASE("Regional recipes consume only available inputs and retain bounded outputs", "[regional]") {
	std::array<uint16_t, None> stock{}; uint16_t out = 0;
	auto r = Process(definitions[FoodProcessor], stock, out, 256, 100, 100, 0, 0, true, true);
	CHECK(r.limit == 1); CHECK(out == 0);
	stock[Produce] = 37;
	r = Process(definitions[FoodProcessor], stock, out, 256, 100, 100, 0, 0, true, true);
	CHECK(r.output == 18); CHECK(stock[Produce] == 1); CHECK(out == 18);
	stock[Produce] = 200; out = 255;
	r = Process(definitions[FoodProcessor], stock, out, 256, 100, 100, 0, 0, true, true);
	CHECK(r.limit == 2); CHECK(out == 256); CHECK(stock[Produce] == 198);
	r = Process(definitions[FoodProcessor], stock, out, 256, 100, 100, 0, 0, true, true);
	CHECK(r.output == 0); CHECK(stock[Produce] == 198);
}
TEST_CASE("Utility shortages scale production and can recover", "[regional]") {
	std::array<uint16_t, None> stock{}; stock[Produce] = 200; uint16_t out = 0;
	auto r = Process(definitions[FoodProcessor], stock, out, 256, 100, 50, 0, 0, true, true);
	CHECK(r.output == 12); CHECK(r.productivity == 50); CHECK(r.limit == 4);
	r = Process(definitions[FoodProcessor], stock, out, 256, 25, 75, 0, 0, true, true);
	CHECK(r.output == 6); CHECK(r.limit == 3);
	r = Process(definitions[FoodProcessor], stock, out, 256, 100, 100, 0, 0, true, true);
	CHECK(r.output == 24);
}
TEST_CASE("Disconnected and unfunded operations preserve inventories", "[regional]") {
	std::array<uint16_t, None> stock{}; stock[Produce] = 200; uint16_t out = 20;
	CHECK(Process(definitions[FoodProcessor], stock, out, 256, 100, 100, 0, 0, false, true).limit == 5);
	CHECK(Process(definitions[FoodProcessor], stock, out, 256, 100, 100, 0, 0, true, false).limit == 6);
	CHECK(stock[Produce] == 200); CHECK(out == 20);
}
TEST_CASE("Two-input factories cannot substitute one required input", "[regional]") {
	std::array<uint16_t, None> stock{}; stock[Metals] = 100; uint16_t out = 0;
	CHECK(Process(definitions[Factory], stock, out, 256, 100, 100, 0, 0, true, true).output == 0);
	stock[WoodProducts] = 7;
	CHECK(Process(definitions[Factory], stock, out, 256, 100, 100, 0, 0, true, true).output == 7);
	CHECK(stock[Metals] == 93); CHECK(stock[WoodProducts] == 0);
}
TEST_CASE("Optional machinery has capped gains and does not create input cargo", "[regional]") {
	std::array<uint16_t, None> stock{}; stock[Produce] = 200; stock[Machinery] = 3; uint16_t out = 0;
	auto r = Process(definitions[FoodProcessor], stock, out, 256, 100, 100, 0, 1, true, true);
	CHECK(r.output == 30); CHECK(r.productivity == 125); CHECK(stock[Produce] == 140); CHECK(stock[Machinery] == 2);
	stock[Produce] = 48;
	r = Process(definitions[FoodProcessor], stock, out, 256, 100, 100, 0, 1, true, true);
	CHECK(r.output == 24); CHECK(stock[Produce] == 0); CHECK(stock[Machinery] == 2);
}
TEST_CASE("Recycling recovery is lossy and cannot self-feed", "[regional]") {
	std::array<uint16_t, None> stock{}; stock[Recyclables] = 63; uint16_t out = 0;
	CHECK(Process(definitions[Recycler], stock, out, 256, 100, 100, 0, 0, true, true).output == 15);
	CHECK(stock[Recyclables] == 3); CHECK(ValidateRecipes());
}
TEST_CASE("Housing responds smoothly to delivered food and services", "[regional]") {
	auto basic = OccupancyTarget(160, 100, 100, 100, 0, 0, 100, 0);
	auto fed = OccupancyTarget(160, 100, 100, 100, 100, 0, 100, 0);
	CHECK(fed > basic); CHECK(OccupancyTarget(160, 100, 100, 100, 100, 100, 100, 100) == 160);
	CHECK(Approach(160, 0) == 140); CHECK(Approach(0, 160) == 20);
	uint16_t people = 0; for (int n = 0; n < 100; ++n) people = Approach(people, fed);
	CHECK(people == fed); CHECK(SettlementStage(499) == "Small town"); CHECK(SettlementStage(500) == "Town");
}
TEST_CASE("Long deterministic recipe runs survive alternating shortages and oversupply", "[regional]") {
	auto run = []() {
		uint64_t digest = 0;
		for (const auto &d : definitions) {
			std::array<uint16_t, None> stock{}; uint16_t out = 0;
			for (uint32_t cycle = 0; cycle < 2000; ++cycle) {
				for (auto &units : stock) units = std::min<uint16_t>(768, units + cycle % 37);
				auto r = Process(d, stock, out, 768, cycle % 101, (cycle * 7) % 101, cycle % 3, (cycle / 7) % 3, cycle % 11 != 0, cycle % 13 != 0);
				REQUIRE(out <= 768); for (auto units : stock) REQUIRE(units <= 768);
				digest = digest * 31 + r.output; if (cycle % 5 == 0) out /= 2;
			}
		}
		return digest;
	};
	CHECK(run() == run());
}
