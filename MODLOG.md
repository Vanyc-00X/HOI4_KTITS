# MODLOG — Мир Казуальности

## Intake
- Игра: Hearts of Iron IV (single-player / offline total conversion)
- Идея: тотальная конверсия, 24 государства, глобальные механики абсурда
- ТЗ: `ресурсы/docs/ТЗ_Мода.md` v3.0
- Корень мода: `D:\Dowland\Mod\Games\HOI4\ПРОГЕРЫ МОД`
- Ресурсы: `ресурсы\` (ImageSovereigns — портреты)
- История реализации и актуальная версия описаны в записях этапов ниже.

## Route
- Data-only Paradox scripting (focuses, ideas, decisions, events, map)
- Не трогаем ванильные файлы; `replace_path` для history/map/focus/events
- universal-modder: journal + поэтапная поставка

## Этап 1 — 2026-10-03
- Создана структура папок
- descriptor.mod v0.1.0, supported_version 1.16.*
- 24 country tags: VCI SOY BTR KRZ KZS MUS TRF ZLD ISL CLB ADL DMK FDP CRE SVA ART KMS ZNS ZKR ZML NBL ISG HRL SHF
- colors + country gfx stubs
- RU локализация названий стран
- Архитектура карты: ~110–130 states, ~900–1200 provinces, 24–28 strategic regions
- Полный roadmap файлов в docs/ETAP_01_ARCHITECTURE.md

## Этап 2 — 2026-10-03
- history/countries × 24 (politics, popularities, capital 1–24, recruit_character)
- common/characters × 24 (тот же лидер на 4 идеологии)
- common/ideas/mk_starting_ideas.txt — 24 стартовых духа
- history/units/*_1936.txt × 24 (пустые OOB)
- bookmark mk_era_of_mad_rulers.txt
- loc: mk_leaders, mk_parties, mk_ideas, mk_bookmark, mk_ideologies_flavor
- docs/ETAP_02_COUNTRIES.md, docs/CAPITAL_STATE_IDS.md

## Этап 3 — 2026-10-03
- Карта 2048×1024: provinces/terrain/rivers/heightmap/cities/world_normal/trees
- definition.csv: provinces + states + strategicregions
- history/states × 127 (столицы 1–24), все 24 TAG на карте
- supply_nodes на столицах, unitstacks/buildings
- Генератор: tools/generate_kazualia_map.py
- docs/ETAP_03_MAP.md

## Crash fix — 2026-10-03 20:03
- Причина: provinces.bmp писался RGB вместо BGR → цвета не совпадали с definition.csv
- Фикс: BGR-запись BMP

## Crash fix — 2026-10-03 20:07
- X-crossing / CHR→CRE / rivers index

## Crash fix — 2026-10-03 20:10
- country_tags stubs / contiguous strips

## Crash fix — 2026-10-03 20:13
- Причины:
  1) replace_path national_focus + events → Unable to find focus tree / 11k invalid focus
  2) море на всю ширину карты → TOO LARGE BOX (wrap)
  3) ещё X-crossing на стыках
- Фикс v0.3.3:
  - убраны replace_path для national_focus и events (ванила грузится)
  - 1 cell = 1 province (0 X-cross)
  - 6 морей без wrap (nw/ne/sw/se/west/east)
  - rivers: точная палитра ванили
  - weatherpositions пустой

## Next
- Ждать «продолжай» → Этап 4 (глобальные механики)
- Нужны портреты 24 лидеров в `ресурсы\ImageSovereigns`
- Первый playtest после копирования .mod в Documents — прислать error.log

## Risks
- Кириллический путь мода → при отказе лаунчера сделать latin junction
- Procedural colormap/реки — визуальные артефакты возможны
- GFX_portrait_unknown warnings до реальных портретов

## Crash fix — 2026-10-03 20:17
- continent.txt restored vanilla continents (portraits parse)
- sea as 32x32 cells (no TOO LARGE BOX)
- flags TGA 24 tags x3 sizes + ideology
- rivers raw vanilla palette; weatherpositions filled
- descriptor v0.3.4

## Crash fix — 2026-10-03 20:25 (v0.3.6)
- Главный краш: coastal=true без naval_base_spawn → 40 портов, coastal только на них
- buildings.txt: только naval_base_spawn (убраны infrastructure/неверные координаты фабрик)
- weatherpositions: формат `sr_id;x;h;y;size`
- удалён битый portraits/mk_portraits.txt
- rivers.bmp: палитра ванили, пустая карта (индекс 254)
- sea SR: flood-fill contiguous chunks (не fractioned)
- replace_path common/ai_strategy + ai_areas + ai_faction_theaters
- stub-флаги 32bpp для ванильных тегов (SCO/CSA и др.)

## Load fix — 2026-10-03 20:37 (v0.3.7)
- Симптом: ванильная карта 1936/1939, мод не грузился
- Причина: `Incorrect MOD descriptor` — regex `path=` затирал все `replace_path`, плюс `path=` пропал; лаунчер брал старую папку `mod/Mir_Kazualnosti` без map
- Фикс: корректный `Mir_Kazualnosti.mod` с path на junction; старая папка → `Mir_Kazualnosti_OLD_no_map`; `tools/register_mod.py`

## Crash/map fix — 2026-10-03 20:42 (v0.3.8)
- X-crossing 1953 → 0 (T-junction на углах клеток)
- coastal: порт на КАЖДОЙ land у моря (132); Y в buildings снизу вверх
- rivers biClrUsed=0; BOM снят с common/countries
- unitstacks пересчитан с инвертированным Y

## Map polish — 2026-10-03 20:46 (v0.3.9)
- wrap X-crossing на x=2047 → склейка с x=0
- buildings: air_base + rocket_site_spawn + special_project на каждый state; без пустой строки
- adjacency_rules/adjacencies очищены (ванильные провинции 12k+)
- common/names/mk_names.txt для 24 тегов

## Crash fix — 2026-10-03 20:52 (v0.3.10)
- Краш: TOO LARGE BOX — склейка x=0/x=2047 дала провинциям пиксели с двух краёв карты
- Фикс: правый край восстановлен; wrap X чинится только на левом столбце (без общих цветов)
- buildings.txt без trailing newline
- восстановлен supported_version="1.19.*" (regex version= снова его затирал)

## Start-campaign crash — 2026-10-03 20:55 (v0.3.11)
- Симптом: error.log почти чистый, краш на `Launching SINGLEPLAYER`
- Причина: ванильные on_startup / focus / events / decisions трогают несуществующие стейты
- replace_path: national_focus, on_actions, events, decisions, scripted_effects/triggers
- пустое default focus tree `mk_generic_focus`
- скопирован leader_unknown.dds

## Start-campaign crash — 2026-10-03 20:58 (v0.3.12)
- v0.3.11 вырезал scripted_triggers → 3k ошибок MIO (`is_literally_china`) — откат
- replace_path `history/general` (spain/china advisors + missing focuses)
- replace_path MIO / peace_conference / special_projects
- unitstacks: 19 слотов на провинцию (как ваниль)

## Start-campaign crash — 2026-10-03 21:02 (v0.3.13)
- replace_path MIO/peace не срабатывал → blank-override все ванильные файлы
- убран special_project_facility_spawn из buildings (пустые special_projects крашили старт)
- мод установлен junction’ом в `Documents/mod/Mir_Kazualnosti`, path=`mod/Mir_Kazualnosti`

## Start-campaign crash — 2026-10-03 21:10 (v0.3.14)
- HARD: `Expected exactly one peace_action_category to be set as default` — blank peace categories
- убраны blank MIO/peace + их replace_path → снова ваниль
- replace_path + blank `common/scripted_effects` (italian/soviet focus load, SWI missions)
- stub focus trees: italian_focus, soviet_focus
- играть: **VCI** (Великая Казуальная Империя), default bookmark

## Start-campaign crash — 2026-10-03 21:15 (v0.3.15)
- Симптом: Launching SINGLEPLAYER за VCI → нативный краш (error.log без hard DB error)
- blank scripted_effects ломал special_projects/tech → **вернули ваниль**
- удалён фантом `province 0` из definition.csv
- убран `rocket_site_spawn` из buildings
- 364 landless stub: capital размазан по стейтам 1–127 (не все на 1)

## Boot crash — 2026-10-03 21:20 (v0.3.16)
- v0.3.15 убрал province 0 → мгновенный краш на Loading Databases/states
- HOI4 **требует** строку `0;...` в definition.csv (как ваниль); без неё сдвигаются свойства провинций
- province 0 возвращён + добавлен в strategic region 1

## Start crash — 2026-10-03 21:25 (v0.3.17)
- SR1: при вставке province 0 съели `}` у `provinces={}` → Malformed weather
- MAP_ERROR `no rocket site` / `no gun emplacement` на всех стейтах → вернул `rocket_site_spawn` ×127
  (оба здания используют один spawn_point)

## Start crash — 2026-10-03 21:30 (v0.3.18)
- CTD после Launching SINGLEPLAYER без MAP_ERROR в логе
- Причина: у всех 132 `naval_base_spawn` поле adjacent sea = **суша** (должен быть sea)
- Пересчитаны sea-соседи по provinces.bmp; + `special_project_facility_spawn` ×127; скопирован colors.txt

## Start crash — 2026-10-03 21:35 (v0.3.19)
- Crash dump: `EXCEPTION_ACCESS_VIOLATION` после Launching (UI уже грузится)
- `nuclear_reactor_spawn` ×127; убран `special_project_facility_spawn`
- опустошены `supply_nodes.txt` / `railways.txt`
- province 0 → sea + SR25; минимальный `ai_areas`

## Этап 4 — 2026-10-03 (v0.4.0)
- Температура Абсурда: `global.mk_absurd_temp`, месячный тик, решения, пороги идей
- 24 Голоса Мира + Всемирный Конгресс (решения/ивенты/кулдаун)
- НПТ: переменная + финансирование/пропаганда/сеть
- Идеологические альянсы + «Обвинить/изгнать ревизиониста»
- Великий Политический Поворот (дата 1936.3.11 или Абсурд ≥40)
- on_actions / decisions / events / ideas / scripted_* / RU loc
- docs/ETAP_04_GLOBAL.md

## Start crash — 2026-10-03 22:45 (v0.4.1)
- Все краши с 20:45 имеют **один и тот же стек** (ACCESS_VIOLATION после Launching) → фиксы v0.3.12–v0.3.19 били мимо
- `tools/validate_mod.py`: статическая сверка bmp↔definition, стейты, SR, здания, порты, столицы, OOB, скобки → карта чистая
- Причины-кандидаты, исправлены:
  1) `mk_generic_focus` (default) и стабы italian/soviet — **пустые деревья без фокусов** → дерево «Казуальный курс» (9 фокусов) + стиль `default_style` + `search_filter_prios`
  2) у 24 стран **нет шаблонов дивизий** → пехотный шаблон + 2 дивизии в столице + стартовое снаряжение
  3) province 0 вернул к ванильному `land;false;unknown;0`, убран из SR25 (ошибка `invalid province '0'`)
  4) supply_nodes на 24 столицах
- Иконки решений/категорий заменены на существующие в ванили
- Loc регионов → `localisation/russian/replace/` (убраны коллизии)
- `register_mod.py` больше не возвращает replace_path для MIO/peace_conference

## Start crash — 2026-10-03 22:55 (v0.4.2) — НАСТОЯЩАЯ ПРИЧИНА
- v0.4.1 упал с тем же стеком → фокусы/OOB были не причиной
- `tools/minidump_strings.py` (uv --with minidump): AV на чтении `0x48` (null + offset),
  на стеке строки `move_camera_to`, `highlight_states_trig`, `obj_1`, `state`
- Это ванильный **`tutorial/tutorial.txt`**: state 550 (Эритрея), провинции 5091/12856/5010/12766…, tag ETH.
  Движок резолвит их при старте партии → на новой карте null → краш
- Фикс: `tools/build_tutorial.py` генерирует tutorial.txt с ремапом на state 1 / провинции VCI / SOY
- `tools/find_hardcoded_ids.py`: поиск ванильных файлов вне replace_path с ID вне нашей карты.
  Структурные (не триггеры) ссылки нашлись в страновых рейдах → пустые
  `common/raids/{air_raids_custom,land_infiltration_custom,paratrooper_raids_custom,naval_commando_raids}.txt`
- Урок: для тотальной конверсии карты **обязательно** перекрывать tutorial.txt; при нативном
  краше без строки в error.log — сначала строки со стека минидампа, потом фиксы
- ✅ 23:00 игра стартовала за VCI без краша

## Этап 5 — 2026-10-03 23:30 (v0.5.0)
- Фикс: `on_startup` без scope → init этапа 4 обёрнут в `VCI = { }` (ошибка Invalid Scope в error.log)
- Генератор `tools/build_countries.py` + данные `tools/country_data_{1,2,3}.py`
- VCI, SOY, BTR, KRZ: 62 фокуса; KZS, MUS: 50; у всех 13 событий, 8 решений, 12 духов, механика `mk_mech`
- 4 курса со сменой идеологии (тот же лидер), секретная ветка, эко/армия/дипломатия
- `common/opinion_modifiers/mk_opinion_modifiers.txt`, `common/scripted_effects/mk_mech_effects.txt`
- Проверка ссылок `tools/check_refs.py`: 0 проблем
- docs/ETAP_05_COUNTRIES_1_6.md
- ✅ 23:36 v0.5.0 стартовала без краша, ошибок мода в error.log нет

## Этап 6 — 2026-10-03 (v0.6.0)
- Данные `tools/country_data_4.py` (TRF, ZLD, ISL) и `_5.py` (CLB, ADL, DMK)
- CLB, DMK: 62 фокуса; TRF, ZLD, ISL, ADL: 50; у всех 13 событий, 8 решений, 12 духов
- Генератор: ключи `exploit_extra` / `exploit_available` в `mech` — особый эффект решения-эксплойта
  (ADL +2 Голоса; DMK мирно забирает пограничную область соседа через `transfer_state`)
- `tools/check_gfx_names.py`: `GFX_idea_generic_diplomacy_bonus` не существует → заменён
- check_refs / validate_mod: 0 проблем
- docs/ETAP_06_COUNTRIES_7_12.md

## Этап 7 — 2026-10-03 23:55 (v0.7.0)
- Данные `tools/country_data_6.py`: FDP, CRE (62 фокуса), SVA, ART, KMS, ZNS (50)
- Особые эксплойты: KMS — мнение соседей `mk_kazual_goodwill`; ZNS — мирная интеграция области
- `check_gfx_names.py --list PREFIX` для подбора существующих иконок
- check_refs / validate_mod: 0 проблем
- docs/ETAP_07_COUNTRIES_13_18.md

## Этап 8 — 2026-10-04 02:40 (v0.8.0)
- Данные `tools/country_data_7.py`: NBL, SHF (62 фокуса), ZKR, ZML, ISG, HRL (50)
- Эксплойты: ZKR/ISG строят гражданский завод, NBL — военный (`add_building_construction` в области
  со свободным слотом); HRL — +1 Голос и мнение соседей
- Все 24 страны имеют свои деревья, `mk_generic_focus` остаётся запасным
- check_refs / validate_mod: 0 проблем
- docs/ETAP_08_COUNTRIES_19_24.md

## Этап 9 — 2026-10-04 02:55 (v0.9.0)
- Ревизионизм по ТЗ: выход из альянса + wargoals vs всех + hesitation у оставшихся + «Осудить ревизионизм»
- 5-й блок: Протокол НПТ; дух члена фракции; wargoal `mk_revisionist_aggression`
- Хронология эпох (развилки / блоки / кризисы / финалы) + ~20 новых глобальных событий (итого ~30)
- Дипломатические решения и 6 финалов кампании
- check_refs / validate_mod: 0 проблем
- docs/ETAP_09_DIPLOMACY.md

## Этап 10 — 2026-10-04 03:55 (v0.10.0)
- Генератор `tools/build_ai.py`: 48 strategy plans, дипломатия/охота на ревизионистов, areas, theaters
- AI weights на глобальных решениях
- 1040 ссылок на фокусы в планах валидны; check_refs / validate_mod: 0
- docs/ETAP_10_AI.md

## Этап 11 — 2026-10-04 19:20 (v0.11.0)
- Геймплей: сквозной сюжет `mk_plot.1–10`, вариативные опции событий по идеологии
- НПТ только при `has_government = fascism` (триггеры, `mk_add_npt`, решения, generic-фокусы); seed BTR+CRE
- Косметика курса: `set_cosmetic_tag` + `set_character_name` + флаги `TAG_ideology` (360 TGA; вычищены 1820 чужих)
- Фокусы: CB/альянсы/invite/guarantee; фашистский финал с wargoal+НПТ
- `tools/country_cosmetics.py`, rebuild countries/flags; check_refs / validate_mod: 0
- docs/ETAP_11_GAMEPLAY.md

## Этап 12 — 2026-10-04 19:25 (v0.11.0)
- Авто: check_refs / validate_mod = 0; smoke косметики/НПТ/сюжета/флагов
- Фикс по error.log: invite в фракцию только в мире (`mk_dec_invite_same_ideology` + фокусы)
- docs/ETAP_12_TESTING.md — ручной чеклист для прогона в HOI4

## Этап 13 — 2026-10-04 20:00 (v0.12.0)
- Деревья 62/50 → 88/76 фокусов; интересные награды (CB, ресурсы, invite-all, саммиты)
- 19 событий/страна + `mk_flavor.1–8` и месячный пульс
- AI: сильнее альянсы/война/индустрия; form-faction AI factor 25
- Создание идеологического альянса / НПТ-протокола сразу зовёт всех единомышленников
- Ресурсы на всех 127 штатах (`build_resources.py`)
- check_refs / validate_mod: 0; docs/ETAP_13_CONTENT.md

## Этап 14 — 2026-10-05 (v0.13.0)
- Уголь (HOI4 1.19, energy): 7-й ресурс во всех 127 штатах — `build_resources.py` (всего 3060; 9–52 на штат, у каждой страны ≥ 47)
- `add_coal_focus_rewards.py`: 78 «стальных» наград фокусов получили парный уголь (54×12, 24×15)
- `validate_mod.py`: проверка `resources` — известные ключи + наличие всех 7 ресурсов
- check_refs / validate_mod: 0; docs/ETAP_14_COAL.md


## Этап 15 — 2026-10-05 (v0.14.0)
- 24 уникальных сильных профиля правителей с персональными плюсами/минусами; traits добавлены всем четырём идеологическим вариантам каждого лидера.
- При капитуляции правитель временно теряет национальный trait; победитель получает событие и выбирает бывшего правителя политическим советником или военным советником Верховного командования с тем же trait. При освобождении trait возвращается.
- Деревья расширены на **192 персональных фокуса** (8 × 24), итого 96/84 фокуса на страну; добавлены тематические экономики, абсурдные casus belli, гарантии, дипломатия, альянсы и коллективная безопасность.
- AI планы/веса учитывают новую ветку; целевой нарушитель Конгресса выбирается по `mk_misconduct`, обычное объявление войны увеличивает проступки.
- Всемирный Конгресс получил взвешенное голосование с кворумом; при абсолютном большинстве поддержавшие страны объявляют коллективную войну с `topple_government`. Осуждённая страна может сопротивляться или принять решение и прекратить огонь с участниками операции.
- Во всех игровых текстах используется «Температура Абсурда».
- `check_refs.py`: 0 проблем; `validate_mod.py`: 0 проблем; генераторы стран/AI/правителей выполнены.
- Ручной запуск HOI4 после этих изменений не выполнялся; нужен игровой smoke-test.
- docs/ETAP_15_WORLD_ORDER.md

## Этап 16 — 2026-10-06 (v0.15.0)
- Карта стала более естественной формы: сформирована неровная береговая линия и слегка искривлены границы провинций без X-пересечений.
- Добавлены/согласованы игровые биомы: степные равнины, леса, холмы, горы, болота, пустыни и джунгли; рельеф отражён в heightmap и normal map.
- Речной растр ограничен сушей; заполнены лесной покров, столицы и городские центры штатов.
- После обновления: 982 сухопутные и 1066 морских провинций, 127 штатов, 43 стратегических региона.
- Генератор карты сохраняет текущие state resources, игровые city groups и map rules.
- Проверки `check_refs.py`, `validate_mod.py`, `py_compile` и `git diff --check` пройдены; игровой запуск HOI4 не выполнялся.

## Этап 17 — 2026-10-06 (v0.15.1)
- Увеличена суша: 1308 сухопутных и 740 морских провинций; размер карты и общее число провинций сохранены.
- Исправлен заголовок палитры `rivers.bmp`, координаты stack/weather/buildings теперь совпадают с координатами карты.
- Все прибрежные провинции получили naval-base spawn и стартовую базу; удалены визуальные записи infrastructure без игровых моделей.
- Исправлены синтаксис пограничного решения и wargoal, эффект найма персонажей, а также BOM трёх файлов локализации.
- Исправлена генерация рельефа на пикселях провинций у границы карты.

## Patch — v0.15.2
- Удалён недопустимый tech ID `artillery` из стартовых технологий 24 стран; движок сообщал о нём дважды на страну.
- `tools/validate_mod.py` теперь проверяет, что этот ошибочный ID не появится снова в `set_technology`.
