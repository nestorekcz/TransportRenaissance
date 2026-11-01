/** Offline art-fixture authoring; uses the existing house command and settings. */
static bool ConAtelierTree(std::span<std::string_view> argv)
{
	if (argv.empty()) { IConsolePrint(CC_HELP, "atelier_tree <x> <y> <type 0..2>; offline art fixture only"); return true; }
	if (argv.size() != 4 || _game_mode != GM_NORMAL || _networking) return false;
	auto x = ParseInteger<uint32_t>(argv[1]);
	auto y = ParseInteger<uint32_t>(argv[2]);
	auto type = ParseInteger<uint8_t>(argv[3]);
	if (!x || !y || !type || *type > 2 || *x >= Map::SizeX() || *y >= Map::SizeY()) return false;
	TileIndex tile = TileXY(*x, *y);
	Backup<CompanyID> company(_current_company, GetFirstPlayableCompanyID());
	auto result = Command<CMD_PLANT_TREE>::Do({DoCommandFlag::Execute}, tile, tile, *type, false);
	company.Restore();
	if (result.Succeeded()) { SetTreeGrowth(tile, TreeGrowthStage::Grown); MarkTileDirtyByTile(tile); }
	IConsolePrint(result.Succeeded() ? CC_INFO : CC_ERROR, "ATELIER_TREE {},{} {}", *x, *y, result.Succeeded() ? "OK" : "FAILED");
	return true;
}

static bool ConAtelierHouse(std::span<std::string_view> argv)
{
	if (argv.empty()) {
		IConsolePrint(CC_HELP, "Place one protected house for an art fixture. Usage: atelier_house <x> <y> <house-id>. Requires house placement enabled and NewGRF developer tools; offline only.");
		return true;
	}
	if (argv.size() != 4 || _game_mode != GM_NORMAL || _networking) return false;
	auto x = ParseInteger<uint32_t>(argv[1]);
	auto y = ParseInteger<uint32_t>(argv[2]);
	auto house = ParseInteger<uint16_t>(argv[3]);
	if (!x || !y || !house || *x >= Map::SizeX() || *y >= Map::SizeY()) return false;
	Backup<CompanyID> company(_current_company, OWNER_DEITY);
	auto result = Command<CMD_PLACE_HOUSE>::Do({DoCommandFlag::Execute}, TileXY(*x, *y), static_cast<HouseID>(*house), true, true);
	company.Restore();
	IConsolePrint(result.Succeeded() ? CC_INFO : CC_ERROR, "ATELIER_HOUSE {},{} id={} {}", *x, *y, *house, result.Succeeded() ? "OK" : "FAILED");
	return true;
}

/** Flush the viewport after positioning it, for reproducible native captures. */
static bool ConAtelierView(std::span<std::string_view> argv)
{
	if (argv.empty()) { IConsolePrint(CC_HELP, "atelier_view <zoom> <x> <y>; offline art fixture only"); return true; }
	if (argv.size() != 4 || _game_mode != GM_NORMAL || _networking) return false;
	auto zoom = ParseInteger<uint8_t>(argv[1]);
	auto x = ParseInteger<uint32_t>(argv[2]);
	auto y = ParseInteger<uint32_t>(argv[3]);
	if (!zoom || !x || !y || *zoom > to_underlying(ZoomLevel::Max) || *x >= Map::SizeX() || *y >= Map::SizeY()) return false;
	IConsoleCmdExec(fmt::format("zoomto {}", *zoom));
	ScrollMainWindowToTile(TileXY(*x, *y), true);
	UpdateViewportPosition(GetMainWindow(), 0);
	return true;
}

/** Read-only audit of imported fleet graphics and unchanged native economics. */
static bool ConAtelierFleetAudit(std::span<std::string_view> argv)
{
	if (argv.empty()) { IConsolePrint(CC_HELP, "atelier_fleet_audit; offline graphics validation"); return true; }
	if (argv.size() != 1 || _game_mode != GM_NORMAL || _networking) return false;
	for (const Engine *e : Engine::Iterate()) {
		uint valid = 0;
		for (uint d = 0; d < 8; ++d) {
			VehicleSpriteSeq seq{};
			GetCustomVehicleIcon(e->index, static_cast<Direction>(d), EIT_PURCHASE, &seq);
			if (seq.IsValid() && SpriteExists(seq.seq[0].sprite)) {
				const Sprite *sprite = GetSprite(seq.seq[0].sprite, SpriteType::Normal);
				if (sprite->width > 0 && sprite->height > 0) ++valid;
			}
		}
		bool ground = e->type == VEH_TRAIN || e->type == VEH_ROAD;
		IConsolePrint(CC_INFO, "FH_ENGINE id={} type={} provider={:08X} valid={} speed={} power={} weight={} capacity={} cargo={} cost={} running={} intro={} life={} climates={} refit={}",
			e->index.base(), static_cast<uint>(e->type), e->GetGRF() == nullptr ? 0 : e->GetGRF()->grfid, valid,
			e->GetDisplayMaxSpeed(), ground ? e->GetPower() : 0, ground ? e->GetDisplayWeight() : 0,
			e->GetDisplayDefaultCapacity(), e->GetDefaultCargoType(), e->GetCost(), e->GetRunningCost(),
			e->info.base_intro.base(), e->info.lifelength.base(), e->info.climates.base(), e->info.refit_mask);
	}
	return true;
}

static bool ConAtelierFleetShop(std::span<std::string_view> argv)
{
	if (argv.empty()) { IConsolePrint(CC_HELP, "atelier_fleet_shop <type 0..3>; offline vehicle preview"); return true; }
	if (argv.size() != 2 || _game_mode != GM_NORMAL || _networking) return false;
	auto type = ParseInteger<uint8_t>(argv[1]);
	if (!type || *type > 3) return false;
	ShowBuildVehicleWindow(INVALID_TILE, static_cast<VehicleType>(*type));
	return true;
}
