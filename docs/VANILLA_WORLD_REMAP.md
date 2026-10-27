# Vanilla world remap (v0.13.0-vanilla-map)

Кастомная карта Казуалии перенесена в `_archive_custom_map/`.  
Игра использует **ванильную карту мира**. Все сухопутные стейты принадлежат **24 тегам мода** (вариант A).

Фокусные деревья, персонажи, идеи, ивенты и решения **сохранены** на исходных тегах (VCI, SOY, …).

## Жёсткие замены

| MK | Роль | Ванильный слот | Столица |
|----|------|----------------|---------|
| **KRZ** | Коммунизм, Пименов Иоанн | **СССР (SOV)** | 219 Москва |
| **BTR** | Фашизм, Чёрная Тартария | **Третий рейх (GER+AUS+CZE)** | 64 Берлин |
| **CRE** | Фашизм, Чёрная Республика | **Италия + Эфиопия + Албания + Ливия** | 2 Рим |

## Полный мэппинг

| TAG | Идеология | Территория | Столица |
|-----|-----------|------------|---------|
| KRZ | communism | СССР целиком | Moscow 219 |
| BTR | fascism | Германия + Австрия + Чехословакия | Berlin 64 |
| CRE | fascism | Италия + Эфиопия + Албания + Ливия | Rome 2 |
| DMK | fascism | Япония + Маньчжоу-го + Мэнцзян | Tokyo 282 |
| SOY | democratic | США + Филиппины + Либерия | Washington 361 |
| VCI | democratic | Британия + Ирландия (метрополия) | London 126 |
| ZLD | democratic | Франция (метрополия) | Paris 16 |
| ADL | democratic | Бенилюкс | Amsterdam 7 |
| SVA | democratic | Скандинавия (SWE/NOR/DEN/FIN/ICE) | Stockholm 141 |
| KMS | democratic | Британская Индия + Бирма | Delhi 439 |
| ZKR | democratic | Австралия + Новая Зеландия | NSW 285 |
| HRL | democratic | Испания + Португалия (метрополии) | Madrid 41 |
| MUS | neutrality | Китай + варлорды + Тибет | Beijing 608 |
| KZS | neutrality | Польша + Прибалтика + Румыния + Венгрия | Warsaw 10 |
| ISL | neutrality | Исламский пояс + Магриб + мандаты Бл. Востока | Ankara 49 |
| CLB | neutrality | Канада | Ottawa 276 |
| FDP | neutrality | Балканы + Швейцария | Belgrade 107 |
| ART | neutrality | Южный конус (ARG/CHL/URG/PAR) | Buenos Aires 278 |
| NBL | neutrality | Бразилия + Андский север | Rio 500 |
| TRF | communism | Мексика + ЦА + Карибы | Mexico 277 |
| ZML | communism | Монголия + Тува + Синьцзян + Яньань/PRC | Yan'an 622 |
| ISG | communism | Сиам + Малайя + Индокитай | Bangkok 1076 |
| SHF | neutrality | Голландская Ост-Индия | Java 335 |
| ZNS | neutrality | Африка южнее Сахары (бывшие колонии + SAF) | Transvaal 275 |

## Технические изменения

- Убран `replace_path="map/strategicregions"` — грузится ванильная карта
- `history/states` — копия ванили с `owner`/`add_core_of` на MK-теги
- Удалены строки `transfer_state_to` (DLC-релизаблы), чтобы стейты не уходили на стабы
- Скрипт: `tools/remap_to_vanilla_world.ps1`

## Установка

Как раньше: папка мода + `.mod` с `path=`.  
В лаунчере только этот мод. На селекте стран должны быть **VCI / KRZ / CRE / …**, а карта — **мир 1936**, не Казуалия.
