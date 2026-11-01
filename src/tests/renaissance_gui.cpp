/* Transport Renaissance additions, licensed under GPL-2.0-only. */

#include "../stdafx.h"
#include "../3rdparty/catch2/catch.hpp"
#include "../renaissance_gui.h"

#include "../safeguards.h"

TEST_CASE("Station attention requires waiting cargo and a rating below 50 percent", "[renaissance]")
{
	CHECK_FALSE(CargoNeedsAttention(false, 1000, 0));
	CHECK_FALSE(CargoNeedsAttention(true, 0, 0));
	CHECK(CargoNeedsAttention(true, 1, 0));
	CHECK(CargoNeedsAttention(true, 1, 126));
	CHECK_FALSE(CargoNeedsAttention(true, 1, 127));
	CHECK_FALSE(CargoNeedsAttention(true, 1000000, 128));
	CHECK_FALSE(CargoNeedsAttention(true, 1, 255));
}

TEST_CASE("Water interpolation wraps and preserves palette phase and alpha", "[renaissance]")
{
	const std::array cycle{Colour(20, 40, 60, 100), Colour(100, 160, 200, 240)};
	const auto start = SampleWaterPalette(cycle, 0, 0);
	CHECK(start.r == 20);
	CHECK(start.a == 100);
	const auto middle = SampleWaterPalette(cycle, 16384, 0);
	CHECK(middle.r == 60);
	CHECK(middle.g == 100);
	CHECK(middle.b == 130);
	CHECK(middle.a == 170);
	CHECK(SampleWaterPalette(cycle, 0, 1).r == 100);
	CHECK(SampleWaterPalette(cycle, 32768, 0).r == 100);
	CHECK(SampleWaterPalette(cycle, 65535, 0).r == 20);
	CHECK(SampleWaterPalette(cycle, 0, 2).r == 20);
	const std::array constant{Colour(42, 88, 122)};
	CHECK(SampleWaterPalette(constant, 12345, 99).r == 42);
}
