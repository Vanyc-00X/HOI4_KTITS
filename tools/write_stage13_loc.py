# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def append_keys(path: Path, keys: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8-sig")
    missing = {k: v for k, v in keys.items() if f" {k}:" not in text}
    if not missing:
        print(f"{path.name}: nothing to add")
        return
    if not text.endswith("\n"):
        text += "\n"
    for k, v in missing.items():
        text += f' {k}:0 "{v}"\n'
    path.write_text("\ufeff" + text, encoding="utf-8")
    print(f"{path.name}: +{len(missing)}")


flavor = {
    "mk_flavor.1.t": "Блок собран за час",
    "mk_flavor.1.d": "Едва альянс объявлен — телеграммы летят ко всем единомышленникам. В Казуалии идеология сама собирает фракцию.",
    "mk_flavor.1.a": "Двери открыты",
    "mk_flavor.2.t": "Сырьевой сюрприз",
    "mk_flavor.2.d": "Геологи (или просто удачливые чиновники) докладывают о новых залежах. Карта ресурсов снова врёт — в вашу пользу.",
    "mk_flavor.2.a": "Копать глубже",
    "mk_flavor.2.b": "Раздуть новость",
    "mk_flavor.3.t": "Учения у границы",
    "mk_flavor.3.d": "Генштаб предлагает «мирные» манёвры. Соседи уже нервничают.",
    "mk_flavor.3.a": "Тренировать армию",
    "mk_flavor.3.b": "Набрать резерв",
    "mk_flavor.3.c": "Сразу найти повод",
    "mk_flavor.4.t": "Клуб единомышленников",
    "mk_flavor.4.d": "Дипломаты предлагают либо согреть отношения, либо сразу сколотить блок.",
    "mk_flavor.4.a": "Укрепить связи",
    "mk_flavor.4.b": "Создать альянс",
    "mk_flavor.5.t": "Торг на Конгрессе",
    "mk_flavor.5.d": "Голос можно купить, выпросить или просто громко потребовать.",
    "mk_flavor.5.a": "Купить голос",
    "mk_flavor.5.b": "Играть на абсурде",
    "mk_flavor.6.t": "Карта ресурсов оживает",
    "mk_flavor.6.d": "По Казуалии разъехались геологические партии. Сталь, нефть и каучук больше не «везде поровну».",
    "mk_flavor.6.a": "Мир стал тяжелее",
    "mk_flavor.7.t": "Уличный жар",
    "mk_flavor.7.d": "Механика страны зашкаливает — улицы шумят, кабинеты спорят.",
    "mk_flavor.7.a": "Обратить в военный пыл",
    "mk_flavor.7.b": "Заткнуть золотом",
    "mk_flavor.8.t": "Промышленный импульс",
    "mk_flavor.8.d": "Либо новый завод, либо новая скважина. Выбор эпохи.",
    "mk_flavor.8.a": "Строить завод",
    "mk_flavor.8.b": "Копать ресурсы",
}

append_keys(ROOT / "localisation/russian/mk_events_l_russian.yml", flavor)
