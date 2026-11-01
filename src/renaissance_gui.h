/* Transport Renaissance additions, licensed under GPL-2.0-only. */

/** @file renaissance_gui.h Pure presentation helpers; no authoritative game state. */

#ifndef RENAISSANCE_GUI_H
#define RENAISSANCE_GUI_H

#include "gfx_type.h"
#include "core/math_func.hpp"

/** Waiting cargo with a displayed service rating below 50% merits inspection. */
constexpr bool CargoNeedsAttention(bool has_rating, uint available, uint8_t rating)
{
	/* Match the integer percentage displayed by the station window. */
	return has_rating && available != 0 && ToPercent8(rating) < 50;
}

/**
 * Sample a cyclic palette with linear interpolation, including the wrap boundary.
 * @param colours Non-empty palette cycle.
 * @param phase Fraction of one complete cycle, in 1/65536 units.
 * @param offset Whole palette entries by which to offset the sample.
 */
inline Colour SampleWaterPalette(std::span<const Colour> colours, uint16_t phase, uint offset)
{
	assert(!colours.empty());
	const uint32_t position = uint32_t(phase) * static_cast<uint32_t>(colours.size());
	const size_t index = ((position >> 16) + offset) % colours.size();
	const Colour &a = colours[index];
	const Colour &b = colours[(index + 1) % colours.size()];
	const uint32_t fraction = position & 0xFFFF;
	auto blend = [fraction](uint8_t from, uint8_t to) -> uint8_t {
		return (uint32_t(from) * (65536 - fraction) + uint32_t(to) * fraction + 32768) >> 16;
	};
	return Colour(blend(a.r, b.r), blend(a.g, b.g), blend(a.b, b.b), blend(a.a, b.a));
}

#endif /* RENAISSANCE_GUI_H */
