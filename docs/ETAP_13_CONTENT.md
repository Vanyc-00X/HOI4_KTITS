# Этап 13 — контент, AI, ресурсы, альянсы

Версия мода: **0.12.0**

## Больше фокусов
Через `tools/focus_flavor.py` деревья расширены:
- крупные страны: **88** фокусов (было 62)
- остальные: **76** (было 50)
- всего в моде: **1953** фокуса

Новые награды: ресурсы, invite-all, casus belli, guarantee, саммиты, «поводы» генштаба.

## Больше событий
- у каждой страны **19** событий (было 14), в т.ч. 15–19 flavor
- глобальные `mk_flavor.1–8` + месячный пульс `mk_monthly_flavor_pulse`
- итого событий в моде: **510**

## Умнее AI
- выше веса befriend/alliance/support для единомышленников
- `mk_alliance_drive`, `mk_war_focus`, industrial bias
- сильнее push на `mk_dec_form_ideology_faction` (factor 25)
- планы учитывают расширенные деревья и eco/diplo/army

## Альянс = мгновенные приглашения
`mk_form_ideology_faction_effect` и `mk_form_npt_protocol_effect`:
после `create_faction` — `every_other_country` с той же идеологией (мирные, не в фракции) сразу получают `add_to_faction`.

## Ресурсы на карте
`python tools/build_resources.py` — у всех 127 штатов есть steel/oil/aluminium/rubber/tungsten/chromium по профилю владельца.

## Команды
```
python tools/build_countries.py
python tools/build_ai.py
python tools/build_resources.py
python tools/write_stage13_loc.py
python tools/register_mod.py
python tools/check_refs.py
python tools/validate_mod.py
```
