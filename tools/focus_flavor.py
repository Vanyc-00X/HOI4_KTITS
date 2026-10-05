# -*- coding: utf-8 -*-
"""Extra focus names and target tree sizes for Stage 13 content expansion."""

# Target lengths after padding (base specs are smaller)
SIZES_BIG = {
    "start": 8, "keep": 11, "a": 11, "b": 11, "c": 11,
    "secret": 9, "eco": 9, "army": 9, "diplo": 9,
}
SIZES_SMALL = {
    "start": 7, "keep": 10, "a": 9, "b": 9, "c": 9,
    "secret": 8, "eco": 8, "army": 8, "diplo": 8,
}

# Shared pools — picked by (tag hash + index) so every country feels different
START_EXTRA = [
    "Свод законов эпохи", "Ночной кабинет", "Карта влияния",
    "Присяга новой эпохи", "Бюро прогнозов", "Первый скандал сезона",
]

ECO_EXTRA = [
    "Сырьевой рывок", "Станки двойного назначения", "Энергомосты",
    "Склады на границе", "Картель поставщиков", "Ночные смены",
    "Импортные чертежи", "Ресурсные концессии", "План четырёх кварталов",
]

ARMY_EXTRA = [
    "Полевой устав абсурда", "Пограничные манёвры", "Корпус добровольцев",
    "Арсеналы второй линии", "Штаб оправданий", "Учения «Сосед рядом»",
    "Доктрина быстрого повода", "Мобилизационный купон", "Фронтовые газеты",
]

DIPLO_EXTRA = [
    "Телеграмма единомышленникам", "Пакт о взаимопонимании", "Культурный десант",
    "Конгрессный торг", "Тихие гарантии", "Клуб идеологий",
    "Обмен атташе", "Доктрина открытых дверей", "Саммит блоков",
]

SECRET_EXTRA = [
    "Чёрный ящик эпохи", "Протокол зазеркалья", "Лаборатория слухов",
    "Код вне закона", "Архив запретных мемов", "Последний пароль",
]

BRANCH_EXTRA = {
    "fascism": [
        "Марш единомыслия", "Чёрные списки", "Культ дисциплины",
        "Орден внутренних дел", "Ячейки протокола", "Право сильного",
        "Военный трибунал века", "Имперская повинность", "Флаг над соседом",
    ],
    "communism": [
        "Красные советы улиц", "Пятилетка лозунгов", "Интернационал дворов",
        "Народный контроль", "Коллективный азарт", "Экспорт революции",
        "Красная логистика", "Комитеты бдительности", "Общий котёл",
    ],
    "democratic": [
        "Дебаты без конца", "Свобода печати (условно)", "Выборы под куполом",
        "Гражданские инициативы", "Прозрачный бюджет", "Мирные миссии",
        "Парламентский компромисс", "Права и процедуры", "Голос меньшинства",
    ],
    "neutrality": [
        "Тихая вертикаль", "Аппарат без шума", "Нейтральный интерес",
        "Серые кабинеты", "Баланс сил", "Технократ у руля",
        "Стабильность любой ценой", "Регламент превыше всего", "Сдержанная сила",
    ],
}


def target_sizes(big: bool) -> dict:
    return dict(SIZES_BIG if big else SIZES_SMALL)


def _pick(pool: list[str], tag: str, sec: str, i: int) -> str:
    h = sum(ord(c) for c in tag + sec) + i * 17
    return pool[h % len(pool)]


def expand_spec(tag: str, spec: dict) -> dict:
    """Return a shallow-copied spec with padded focus name lists."""
    import copy
    s = copy.deepcopy(spec)
    sizes = target_sizes(s["big"])
    for sec, n in sizes.items():
        names = list(s[sec]["names"])
        if sec == "start":
            pool = START_EXTRA
        elif sec == "eco":
            pool = ECO_EXTRA
        elif sec == "army":
            pool = ARMY_EXTRA
        elif sec == "diplo":
            pool = DIPLO_EXTRA
        elif sec == "secret":
            pool = SECRET_EXTRA
        else:
            pool = BRANCH_EXTRA[s[sec]["ideology"]]
        used = set(names)
        k = 0
        while len(names) < n:
            cand = _pick(pool, tag, sec, k)
            # make unique per tree
            label = cand if cand not in used else f"{cand} ({tag})"
            if label in used:
                label = f"{cand} #{k + 1}"
            names.append(label)
            used.add(label)
            k += 1
        s[sec]["names"] = names
    return s
