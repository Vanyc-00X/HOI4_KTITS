# Mir Kazualnosti (HOI4)

Total conversion for **Hearts of Iron IV 1.19.\***  
«Мир Казуальности: Эпоха Сходящих с Ума Правителей» — 24 кастомных страны, своя карта, фокусы, сюжет, НПТ, альянсы и AI.

Repository: https://github.com/Vanyc-00X/HOI4_KTITS

## Requirements

- Hearts of Iron IV **1.19.\***
- Single-player or multiplayer **with the same mod build** on every PC
- Do **not** mix with vanilla / other total conversions in one playset

## Install (recommended)

1. Download / clone this repo.
2. Copy the whole folder into:
   ```
   Documents\Paradox Interactive\Hearts of Iron IV\mod\Mir_Kazualnosti\
   ```
3. Create (or edit) next to it:
   ```
   Documents\Paradox Interactive\Hearts of Iron IV\mod\Mir_Kazualnosti.mod
   ```
   Example contents:

```text
version="0.15.1"
tags={
	"Alternative History"
	"Total Conversion"
	"Map"
	"National Focuses"
	"Gameplay"
}
name="Mir Kazualnosti: Epokha Skhodyashchikh s Uma Pravitely"
replace_path="history/countries"
replace_path="history/states"
replace_path="history/units"
replace_path="history/diplomacy"
replace_path="history/general"
replace_path="common/bookmarks"
replace_path="map/strategicregions"
replace_path="common/ai_strategy_plans"
replace_path="common/ai_strategy"
replace_path="common/ai_areas"
replace_path="common/ai_faction_theaters"
replace_path="common/national_focus"
replace_path="common/on_actions"
replace_path="events"
replace_path="common/decisions"
supported_version="1.19.*"
path="mod/Mir_Kazualnosti"
```

4. Or set an **absolute Latin path** (important on OneDrive / non-English Documents folders such as `Έγγραφα`):
   ```text
   path="C:/HOI4Mods/Mir_Kazualnosti"
   ```
   and put the mod files in that ASCII folder. Paradox often fails to load mods from Greek/Cyrillic paths.

5. Launcher → enable only this mod → Play.  
   You must see **VCI / SOY / BTR / …**, not Germany/USSR.

### OneDrive / Greek Documents fix

If your path looks like:

`C:\Users\...\OneDrive\Έγγραφα\Paradox Interactive\Hearts of Iron IV\mod`

copy the mod to `C:\HOI4Mods\Mir_Kazualnosti` and point `path=` there. Keep the `.mod` file in the launcher `mod` folder.

## Multiplayer

Works if **all players**:

- use the **same** commit / zip of this mod;
- enable the same playset;
- use HOI4 **1.19.\*** (same patch; DLC list should match as much as possible);
- host creates the lobby with the mod already on.

## What’s in the mod

- 24 tags, custom map, bookmarks
- National focuses (84–96 per country), decisions, events, plot chain
- Mechanics: Degree of Absurdity, weighted World Congress ballots and collective war mandates, NPT (fascism only), ideology blocs + revisionism
- 24 distinct ruler traits; captured rulers can return as political or high-command advisors
- Cosmetic renames/flags on political courses
- AI strategy plans / areas / theaters
- Resources scattered on all states: steel / oil / aluminium / rubber / tungsten / chromium + **coal** (1.19 energy), also as focus rewards
- Railway links and tiered supply hubs, plus artillery, cavalry and motorized national army templates with named commanders
- 1939 **Border Crisis** bookmark with changed ownership and governments, active wars, and two new infantry weapon technologies

Version in `descriptor.mod` / `tools/register_mod.py`: **0.15.1**

## Rebuild tools (optional)

Python helpers live in `tools/`:

```bash
python tools/build_countries.py
python tools/build_ruler_content.py
python tools/build_ai.py
python tools/build_flags.py
python tools/build_resources.py
python tools/add_coal_focus_rewards.py
python tools/check_refs.py
python tools/validate_mod.py
python tools/register_mod.py
```

## Docs

See `docs/ETAP_*.md` and `MODLOG.md` for stage notes.

## License / notes

- Personal / friend sharing and this GitHub repo upload by the authors.
- Do not redistribute Paradox Interactive game binaries.
- Own only games you play; offline / single-player and matched multiplayer only — no anti-cheat / multiplayer cheat use.
