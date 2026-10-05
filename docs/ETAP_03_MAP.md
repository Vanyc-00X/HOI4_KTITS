# Этап 3 — Карта «Казуалия»

## Итог
Сгенерирована компактная вымышленная карта XXI века со **всеми 24 государствами** на одном суперконтиненте.

| Параметр | Значение |
|----------|----------|
| Размер | **2048×1024** (world_normal 1024×512) |
| States | **127** (столицы 1–24 сохранены) |
| Land provinces | **620** |
| Sea provinces | **16** |
| Strategic regions | **28** (24 суша + 4 моря) |
| Генератор | `tools/generate_kazualia_map.py` |

## Расположение (макрорегионы)

```
        [СЕВЕР: SVA —— CLB —— ART]
              |         |       |
[СЗ: KMS]—[ZLD]—[VCI CORE]—[NBL]—[СВ: ZNS]
              |    |    |    |
         [MUS] [SOY] [FDP] [DMK]
              |    |    |    |
[З: ISL]—[TRF]—[ZML]—[ISG]—[HRL]—[В: KRZ]
              |              |
         [ADL]          [CRE]—[BTR]
              |              |
        [ЮЗ: ZKR]——[SHF]——[ЮВ: KZS]
```

## States на страну
- Крупные (VCI, KRZ, SHF): **10**
- Средние: **5**
- Малые (KZS, ADL, ZML, ISG): **3**

Столицы = state ID **1–24** (как в Этапе 2).

## Созданные файлы
- `map/provinces.bmp`, `terrain.bmp`, `rivers.bmp`, `heightmap.bmp`, `cities.bmp`, `world_normal.bmp`, `trees.bmp`
- `map/definition.csv`, `default.map`, `continent.txt`, `adjacencies.csv`, `positions.txt`
- `map/unitstacks.txt`, `buildings.txt`, `supply_nodes.txt`, `railways.txt`
- `map/strategicregions/*.txt` × 28
- `map/terrain/*` (материалы + colormap)
- `history/states/*.txt` × 127
- `localisation/russian/mk_states_l_russian.yml`
- `localisation/russian/mk_strategic_regions_l_russian.yml`
- `docs/ETAP_03_MAP_REPORT.md`

## Перегенерация
```
python tools/generate_kazualia_map.py
```
Требует доступ к ванили: `E:\SteamLibrary\steamapps\common\Hearts of Iron IV\map` (палитры).

## Зависимости
- Этап 2 capitals 1–24
- Ванильные state_category (`metropolis`, `city`, `town`, `rural`, …)

## Возможные проблемы
1. **Визуал карты** — procedural colormap/высоты; не арт-финал. Возможны артефакты рек/леса.
2. **Railways** — файл пустой; снабжение через supply_nodes на столицах.
3. **Первый запуск** — смотреть `error.log`; при краше прислать лог.
4. **Кириллический путь мода** — лаунчер может требовать latin junction.
5. Карта **упрощённая** (сетка провинций) — на Этапе 12 можно детализировать берега/ВП.

## Что дальше
Этап 4 — глобальные механики: Температура Абсурда, 24 Голоса, НПТ, Идеологические Альянсы + «Обвинить в ревизионизме».
