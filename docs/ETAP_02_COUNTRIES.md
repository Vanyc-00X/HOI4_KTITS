# Этап 2 — Базовые данные стран

## Итог
Созданы history, characters, стартовые national ideas, bookmark и RU-локализация для всех **24** государств. Имена лидеров и стартовые идеологии — строго по ТЗ v3.0.

## Стартовые идеологии (маппинг на сабтипы HOI4)

| TAG | Локальная идеология (ТЗ) | ruling_party | ideology subtype |
|-----|--------------------------|--------------|------------------|
| VCI | Казуальное самодержавие | neutrality | despotism |
| SOY | Соевый либерализм | democratic | liberalism |
| BTR | Анархо-фашизм | fascism | fascism_ideology |
| KRZ | Ленинизм | communism | leninism |
| KZS | Православный национализм | neutrality | despotism |
| MUS | Конституционная монархия | democratic | conservatism |
| TRF | Анархо-коммунизм хиппи | communism | anarchist_communism |
| ZLD | Социал-демократия | democratic | socialism |
| ISL | Исламский модернизм | neutrality | moderatism |
| CLB | Технократия | neutrality | oligarchism |
| ADL | Центристский консерватизм | democratic | conservatism |
| DMK | Интегрализм | fascism | falangism |
| FDP | Меритократия | neutrality | oligarchism |
| CRE | Неофашизм | fascism | fascism_ideology |
| SVA | Технодемократия | democratic | liberalism |
| ART | Гражданский национализм | neutrality | centrism |
| KMS | Социальный либерализм | democratic | liberalism |
| ZNS | Пан-регионализм | neutrality | centrism |
| ZKR | Либеральный консерватизм | democratic | conservatism |
| ZML | Коммунальный популизм | communism | marxism |
| NBL | Президентский модернизм | neutrality | oligarchism |
| ISG | Гражданский социализм | communism | marxism |
| HRL | Лигизм | democratic | liberalism |
| SHF | Федеративный консерватизм | neutrality | moderatism |

Метаморфоза: у каждого character есть `country_leader` на все 4 группы идеологий — личность правителя не меняется.

## Столицы (временные state ID → Этап 3)
См. `docs/CAPITAL_STATE_IDS.md` (state 1–24 = столицы TAG по порядку ТЗ).

## Новые ID
### Characters
`VCI_sabirov_marat_ayratovich`, `SOY_efimov_aleksandr_andreevich`, `BTR_akhtyamov_kamil_nailevich`, `KRZ_pimenov_ioann_pavlovich`, `KZS_darya_yuzeeva`, `MUS_musina_alina_maratovna`, `TRF_chazov_georgiy_alekseevich`, `ZLD_sabirova_alfiya_rasilevna`, `ISL_gabdrakhmanov_redik_florovich`, `CLB_ivanov_konstantin_alekseevich`, `ADL_aydov_matvey`, `DMK_sidorov_dmitriy_rustamovich`, `FDP_bagautdinov_bulat_ramilevich`, `CRE_khasanov_damir_yurevich`, `SVA_arifullin_said_askarovich`, `ART_gilmiev_aydar_ayratovich`, `KMS_gilyazov_kamil_ildarovich`, `ZNS_zaynutdinov_artur_ravilevich`, `ZKR_zakirov_ilnar_almazovich`, `ZML_zamaliev_ruslan_ayratovich`, `NBL_iskhanov_bulat_eduardovich`, `ISG_ismagilov_bulat_maratovich`, `HRL_kharitonov_nazar_dmitrievich`, `SHF_sharafutdinov_ranil_ramisovich`

### Ideas
`VCI_kazualnaya_byurokratiya`, `SOY_programmistskiy_klaster`, `BTR_dvoynaya_vlast`, `KRZ_revolyutsionnyy_eksport`, `KZS_kazachiy_krug`, `MUS_korona_i_parlament`, `TRF_kommunalnyy_konsensus`, `ZLD_koalitsionnyy_kapital`, `ISL_indeks_modernizatsii`, `CLB_tekhnokraticheskiy_apparat`, `ADL_diplomaticheskiy_balans`, `DMK_integratsionnyy_kurs`, `FDP_parlamentskie_mandaty`, `CRE_indeks_mobilizatsii`, `SVA_nauchnye_sovety`, `ART_grazhdanskaya_identichnost`, `KMS_set_partnerov`, `ZNS_pan_regionalizm`, `ZKR_kontraktnaya_ekonomika`, `ZML_kommunalnyy_torg`, `NBL_risk_peregreva`, `ISG_kooperativnaya_ustoychivost`, `HRL_liga_ochki`, `SHF_federalnyy_risk`

### Bookmark
`MK_BOOKMARK_*` / файл `common/bookmarks/mk_era_of_mad_rulers.txt`, дата `1936.1.1` (игровой год; лор = Год 0).

## Зависимости
- Этап 1 tags/colors — готовы
- States 1–24 — **ещё нет** (Этап 3); без карты запуск крашится
- Портреты — заглушка `GFX_portrait_unknown`; нужны файлы в `ресурсы\`

## Возможные проблемы
1. Запуск до Этапа 3 невозможен (нет states/map).
2. Портрет-заглушка может дать warning в error.log — норма до Этапа 11.
3. Стартовые OOB: 6 дивизий у крупных, 4 у средних и 2 у малых стран; численность теперь задана в `history/units`.
4. Уникальные механики пока как статичные духи; переменные — Этап 4+.
