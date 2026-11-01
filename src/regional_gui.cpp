/* Transport Renaissance regional development. GPL-2.0-only. */
#include "stdafx.h"
#include "regional.h"
#include "window_gui.h"
#include "window_func.h"
#include "strings_func.h"
#include "gfx_func.h"
#include "viewport_func.h"
#include "viewport_type.h"
#include "command_func.h"
#include "dropdown_type.h"
#include "dropdown_func.h"
#include "querystring_gui.h"
#include "tilehighlight_func.h"
#include "settings_type.h"
#include "town.h"
#include "company_base.h"
#include "table/strings.h"
#include "table/sprites.h"
#include "safeguards.h"

enum RegionalWidgets { R_CAPTION, R_FOUND, R_GROUP, R_KIND, R_BUILD, R_INSPECT, R_DENSITY, R_BRUSH, R_LAYOUT, R_OVERLAY, R_OVERVIEW, R_NEXT, R_LOCATE, R_REMOVE, R_DEMOLISH, R_CAPACITY, R_EFFICIENCY, R_STORAGE, R_CLEAN, R_BODY, R_SCROLL };
static constexpr std::initializer_list<NWidgetPart> regional_widgets = {
	NWidget(NWID_HORIZONTAL),
		NWidget(WWT_CLOSEBOX, COLOUR_DARK_GREEN),
		NWidget(WWT_CAPTION, COLOUR_DARK_GREEN, R_CAPTION), SetStringTip(STR_REGIONAL_TITLE),
		NWidget(WWT_DEFSIZEBOX, COLOUR_DARK_GREEN),
	EndContainer(),
	NWidget(NWID_HORIZONTAL),
		NWidget(WWT_PUSHTXTBTN, COLOUR_GREY, R_FOUND), SetStringTip(STR_REGIONAL_FOUND), SetFill(1, 0),
		NWidget(WWT_DROPDOWN, COLOUR_GREY, R_GROUP), SetStringTip(STR_JUST_RAW_STRING), SetMinimalSize(130, 14), SetFill(1, 0),
		NWidget(WWT_DROPDOWN, COLOUR_GREY, R_KIND), SetStringTip(STR_JUST_RAW_STRING), SetMinimalSize(220, 14), SetFill(1, 0),
		NWidget(WWT_PUSHTXTBTN, COLOUR_GREY, R_BUILD), SetStringTip(STR_REGIONAL_BUILD), SetFill(1, 0),
	EndContainer(),
	NWidget(NWID_HORIZONTAL),
		NWidget(WWT_PUSHTXTBTN, COLOUR_GREY, R_INSPECT), SetStringTip(STR_REGIONAL_INSPECT), SetFill(1, 0),
		NWidget(WWT_PUSHTXTBTN, COLOUR_GREY, R_DENSITY), SetStringTip(STR_JUST_RAW_STRING), SetMinimalSize(115, 14), SetFill(1, 0),
		NWidget(WWT_PUSHTXTBTN, COLOUR_GREY, R_BRUSH), SetStringTip(STR_JUST_RAW_STRING), SetMinimalSize(115, 14), SetFill(1, 0),
		NWidget(WWT_PUSHTXTBTN, COLOUR_GREY, R_LAYOUT), SetStringTip(STR_JUST_RAW_STRING), SetMinimalSize(180, 14), SetFill(1, 0),
	EndContainer(),
	NWidget(NWID_HORIZONTAL),
		NWidget(WWT_DROPDOWN, COLOUR_GREY, R_OVERLAY), SetStringTip(STR_JUST_RAW_STRING), SetMinimalSize(180, 14), SetFill(1, 0),
		NWidget(WWT_PUSHTXTBTN, COLOUR_GREY, R_OVERVIEW), SetStringTip(STR_REGIONAL_OVERVIEW), SetFill(1, 0),
		NWidget(WWT_PUSHTXTBTN, COLOUR_GREY, R_NEXT), SetStringTip(STR_REGIONAL_NEXT), SetFill(1, 0),
		NWidget(WWT_PUSHTXTBTN, COLOUR_GREY, R_LOCATE), SetStringTip(STR_REGIONAL_LOCATE), SetFill(1, 0),
	EndContainer(),
	NWidget(NWID_HORIZONTAL),
		NWidget(WWT_PANEL, COLOUR_GREY, R_BODY), SetMinimalSize(580, 260), SetResize(1, 1), SetFill(1, 1), SetScrollbar(R_SCROLL), EndContainer(),
		NWidget(NWID_VSCROLLBAR, COLOUR_GREY, R_SCROLL),
	EndContainer(),
	NWidget(NWID_HORIZONTAL),
		NWidget(WWT_PUSHTXTBTN, COLOUR_GREY, R_REMOVE), SetStringTip(STR_REGIONAL_REMOVE), SetFill(1, 0),
		NWidget(WWT_PUSHTXTBTN, COLOUR_GREY, R_DEMOLISH), SetStringTip(STR_REGIONAL_DEMOLISH), SetFill(1, 0),
		NWidget(WWT_PUSHTXTBTN, COLOUR_GREY, R_CAPACITY), SetStringTip(STR_REGIONAL_CAPACITY), SetFill(1, 0),
		NWidget(WWT_PUSHTXTBTN, COLOUR_GREY, R_EFFICIENCY), SetStringTip(STR_REGIONAL_EFFICIENCY), SetFill(1, 0),
		NWidget(WWT_PUSHTXTBTN, COLOUR_GREY, R_STORAGE), SetStringTip(STR_REGIONAL_STORAGE), SetFill(1, 0),
		NWidget(WWT_PUSHTXTBTN, COLOUR_GREY, R_CLEAN), SetStringTip(STR_REGIONAL_CLEAN), SetFill(1, 0),
		NWidget(WWT_RESIZEBOX, COLOUR_GREY),
	EndContainer(),
};
static WindowDesc regional_desc(WDP_AUTO, "regional", 600, 370, WC_REGIONAL, WC_NONE, WindowDefaultFlag::Construction, regional_widgets);
static constexpr std::array<std::string_view, 8> overlay_names{"Overlay: off", "Zoning", "Power", "Water", "Public services", "Environment", "Freight bottlenecks", "Recent station service"};

