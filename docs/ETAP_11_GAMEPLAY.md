# Этап 11 — доработка геймплея

Версия мода: **0.11.0**

Цель: цельный сюжет, интересные развилки и ощущение, что курс меняет не только бонусы, но и «лицо» державы.

## Что сделано

### Косметика по идеологии
При выборе политической ветки (первый фокус курса):
- `set_cosmetic_tag = TAG_ideology` → новое название страны и флаг (`gfx/flags/TAG_ideology.tga` + medium/small)
- `set_character_name` → тот же правитель, другое обращение
- пример VCI: **Император Марат Казуалович** → **Товарищ Казуал Марат** / **Вождь Марат Сабиров** / **Президент Марат Сабиров**

Источник имён и RGB флагов: `tools/country_cosmetics.py`.  
Генераторы: `tools/build_countries.py`, `tools/build_flags.py` (360 TGA, только 24 MK-тега).

### НПТ только у фашизма
- триггер `mk_can_use_npt` / `mk_can_form_npt_protocol` → `has_government = fascism`
- эффект `mk_add_npt` игнорирует прирост без фашизма
- фокусы/решения/generic NPT: `available = { has_government = fascism }`
- стартовый seed НПТ: BTR + CRE (не SOY)

### Фокусы: альянсы и оправдание войн
- армия: casus belli (`topple_government` / `puppet_wargoal_focus`) + абсурд
- дипломатия: идеологический kin, invite в фракцию, guarantee, голоса Конгресса
- финал фашистской ветки: wargoal на соседа + НПТ
- финал коммунизма: мнение красных соседей; демократии — голоса

### Сюжет (`events/mk_plot_events.txt`)
Сквозная линия `mk_plot.1`…`10`, завязанная на глобальные эффекты эпох:
1–2 Перелом → 3–4 маски/имена после Поворота → 5 блоки → 6–7 войны с поводами → 8–10 НПТ (только фашизм / тревога остальных).

У каждой страны — вариативные опции intro/веток/механики (не один шаблон на все идеологии).

## Как проверить в игре
1. VCI → коммунистическая ветка → страна «Казуальная Народная Империя», лидер «Товарищ Казуал Марат», другой флаг.
2. Нефашист: категория/решения НПТ недоступны; фокусы `mk_gen_npt_*` серые.
3. Фашист (BTR/CRE или ветка fascism): НПТ растёт, события 8–9 имеют смысл.
4. Через ~30 дней — news `mk_plot.1`; после Поворота — 3–4.

## Файлы
- `tools/country_cosmetics.py`, `tools/build_countries.py`, `tools/build_flags.py`, `tools/write_stage11_loc.py`
- `events/mk_plot_events.txt`, `common/scripted_triggers/mk_global_triggers.txt`, `common/scripted_effects/mk_global_effects.txt`
- `localisation/russian/mk_events_l_russian.yml` (+ per-tag loc)
