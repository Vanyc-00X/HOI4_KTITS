# Этап 10 — AI-стратегии

Версия мода: **0.10.0**

Генератор: `python tools/build_ai.py`

## Содержимое

### Strategy plans (`common/ai_strategy_plans/mk_strategy_plans.txt`)
На каждую из 24 стран — **2 плана** (всего 48):

| План | Когда активен | Фокусы |
|---|---|---|
| `{TAG}_keep_plan` | исторический фокус / до Великого Поворота / ветка keep | start → eco → **keep** → army → diplo → secret |
| `{TAG}_radical_plan` | не исторический + Поворот или Абсурд >39 | start → eco → **альтернатива** → army → diplo → secret |

Альтернативная ветка задана в `ALT_BRANCH` генератора (агрессивные страны чаще берут A/B).

### Strategies (`common/ai_strategy/mk_strategies.txt`)
- `mk_unit_production` — пехота/заводы для всех MK-стран
- `mk_pp_priorities` — приоритеты траты ПП
- `mk_absurd_aggression` — при высоком Абсурде больше армий и военных заводов
- `{TAG}_diplomacy_default` — дружба/альянс с единомышленниками по стартовой идеологии
- `{TAG}_diplomacy_absurd` — антагонизм (и conquer у агрессоров) при высоком Абсурде / ревизионизме / эре кризисов
- `{TAG}_hunt_{OTHER}` — охота на ревизиониста из своего блока
- дипломатический уклон у ADL/KMS/HRL/…
- давление интеграции у DMK/ZNS/SHF/HRL

### Areas / theaters
- `common/ai_areas/mk_areas.txt` — зоны суши 1–24 и морей 25–43
- `common/ai_faction_theaters/mk_theaters.txt` — театр Казуалии + морской

### Решения
В `mk_global_decisions.txt` добавлены `ai_will_do` для альянсов, ревизионизма, Конгресса, НПТ, финалов.

## Проверки
- 1040 ссылок на фокусы в планах — все существуют
- `tools/check_refs.py` — 0 проблем
- `tools/validate_mod.py` — 0 проблем