struct RegionalWindow : Window {
	TileIndex selected = INVALID_TILE;
	TileIndex founding_preview = INVALID_TILE;
	TileIndex demolition_preview = INVALID_TILE;
	uint8_t kind = Regional::Housing, density = 0, group = 0, action = 255, brush = 1;
	bool starter = true;
	std::string town_name = "New Haven", message;
	Scrollbar *vscroll = nullptr;
	RegionalWindow() : Window(regional_desc) { this->CreateNestedTree(); vscroll = this->GetScrollbar(R_SCROLL); vscroll->SetStepSize(GetCharacterHeight(FS_NORMAL)); this->FinishInitNested(0); }
	std::string GetWidgetString(WidgetID widget, StringID stringid) const override {
		switch (widget) {
			case R_KIND: return std::string(Regional::definitions[kind].name);
			case R_GROUP: return std::array<std::string, 3>{"City zones", "Infrastructure", "Industries"}[group];
			case R_DENSITY: return fmt::format("Housing density: {}", density + 1);
			case R_BRUSH: return fmt::format("Brush: {} x {}", brush, brush);
			case R_LAYOUT: return starter ? "Founding: starter street" : "Founding: manual roads";
			case R_OVERLAY: return std::string(overlay_names[_regional_overlay]);
			default: return this->Window::GetWidgetString(widget, stringid);
		}
	}
	void DrawWidget(const Rect &r, WidgetID widget) const override {
		if (widget != R_BODY) return;
		std::string body;
		if (!message.empty()) body = message + "\n\n";
		if (auto *l = GetRegionalLot(selected)) body += RegionalDescribe(*l);
		else body += RegionalOverview();
		if (action == 0) {
			const auto &d = Regional::definitions[kind];
			int64_t price = _settings_game.economy.regional_mode == 2 ? 0 : d.cost * (kind == Regional::Housing ? density + 1 : 1);
			body = fmt::format("{}\nCost {} per lot | maximum brush cost {} | upkeep {} / cycle\nFlat empty land, regional town within 48 tiles. Road frontage required to develop.\nPower and water connect along roads. Zoning never clears existing structures.\n{}\n\n{}", d.name, RegionalMoney(price), RegionalMoney(price * brush * brush), RegionalMoney(_settings_game.economy.regional_mode == 2 ? 0 : d.upkeep),
				kind >= Regional::Farm ? "Inputs must arrive by vehicle. Click a reserved lot to inspect development." : "Housing and shops need power and water before construction starts.", body);
		}
		Rect ir = r.Shrink(8);
		uint height = GetStringHeight(body, ir.Width());
		vscroll->SetCapacity(ir.Height()); vscroll->SetCount(height);
		DrawPixelInfo clip;
		if (!FillDrawPixelInfo(&clip, ir)) return;
		clip.left += ir.left; clip.top += ir.top;
		AutoRestoreBackup dpi(_cur_dpi, &clip);
		int top = ir.top - vscroll->GetPosition();
		DrawStringMultiLine(ir.left, ir.right, top, top + height, body, TC_BLACK);
	}
	void PlaceTool(uint8_t next) {
		action = next; message.clear(); founding_preview = INVALID_TILE; demolition_preview = INVALID_TILE;
		SetObjectToPlaceWnd(SPR_CURSOR_TOWN, PAL_NONE, HT_RECT, this);
		SetTileSelectSize(next == 7 ? 9 : brush, next == 7 ? 5 : brush);
		if (next == 7) message = "Founding preview: 9 x 5 flat empty initial area. Boundary: 48-tile service/planning radius.\nClick a site for its full founding cost. No fixed town upkeep; each developed lot pays its own upkeep.";
		this->SetDirty();
	}
	void OnClick(Point, WidgetID widget, int) override {
		switch (widget) {
			case R_FOUND: ShowQueryString(town_name, STR_REGIONAL_FOUND, 60, this, CS_ALPHANUMERAL, {QueryStringFlag::AcceptUnchanged}); break;
			case R_GROUP: {
				DropDownList list; int n = 0; for (auto name : {"City zones", "Infrastructure", "Industries"}) list.push_back(MakeDropDownListStringItem(name, n++));
				ShowDropDownList(this, std::move(list), group, widget); break;
			}
			case R_KIND: {
				DropDownList list;
				for (uint8_t n = 0; n < Regional::End; ++n) if ((group == 0 && n <= Regional::Park) || (group == 1 && n >= Regional::Solar && n <= Regional::School) || (group == 2 && n >= Regional::Farm)) list.push_back(MakeDropDownListStringItem(std::string(Regional::definitions[n].name), n));
				ShowDropDownList(this, std::move(list), kind, widget); break;
			}
			case R_OVERLAY: { DropDownList list; for (uint8_t n = 0; n < overlay_names.size(); ++n) list.push_back(MakeDropDownListStringItem(std::string(overlay_names[n]), n)); ShowDropDownList(this, std::move(list), _regional_overlay, widget); break; }
			case R_BUILD: PlaceTool(0); break;
			case R_INSPECT: PlaceTool(255); break;
			case R_REMOVE: PlaceTool(1); break;
			case R_DEMOLISH: PlaceTool(2); message = "Demolition costs 10% of actual investment (minimum 20). No refunds. Buildings and inventories will be removed. Click a lot to preview, then click it again to confirm."; break;
			case R_DENSITY: density = (density + 1) % 3; break;
			case R_BRUSH: brush = brush == 5 ? 1 : brush + 2; if (action != 255) PlaceTool(action); break;
			case R_LAYOUT: starter = !starter; break;
			case R_OVERVIEW: selected = INVALID_TILE; message.clear(); ResetObjectToPlace(); action = 255; break;
			case R_LOCATE: if (selected != INVALID_TILE) ScrollMainWindowToTile(selected); break;
			case R_NEXT: {
				auto it = _regional_lots.upper_bound(selected); if (it == _regional_lots.end()) it = _regional_lots.begin();
				for (size_t n = 0; n < _regional_lots.size(); ++n) { if (it->second.limit) { selected = it->first; ScrollMainWindowToTile(selected); break; } if (++it == _regional_lots.end()) it = _regional_lots.begin(); }
				message.clear(); break;
			}
			case R_CAPACITY: case R_EFFICIENCY: case R_STORAGE: case R_CLEAN: {
				uint8_t a = 3 + widget - R_CAPACITY;
				if (selected == INVALID_TILE) { message = "Inspect a completed lot first."; break; }
				auto result = Command<CMD_REGIONAL_ACTION>::Do({}, selected, a, uint8_t{0}, uint8_t{0}, std::string{});
				if (result.Failed()) { message = "Upgrade unavailable: complete construction, check ownership and the two-level limit."; break; }
				if (action != a) { action = a; message = fmt::format("Upgrade costs {}. Click this upgrade again to apply. Capacity raises upkeep and demand; efficiency reduces utility use; storage adds 256 units; cleanup reduces pollution and adds upkeep.", RegionalMoney(result.GetCost())); }
				else { Command<CMD_REGIONAL_ACTION>::Post(STR_REGIONAL_ERROR, selected, a, uint8_t{0}, uint8_t{0}, std::string{}); action = 255; message.clear(); }
				break;
			}
		}
		this->SetDirty();
	}
	void OnDropdownSelect(WidgetID widget, int index, int) override {
		if (widget == R_KIND) kind = index;
		if (widget == R_GROUP) { group = index; kind = index == 0 ? Regional::Housing : index == 1 ? Regional::Solar : Regional::Farm; }
		if (widget == R_OVERLAY) { _regional_overlay = index; MarkWholeScreenDirty(); }
		this->SetDirty();
	}
	void OnQueryTextFinished(std::optional<std::string> text) override { if (text && !text->empty()) { town_name = *text; PlaceTool(7); } }
	void OnPlaceObject(Point, TileIndex tile) override {
		if (action == 255) { selected = tile; message.clear(); this->SetDirty(); return; }
		if (action == 7) {
			TileIndex centre = TileAddXY(tile, 4, 2);
			auto error = RegionalFoundingError(centre, town_name);
			if (!error.empty()) { founding_preview = INVALID_TILE; message = error; this->SetDirty(); return; }
			auto quote = Command<CMD_REGIONAL_ACTION>::Do({}, centre, uint8_t{7}, uint8_t(starter), uint8_t{0}, town_name);
			if (quote.Failed()) { message = "The starter street cannot be built here. Choose manual roads or another site."; this->SetDirty(); return; }
			if (founding_preview != tile) {
				founding_preview = tile;
				message = fmt::format("Found {} for {} including {}. Click the same site again to confirm.\nNo fixed town maintenance; developed lots pay their displayed upkeep.", town_name, RegionalMoney(quote.GetCost()), starter ? "the nine-tile starter street" : "manual road planning");
				this->SetDirty(); return;
			}
			Command<CMD_REGIONAL_ACTION>::Post(STR_REGIONAL_ERROR, centre, uint8_t{7}, uint8_t(starter), uint8_t{0}, town_name);
			founding_preview = INVALID_TILE; message.clear(); this->SetDirty(); return;
		}
		if (action == 2 && tile != demolition_preview) {
			selected = tile;
			auto quote = Command<CMD_REGIONAL_ACTION>::Do({}, tile, uint8_t{2}, uint8_t{0}, uint8_t{0}, std::string{});
			if (quote.Failed()) { message = "Choose a lot owned by your company."; demolition_preview = INVALID_TILE; }
			else { demolition_preview = tile; message = fmt::format("Demolition costs {} and removes this building and its inventories. Click the same lot again to confirm.", RegionalMoney(quote.GetCost())); }
			this->SetDirty(); return;
		}
		if (action == 0) {
			uint32_t valid = 0; std::string why;
			for (uint8_t x = 0; x < brush; ++x) for (uint8_t y = 0; y < brush; ++y) {
				TileIndex t = TileAddXY(tile, x, y); auto error = RegionalPlacementError(t, kind);
				if (!error.empty()) { why = error; continue; }
				Command<CMD_REGIONAL_ACTION>::Post(STR_REGIONAL_ERROR, t, action, kind, density, std::string{}); ++valid;
			}
			message = fmt::format("{} lots requested. {}", valid, why);
		} else if (action <= 2 || action == 7) Command<CMD_REGIONAL_ACTION>::Post(STR_REGIONAL_ERROR, action == 7 ? TileAddXY(tile, 4, 2) : tile, action, action == 7 ? uint8_t(starter) : kind, density, town_name);
		selected = tile; this->SetDirty();
	}
	void OnPlaceObjectAbort() override { action = 255; this->SetDirty(); }
	void OnInvalidateData(int, bool) override { this->SetDirty(); }
};
void ShowRegionalWindow(TileIndex tile) {
	auto *w = dynamic_cast<RegionalWindow *>(FindWindowById(WC_REGIONAL, 0));
	if (!w) w = new RegionalWindow();
	w->selected = tile; w->message.clear(); w->SetDirty();
}
