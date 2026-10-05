# -*- coding: utf-8 -*-
"""Build per-country content (focus tree, ideas, decisions, events, mechanic, loc) from
tools/country_data_*.py specs.

Usage: python tools/build_countries.py            # every spec found
       python tools/build_countries.py VCI SOY    # selected tags
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

# Stage 11 cosmetics + Stage 13 focus expansion
sys.path.insert(0, str(TOOLS))
from country_cosmetics import CHARS, COSMETICS, cosmetic_tag  # noqa: E402
from focus_flavor import expand_spec, target_sizes  # noqa: E402

IDEOLOGY_RU = {"democratic": "демократия", "communism": "коммунизм",
               "fascism": "фашизм", "neutrality": "неприсоединение"}
IDEOLOGY_ICON = {"democratic": "GFX_goal_support_democracy", "communism": "GFX_goal_support_communism",
                 "fascism": "GFX_goal_support_fascism", "neutrality": "GFX_goal_generic_neutrality_focus"}
IDEOLOGY_PICTURE = {"democratic": "generic_democratic_drift_bonus", "communism": "generic_communism_drift_bonus",
                    "fascism": "generic_fascism_drift_bonus", "neutrality": "generic_neutrality_drift_bonus"}
IDEOLOGY_MODS = {
    "democratic": {"stability_factor": 0.04, "political_power_factor": 0.05, "research_speed_factor": 0.03,
                   "democratic_drift": 0.03},
    "communism": {"industrial_capacity_factory": 0.04, "production_speed_buildings_factor": 0.08,
                  "conscription_factor": 0.01, "communism_drift": 0.03},
    "fascism": {"war_support_factor": 0.06, "army_org_factor": 0.03, "conscription_factor": 0.015,
                "fascism_drift": 0.03},
    "neutrality": {"political_power_gain": 0.1, "stability_factor": 0.04,
                   "production_speed_buildings_factor": 0.05, "neutrality_drift": 0.03},
}
IDEOLOGY_TECH = {"democratic": "electronics", "communism": "industry",
                 "fascism": "infantry_weapons", "neutrality": "construction_tech"}
IDEOLOGY_FACTORY = {"democratic": "industrial_complex", "communism": "arms_factory",
                    "fascism": "arms_factory", "neutrality": "industrial_complex"}
POLITICAL = ("keep", "a", "b", "c")
TECH_LABELS = {
    "keep_tech": "Исследования курса", "a_tech": "Исследования курса", "b_tech": "Исследования курса",
    "c_tech": "Исследования курса", "secret_tech": "Секретные разработки",
    "secret_ev_tech": "Засекреченные разработки", "eco_tech": "Промышленные исследования",
    "eco2_tech": "Вторая волна индустрии", "eco_ev_tech": "Инженерные бюро",
    "build_tech": "Строительные технологии",
    "inf_tech": "Стрелковое оружие", "art_tech": "Артиллерия", "doc_bonus": "Сухопутная доктрина",
}
SECTION_BASE_X = {"eco": 1, "army": 5, "diplo": 9, "keep": 13, "a": 17, "b": 21, "c": 25, "secret": 29, "absurd": 33}
SECTION_ICONS = {
    "start": ["GFX_goal_generic_national_unity", "GFX_goal_generic_political_pressure",
              "GFX_goal_generic_scientific_exchange", "GFX_goal_generic_construct_infrastructure",
              "GFX_goal_generic_propaganda", "GFX_goal_generic_dangerous_deal"],
    "eco": ["GFX_goal_generic_construct_civ_factory", "GFX_goal_generic_production",
            "GFX_goal_generic_construct_infrastructure", "GFX_goal_generic_construct_mil_factory",
            "GFX_goal_generic_consumer_goods", "GFX_goal_generic_production2"],
    "army": ["GFX_goal_generic_allies_build_infantry", "GFX_goal_generic_small_arms",
             "GFX_goal_generic_army_doctrines", "GFX_goal_generic_position_armies",
             "GFX_goal_generic_army_artillery", "GFX_goal_generic_special_forces"],
    "diplo": ["GFX_goal_generic_improve_relations", "GFX_goal_generic_alliance",
              "GFX_goal_generic_positive_trade_relations", "GFX_goal_generic_trade",
              "GFX_goal_generic_major_alliance", "GFX_goal_generic_forceful_treaty"],
    "secret": ["GFX_goal_generic_secret_weapon", "GFX_goal_generic_radar", "GFX_goal_generic_dangerous_deal",
               "GFX_goal_generic_scientific_exchange", "GFX_goal_generic_wolf_pack",
               "GFX_goal_generic_more_territorial_claims"],
    "branch": ["GFX_goal_generic_propaganda", "GFX_goal_generic_political_pressure",
               "GFX_goal_generic_national_unity", "GFX_goal_generic_scientific_exchange",
               "GFX_goal_generic_trade", "GFX_goal_generic_construct_civ_factory",
               "GFX_goal_generic_military_sphere"],
}


# ---------------------------------------------------------------- helpers
def ind(text: str, n: int) -> str:
    pad = "\t" * n
    return "\n".join(pad + l if l.strip() else l for l in text.strip("\n").splitlines())


def fmt_mods(mods: dict) -> str:
    return "\n".join(f"{k} = {v:g}" if isinstance(v, float) else f"{k} = {v}" for k, v in mods.items())


def mech(delta: int) -> str:
    if delta >= 0:
        return f"set_temp_variable = {{ mk_mech_delta = {delta} }}\nmk_mech_add = yes"
    return f"set_temp_variable = {{ mk_mech_delta = {-delta} }}\nmk_mech_sub = yes"


def absurd(delta: int) -> str:
    if delta >= 0:
        return f"set_temp_variable = {{ mk_absurd_delta = {delta} }}\nmk_add_absurd = yes"
    return f"set_temp_variable = {{ mk_absurd_delta = {-delta} }}\nmk_sub_absurd = yes"


def votes(n: int) -> str:
    return f"set_temp_variable = {{ mk_votes_delta = {n} }}\nmk_grant_votes = yes"


def npt(n: int) -> str:
    """NPT only works for fascist governments (Stage 11)."""
    return (
        f"if = {{\n\tlimit = {{ has_government = fascism }}\n"
        f"\tset_temp_variable = {{ mk_npt_delta = {n} }}\n\tmk_add_npt = yes\n}}"
    )


def npt_fascist_branch(n: int) -> str:
    """Unconditional NPT grant for focuses on a fascist political branch."""
    return f"set_temp_variable = {{ mk_npt_delta = {n} }}\nmk_add_npt = yes"


def tech(cat: str, name: str) -> str:
    return f"add_tech_bonus = {{\n\tname = {name}\n\tbonus = 1.0\n\tuses = 1\n\tcategory = {cat}\n}}"


def build(where: str, btype: str, level: int = 1) -> str:
    slot = "add_extra_state_shared_building_slots = 1\n" if btype != "infrastructure" else ""
    return (f"{where} = {{\n" + ind(slot + f"add_building_construction = {{ type = {btype} level = {level} "
                                    f"instant_build = yes }}", 1) + "\n}")


def popularity(ideo: str, value: float) -> str:
    return f"add_popularity = {{ ideology = {ideo} popularity = {value:g} }}"


def set_ruling(ideo: str) -> str:
    elections = "yes" if ideo == "democratic" else "no"
    return f"set_politics = {{ ruling_party = {ideo} elections_allowed = {elections} }}"


# ---------------------------------------------------------------- generator
class Country:
    def __init__(self, tag: str, spec: dict):
        self.tag, self.s = tag, spec
        self.ns = f"mk_{tag.lower()}"
        self.loc: list[tuple[str, str]] = []
        self.big = spec["big"]

    def L(self, key: str, value: str) -> None:
        self.loc.append((key, value))

    def ev(self, n: int) -> str:
        return f"{self.ns}.{n}"

    # ---------- ideas
    def ideas(self) -> str:
        t, s = self.tag, self.s
        out = []
        m = s["mech"]
        for lvl, (name, desc), mods in zip(("low", "mid", "high"), m["tiers"], m["tier_mods"]):
            key = f"{t}_mech_{lvl}"
            self.L(key, name)
            self.L(key + "_desc", desc)
            out.append(self.idea(key, m.get("picture", "generic_pp_unity_bonus"), mods))
        for br in POLITICAL:
            b = s[br]
            base = dict(IDEOLOGY_MODS[b["ideology"]])
            base.update(b.get("mods", {}))
            for lvl, mult in (("", 1.0), ("_2", 2.0)):
                key = f"{t}_sp_{br}{lvl}"
                self.L(key, b["spirit"][0] + (": апогей" if lvl else ""))
                self.L(key + "_desc", b["spirit"][1])
                out.append(self.idea(key, IDEOLOGY_PICTURE[b["ideology"]],
                                     {k: round(v * mult, 3) for k, v in base.items()}))
        sec = s["secret"]
        self.L(f"{t}_sp_secret", sec["spirit"][0])
        self.L(f"{t}_sp_secret_desc", sec["spirit"][1])
        out.append(self.idea(f"{t}_sp_secret", "generic_research_bonus", sec.get("mods", {
            "research_speed_factor": 0.07, "political_power_factor": 0.1, "war_support_factor": 0.05})))
        return "ideas = {\n\tcountry = {\n" + "\n\n".join(ind(x, 2) for x in out) + "\n\t}\n}\n"

    @staticmethod
    def idea(key: str, picture: str, mods: dict) -> str:
        return (f"{key} = {{\n\tpicture = {picture}\n\tallowed = {{ always = no }}\n\tremoval_cost = -1\n"
                f"\tmodifier = {{\n{ind(fmt_mods(mods), 2)}\n\t}}\n}}")

    # ---------- focus tree
    def focus_tree(self) -> str:
        t, s = self.tag, self.s
        self.L(f"{t}_focus", s["tree_name"])
        focuses: list[str] = []
        start_n = len(s["start"]["names"])
        start_ids = [f"{t}_start_{i:02d}" for i in range(start_n)]
        start_pos = [(15, 0), (13, 1), (17, 1), (13, 2), (17, 2), (15, 3), (13, 4), (17, 4)][:start_n]
        start_pre = [[], [0], [0], [1], [2], [3, 4], [5], [5]][:start_n]
        for i, fid in enumerate(start_ids):
            x, y = start_pos[i]
            pre = [[start_ids[p]] for p in start_pre[i]]
            icon = SECTION_ICONS["start"][i % len(SECTION_ICONS["start"])]
            focuses.append(self.focus(fid, s["start"]["names"][i], s["start"]["desc"], icon,
                                      x, y, pre, self.start_reward(i, start_n), filters="FOCUS_FILTER_POLITICAL",
                                      ai=8 if i == 0 else 5))
        gate = start_ids[-1]
        y0 = start_pos[-1][1] + 2
        heads = {br: f"{t}_{br}_00" for br in POLITICAL}
        for sec in ("eco", "army", "diplo", "keep", "a", "b", "c", "secret", "absurd"):
            data = s[sec]
            n = len(data["names"])
            ids = [f"{t}_{sec}_{i:02d}" for i in range(n)]
            base = SECTION_BASE_X[sec]
            col_last = {0: ids[0], 1: ids[0]}
            max_row = 0
            for i, fid in enumerate(ids):
                extra = {}
                if i == 0:
                    x, y = base, y0
                    pre = [[start_ids[1]]] if sec in ("eco", "army", "diplo", "absurd") else [[gate]]
                elif i < n - 1:
                    col, row = (i - 1) % 2, (i - 1) // 2 + 1
                    x, y = (base - 1 if col == 0 else base + 1), y0 + row
                    pre = [[ids[i - 2] if i >= 3 else ids[0]]]
                    col_last[col] = fid
                    max_row = max(max_row, row)
                else:
                    x, y = base, y0 + max_row + 1
                    pre = [[col_last[0]], [col_last[1]]]
                if sec in POLITICAL:
                    icon = IDEOLOGY_ICON[data["ideology"]] if i in (0, n - 1) else \
                        SECTION_ICONS["branch"][(i - 1) % len(SECTION_ICONS["branch"])]
                    reward = self.branch_reward(sec, i, n)
                    if i == 0:
                        extra["mutually_exclusive"] = [heads[o] for o in POLITICAL if o != sec]
                        if sec != "keep":
                            extra["available"] = "mk_great_turn_unlocked = yes"
                        # AI prefers keep historically; radicals get weight after Great Turn
                        extra["ai"] = 10 if sec == "keep" else 3
                    else:
                        extra["ai"] = 4
                    filt = "FOCUS_FILTER_POLITICAL"
                elif sec == "secret":
                    icon = SECTION_ICONS["secret"][i % 6]
                    reward = self.secret_reward(i, n)
                    if i == 0:
                        extra["available"] = data["cond"]
                        extra["ai"] = 2
                    else:
                        extra["ai"] = 3
                    filt = "FOCUS_FILTER_POLITICAL"
                elif sec == "absurd":
                    icon = SECTION_ICONS["diplo"][i % 6]
                    reward = self.absurd_reward(i, n)
                    filt = "FOCUS_FILTER_POLITICAL"
                    extra["ai"] = 7 if i not in (2, 7) else 4
                else:
                    icon = SECTION_ICONS[sec][i % 6]
                    reward = getattr(self, f"{sec}_reward")(i, n)
                    filt = {"eco": "FOCUS_FILTER_INDUSTRY", "army": "FOCUS_FILTER_ARMY_XP",
                            "diplo": "FOCUS_FILTER_POLITICAL"}[sec]
                    extra["ai"] = {"eco": 7, "army": 6, "diplo": 8}[sec]
                name = data["names"][i]
                # NPT only for fascist branches / fascist government (Stage 11)
                if "НПТ" in name:
                    if sec in POLITICAL and data.get("ideology") == "fascism":
                        reward += "\n" + npt_fascist_branch(2)
                    elif sec == "secret":
                        reward += "\n" + npt(2)
                    elif sec in POLITICAL:
                        pass  # non-fascist political focuses never grant NPT
                    else:
                        reward += "\n" + npt(1)
                desc = data["desc"]
                focuses.append(self.focus(fid, name, desc, icon, x, y, pre, reward, filters=filt, **extra))
        body = "\n\n".join(ind(f, 1) for f in focuses)
        return (f"focus_tree = {{\n\tid = {t}_focus\n\tcountry = {{\n\t\tfactor = 0\n\t\tmodifier = {{\n"
                f"\t\t\tadd = 10\n\t\t\toriginal_tag = {t}\n\t\t}}\n\t}}\n\tdefault = no\n"
                f"\treset_on_civilwar = no\n\n\tinitial_show_position = {{ focus = {start_ids[0]} }}\n\n"
                f"{body}\n}}\n")

    def focus(self, fid, name, desc, icon, x, y, prereqs, reward, filters, mutually_exclusive=None,
              available=None, ai=None) -> str:
        self.L(fid, name)
        self.L(fid + "_desc", desc)
        lines = [f"id = {fid}", f"icon = {icon}", f"x = {x}", f"y = {y}", "cost = 3"]
        for group in prereqs:
            lines.append("prerequisite = { " + " ".join(f"focus = {p}" for p in group) + " }")
        if mutually_exclusive:
            lines.append("mutually_exclusive = { " + " ".join(f"focus = {m}" for m in mutually_exclusive) + " }")
        if available:
            lines.append(f"available = {{\n{ind(available, 1)}\n}}")
        lines.append(f"search_filters = {{ {filters} }}")
        if ai is not None:
            lines.append(f"ai_will_do = {{\n\tfactor = {ai}\n\tmodifier = {{\n\t\tfactor = 2\n"
                         f"\t\tmk_absurd_high = yes\n\t}}\n}}")
        lines.append(f"completion_reward = {{\n{ind(reward, 1)}\n}}")
        return "focus = {\n" + ind("\n".join(lines), 1) + "\n}"

    # ---------- rewards
    def start_reward(self, i, n):
        t = self.tag
        table = [
            f"add_political_power = 75\ncountry_event = {{ id = {self.ev(1)} days = 1 }}",
            mech(10) + "\n" + votes(1),
            "add_research_slot = 1",
            build("capital_scope", "infrastructure") + "\n" + build("capital_scope", "industrial_complex"),
            "add_stability = 0.05\nadd_war_support = 0.03",
            (f"add_political_power = 50\n{mech(5)}\nset_country_flag = {t}_start_done\n"
             "add_stability = 0.03"),
            "add_political_power = 40\n" + absurd(2) + f"\ncountry_event = {{ id = {self.ev(15)} days = 2 }}",
            build("random_owned_controlled_state", "infrastructure") + "\nadd_manpower = 5000",
        ]
        return table[i] if i < len(table) else table[-1]

    def apply_course_cosmetic(self, ideo: str) -> str:
        """Rename country + leader when the political course is chosen."""
        t = self.tag
        ctag = cosmetic_tag(t, ideo)
        country, adj, leader = COSMETICS[t][ideo]
        self.L(ctag, country)
        self.L(ctag + "_DEF", country)
        self.L(ctag + "_ADJ", adj)
        lkey = f"{t}_leader_{ideo}"
        self.L(lkey, leader)
        self.L(f"{t}_tt_course_{ideo}",
               f"Страна становится: §Y{country}§!\\nЛидер: §Y{leader}§!")
        char = CHARS[t]
        return (
            "drop_cosmetic_tag = yes\n"
            f"set_cosmetic_tag = {ctag}\n"
            f"set_character_name = {{\n\tcharacter = {char}\n\tname = {lkey}\n}}\n"
            f"custom_effect_tooltip = {t}_tt_course_{ideo}"
        )

    def branch_reward(self, br, i, n):
        t, b = self.tag, self.s[br]
        ideo = b["ideology"]
        sign = b.get("mech_sign", 1)
        if i == 0:
            parts = []
            if br != "keep" or ideo != self.s["start_ideology"]:
                parts.append(set_ruling(ideo))
            parts.append(self.apply_course_cosmetic(ideo))
            parts += [popularity(ideo, 0.2), f"add_ideas = {t}_sp_{br}", f"set_country_flag = {t}_branch_{br}",
                      f"country_event = {{ id = {self.ev(2 + POLITICAL.index(br))} days = 1 }}",
                      absurd(2 if br == "keep" else 6)]
            if br == "keep":
                parts.append("add_stability = 0.05")
            if ideo == "fascism":
                parts.append(npt_fascist_branch(1))
            return "\n".join(parts)
        if i == n - 1:
            finale = (
                f"swap_ideas = {{ remove_idea = {t}_sp_{br} add_idea = {t}_sp_{br}_2 }}\n"
                "if = {\n\tlimit = { is_in_faction = no }\n\tmk_form_ideology_faction_effect = yes\n}\n"
            )
            if ideo == "fascism":
                finale += (
                    "random_neighbor_country = {\n"
                    "\tlimit = { is_mk_country = yes NOT = { is_in_faction_with = ROOT } }\n"
                    "\tROOT = { create_wargoal = { type = puppet_wargoal_focus target = PREV } }\n}\n"
                    + npt_fascist_branch(2) + "\n"
                )
            elif ideo == "communism":
                finale += (
                    "every_other_country = {\n"
                    "\tlimit = { is_mk_country = yes has_government = communism NOT = { tag = ROOT } }\n"
                    "\tadd_opinion_modifier = { target = ROOT modifier = mk_ideological_kin }\n}\n"
                )
            elif ideo == "democratic":
                finale += votes(2) + "\n"
            else:
                finale += "add_stability = 0.05\n"
            return finale + absurd(3 if br == "keep" else 5)
        slot = (i - 1) % 9
        wargoal = (
            "random_neighbor_country = {\n"
            "\tlimit = { is_mk_country = yes NOT = { is_in_faction_with = ROOT } has_war = no }\n"
            "\tROOT = { create_wargoal = { type = topple_government target = PREV } }\n}"
        )
        puppet_cb = (
            "random_neighbor_country = {\n"
            "\tlimit = { is_mk_country = yes NOT = { is_in_faction_with = ROOT } has_war = no }\n"
            "\tROOT = { create_wargoal = { type = puppet_wargoal_focus target = PREV } }\n}"
        )
        invite_all = (
            "if = {\n\tlimit = { is_faction_leader = yes has_war = no }\n"
            "\tevery_other_country = {\n"
            "\t\tlimit = { is_mk_country = yes has_government = ROOT is_in_faction = no "
            "is_subject = no has_war = no }\n"
            "\t\tROOT = { add_to_faction = PREV }\n"
            "\t\tadd_ideas = mk_idea_faction_member\n"
            "\t}\n"
            f"\tcountry_event = {{ id = {self.ev(14)} days = 1 }}\n"
            "}"
        )
        resource_grab = (
            "random_owned_controlled_state = {\n"
            "\tadd_resource = { type = steel amount = 8 }\n"
            "\tadd_resource = { type = oil amount = 4 }\n}"
        )
        table = {
            "fascism": [
                popularity(ideo, 0.1) + "\nadd_war_support = 0.05",
                mech(10 * sign) + "\n" + npt_fascist_branch(1),
                wargoal + "\n" + absurd(4),
                tech(IDEOLOGY_TECH[ideo], f"{t}_{br}_tech"),
                "add_manpower = 15000\nadd_war_support = 0.05",
                build("random_owned_controlled_state", "arms_factory"),
                puppet_cb + "\n" + npt_fascist_branch(1),
                resource_grab + "\nadd_war_support = 0.03",
                invite_all + "\n" + absurd(3),
            ],
            "communism": [
                popularity(ideo, 0.12) + "\nadd_political_power = 40",
                mech(10 * sign),
                invite_all,
                tech(IDEOLOGY_TECH[ideo], f"{t}_{br}_tech"),
                build("random_owned_controlled_state", "industrial_complex"),
                "add_stability = -0.02\nadd_war_support = 0.06\n" + absurd(3),
                "every_neighbor_country = {\n\tlimit = { is_mk_country = yes }\n"
                "\tadd_popularity = { ideology = communism popularity = 0.03 }\n}",
                resource_grab + "\n" + mech(5 * sign),
                wargoal + f"\ncountry_event = {{ id = {self.ev(16)} days = 1 }}",
            ],
            "democratic": [
                popularity(ideo, 0.1) + "\nadd_stability = 0.04",
                mech(10 * sign),
                votes(1) + "\nadd_political_power = 50",
                tech(IDEOLOGY_TECH[ideo], f"{t}_{br}_tech"),
                invite_all,
                "every_other_country = {\n\tlimit = { is_mk_country = yes }\n"
                "\tadd_opinion_modifier = { target = ROOT modifier = mk_kazual_goodwill }\n}",
                "add_stability = 0.03\n" + votes(1),
                resource_grab + "\nadd_political_power = 30",
                ("random_other_country = {\n"
                 "\tlimit = { is_mk_country = yes has_government = democratic NOT = { tag = ROOT } has_war = no }\n"
                 "\tROOT = { give_guarantee = PREV }\n}"),
            ],
            "neutrality": [
                popularity(ideo, 0.1) + "\nadd_political_power = 60",
                mech(10 * sign),
                "add_stability = 0.05",
                tech(IDEOLOGY_TECH[ideo], f"{t}_{br}_tech"),
                build("random_owned_controlled_state", "infrastructure", 2),
                votes(1) + "\nadd_political_power = 40",
                invite_all,
                resource_grab + "\nadd_stability = 0.02",
                "add_political_power = 80\n" + absurd(1) + f"\ncountry_event = {{ id = {self.ev(17)} days = 1 }}",
            ],
        }
        return table[ideo][slot]

    def absurd_reward(self, i, n):
        """Country-specific absurd-diplomacy branch: industry, CBs, guarantees, votes and blocs."""
        t = self.tag
        if i == 0:
            return (build("capital_scope", "industrial_complex") + "\n"
                    + build("capital_scope", "infrastructure") + "\n"
                    + "add_political_power = 40\nadd_stability = 0.03")
        if i == 1:
            return (build("random_owned_controlled_state", "industrial_complex") + "\n"
                    "random_owned_controlled_state = {\n"
                    "\tadd_resource = { type = steel amount = 8 }\n"
                    "\tadd_resource = { type = oil amount = 4 }\n}\n"
                    "add_research_slot = 1")
        if i == 2:
            return (
                "random_other_country = {\n"
                "\tlimit = { is_mk_country = yes is_subject = no NOT = { is_in_faction_with = ROOT } }\n"
                "\tROOT = { create_wargoal = { type = topple_government target = PREV } }\n}\n"
                "add_war_support = 0.06\n" + absurd(4)
            )
        if i == 3:
            return (
                "random_neighbor_country = {\n"
                "\tlimit = { is_mk_country = yes is_subject = no has_war = no }\n"
                "\tadd_opinion_modifier = { target = ROOT modifier = mk_kazual_goodwill }\n"
                "\tROOT = { give_guarantee = PREV }\n}\n"
                "add_political_power = 35\nadd_stability = 0.03"
            )
        if i == 4:
            return votes(2) + "\nadd_political_power = 50\nadd_stability = 0.02"
        if i == 5:
            return (
                "if = {\n\tlimit = { is_in_faction = no }\n"
                "\tmk_form_ideology_faction_effect = yes\n}\n"
                "else_if = {\n\tlimit = { is_faction_leader = yes }\n"
                "\tevery_other_country = {\n"
                "\t\tlimit = { is_mk_country = yes has_government = ROOT is_in_faction = no "
                "is_subject = no has_war = no }\n"
                "\t\tROOT = { add_to_faction = PREV }\n"
                "\t\tadd_ideas = mk_idea_faction_member\n"
                "\t}\n}\n"
                "else = { every_other_country = { limit = { is_mk_country = yes } "
                "add_opinion_modifier = { target = ROOT modifier = mk_ideological_kin } } }"
            )
        if i == 6:
            return (
                "random_other_country = {\n"
                "\tlimit = { is_mk_country = yes is_subject = no "
                "check_variable = { mk_misconduct > 0 } "
                "NOT = { tag = ROOT } NOT = { is_in_faction_with = ROOT } "
                "NOT = { has_war_with = ROOT } }\n"
                "\tROOT = { create_wargoal = { type = topple_government target = PREV } }\n}\n"
                + votes(1) + "\nadd_war_support = 0.05"
            )
        return (
            "every_other_country = {\n"
            "\tlimit = { is_mk_country = yes is_subject = no has_war = no }\n"
            "\tROOT = { give_guarantee = PREV }\n"
            "\tadd_opinion_modifier = { target = ROOT modifier = mk_kazual_goodwill }\n}\n"
            "add_ideas = mk_idea_collective_security\n"
            "add_political_power = 100\nadd_stability = 0.05\n"
            + votes(2) + "\n" + absurd(3)
        )

    def secret_reward(self, i, n):
        t = self.tag
        if i == 0:
            return (f"set_country_flag = {t}_secret\ncountry_event = {{ id = {self.ev(6)} days = 1 }}\n"
                    + npt(2) + "\n" + absurd(5))
        if i == n - 1:
            return (f"add_ideas = {t}_sp_secret\nadd_war_support = 0.1\n{npt(2)}\n{absurd(8)}\n"
                    f"news_event = {{ id = {self.ev(13)} hours = 6 }}")
        mid = [
            npt(1) + "\n" + tech("electronics", f"{t}_secret_tech"),
            mech(15),
            "add_political_power = 100\n" + votes(1),
            "add_research_slot = 1",
            absurd(4) + "\nadd_war_support = 0.05",
            "random_owned_controlled_state = {\n\tadd_resource = { type = aluminium amount = 6 }\n"
            "\tadd_resource = { type = tungsten amount = 4 }\n}",
            f"country_event = {{ id = {self.ev(18)} days = 1 }}\n" + mech(10),
        ]
        return mid[(i - 1) % len(mid)]

    def eco_reward(self, i, n):
        t = self.tag
        if i == n - 1:
            return (build("capital_scope", "industrial_complex", 2) +
                    f"\ncountry_event = {{ id = {self.ev(10)} days = 1 }}\n"
                    "random_owned_controlled_state = {\n\tadd_resource = { type = steel amount = 10 }\n}")
        return [
            build("capital_scope", "industrial_complex"),
            tech("industry", f"{t}_eco_tech"),
            build("random_owned_controlled_state", "infrastructure", 2),
            build("random_owned_controlled_state", "arms_factory"),
            tech("construction_tech", f"{t}_build_tech"),
            "random_owned_controlled_state = {\n\tadd_resource = { type = oil amount = 6 }\n"
            "\tadd_resource = { type = rubber amount = 4 }\n}",
            build("random_owned_controlled_state", "industrial_complex") + "\nadd_political_power = 25",
            tech("industry", f"{t}_eco2_tech") + "\n" + mech(5),
        ][i % 8]

    def army_reward(self, i, n):
        t = self.tag
        if i == n - 1:
            return (
                "army_experience = 25\n"
                "random_neighbor_country = {\n"
                "\tlimit = { is_mk_country = yes NOT = { is_in_faction_with = ROOT } }\n"
                "\tROOT = { create_wargoal = { type = topple_government target = PREV } }\n}\n"
                f"country_event = {{ id = {self.ev(11)} days = 1 }}\n"
                + absurd(4)
            )
        justify = (
            "random_neighbor_country = {\n"
            "\tlimit = { is_mk_country = yes NOT = { is_in_faction_with = ROOT } has_war = no }\n"
            "\tROOT = {\n"
            "\t\tcreate_wargoal = { type = puppet_wargoal_focus target = PREV }\n"
            "\t\tadd_war_support = 0.03\n"
            "\t}\n}"
        )
        return [
            "army_experience = 15\nadd_manpower = 5000",
            tech("infantry_weapons", f"{t}_inf_tech"),
            f"add_doctrine_cost_reduction = {{\n\tname = {t}_doc_bonus\n\tcost_reduction = 0.5\n\tuses = 1\n"
            "\tcategory = land_doctrine\n}",
            justify + "\n" + absurd(3),
            tech("artillery", f"{t}_art_tech"),
            "add_manpower = 12000\narmy_experience = 10\nadd_war_support = 0.04",
            build("random_owned_controlled_state", "arms_factory") + "\n" + absurd(2),
            f"country_event = {{ id = {self.ev(16)} days = 1 }}\n" + justify,
        ][i % 8]

    def diplo_reward(self, i, n):
        t = self.tag
        if i == n - 1:
            return (
                votes(2) + "\n"
                "if = {\n\tlimit = { is_in_faction = no }\n\tmk_form_ideology_faction_effect = yes\n}\n"
                f"country_event = {{ id = {self.ev(12)} days = 1 }}"
            )
        kin = ("every_other_country = {\n\tlimit = { is_mk_country = yes has_government = ROOT }\n"
               "\tadd_opinion_modifier = { target = ROOT modifier = mk_ideological_kin }\n"
               "\treverse_add_opinion_modifier = { target = ROOT modifier = mk_ideological_kin }\n}")
        goodwill = ("every_other_country = {\n\tlimit = { is_mk_country = yes }\n"
                    "\tadd_opinion_modifier = { target = ROOT modifier = mk_kazual_goodwill }\n}")
        invite_all = (
            "if = {\n\tlimit = { is_faction_leader = yes has_war = no }\n"
            "\tevery_other_country = {\n"
            "\t\tlimit = { is_mk_country = yes has_government = ROOT is_in_faction = no "
            "is_subject = no has_war = no }\n"
            "\t\tROOT = { add_to_faction = PREV }\n"
            "\t\tadd_ideas = mk_idea_faction_member\n"
            "\t}\n"
            f"\tcountry_event = {{ id = {self.ev(14)} days = 1 }}\n"
            "}"
        )
        guarantee = (
            "random_other_country = {\n"
            "\tlimit = { is_mk_country = yes has_government = ROOT NOT = { tag = ROOT } has_war = no }\n"
            "\tROOT = { give_guarantee = PREV }\n"
            "\tadd_opinion_modifier = { target = ROOT modifier = mk_ideological_kin }\n}"
        )
        form_bloc = (
            "if = {\n\tlimit = { is_in_faction = no has_war = no }\n"
            "\tmk_form_ideology_faction_effect = yes\n}"
        )
        return [
            votes(1), kin, invite_all, votes(1) + "\nadd_stability = 0.03", goodwill, guarantee,
            form_bloc + "\n" + absurd(2),
            f"country_event = {{ id = {self.ev(19)} days = 1 }}\n" + kin,
        ][i % 8]

    # ---------- decisions
    def decisions(self) -> tuple[str, str]:
        t, s, m = self.tag, self.s, self.s["mech"]
        self.L(f"mk_cat_{t}", m["name"])
        self.L(f"mk_cat_{t}_desc", f"{m['desc']}\\n\\n§Y{m['name']}:§! [?mk_mech|0] / 100")
        self.L(f"{t}_mech_up_tt", f"{m['name']} §Gрастёт§!")
        self.L(f"{t}_mech_down_tt", f"{m['name']} §Rснижается§!")
        cat = (f"mk_cat_{t} = {{\n\ticon = {m.get('cat_icon', 'GFX_decision_category_generic_political_actions')}\n"
               f"\tpriority = 110\n\tallowed = {{ original_tag = {t} }}\n\tvisible = {{ tag = {t} }}\n}}\n")
        decs = []
        d = m["decisions"]

        def dec(key, name, desc, icon, cost, body, visible="", available="", reenable=30, ai=1):
            self.L(key, name)
            self.L(key + "_desc", desc)
            parts = [f"icon = {icon}", f"cost = {cost}", "fire_only_once = no", f"days_re_enable = {reenable}"]
            if visible:
                parts.append(f"visible = {{\n{ind(visible, 1)}\n}}")
            parts.append(f"available = {{\n{ind(f'has_political_power > {cost - 1}' + chr(10) + available, 1)}\n}}")
            parts.append(f"complete_effect = {{\n{ind(body, 1)}\n}}")
            parts.append(f"ai_will_do = {{ factor = {ai} }}")
            decs.append(f"{key} = {{\n{ind(chr(10).join(parts), 1)}\n}}")

        dec(f"{t}_dec_raise", *d["raise"], "generic_political_discourse", 25,
            mech(10) + f"\ncustom_effect_tooltip = {t}_mech_up_tt\nadd_stability = -0.01",
            available="check_variable = { mk_mech < 95 }")
        dec(f"{t}_dec_lower", *d["lower"], "generic_civil_support", 25,
            mech(-10) + f"\ncustom_effect_tooltip = {t}_mech_down_tt\nadd_stability = 0.02",
            available="check_variable = { mk_mech > 5 }")
        exploit_extra = m.get("exploit_extra", "")
        dec(f"{t}_dec_exploit", *d["exploit"], "generic_industry", 50,
            mech(-30) + f"\ncountry_event = {{ id = {self.ev(7)} days = 1 }}"
            + ("\n" + exploit_extra.strip() if exploit_extra else ""),
            available="check_variable = { mk_mech > 69 }\n" + m.get("exploit_available", ""),
            reenable=90, ai=2)
        dec(f"{t}_dec_crisis", *d["crisis"], "generic_break_treaty", 40,
            mech(20) + "\nadd_stability = -0.02", visible="check_variable = { mk_mech < 20 }", reenable=60, ai=3)
        for br in POLITICAL:
            b = s[br]
            dec(f"{t}_dec_campaign_{br}", f"Кампания: {b['title']}",
                f"Мобилизовать сторонников курса «{b['title']}».", "generic_nationalism", 30,
                popularity(b["ideology"], 0.05) + "\n" + mech(5 * b.get("mech_sign", 1)),
                visible=f"has_country_flag = {t}_branch_{br}", reenable=60)
        return cat, f"mk_cat_{t} = {{\n\n" + "\n\n".join(ind(x, 1) for x in decs) + "\n}\n"

    # ---------- events
    def events(self) -> str:
        t, s, ev = self.tag, self.s, self.s["events"]
        mname = s["mech"]["name"]
        out = [f"add_namespace = {self.ns}"]

        def event(n, title, desc, options, news=False, picture="GFX_report_event_generic_read_write"):
            key = self.ev(n)
            self.L(key + ".t", title)
            self.L(key + ".d", desc)
            kind = "news_event" if news else "country_event"
            opts = []
            for letter, (oname, body) in zip("abc", options):
                self.L(f"{key}.{letter}", oname)
                opts.append(f"option = {{\n\tname = {key}.{letter}\n{ind(body, 1)}\n}}" if body
                            else f"option = {{\n\tname = {key}.{letter}\n}}")
            extra = "\tmajor = yes\n" if news else ""
            return (f"{kind} = {{\n\tid = {key}\n\ttitle = {key}.t\n\tdesc = {key}.d\n\tpicture = {picture}\n"
                    f"{extra}\tis_triggered_only = yes\n" + "\n".join(ind(o, 1) for o in opts) + "\n}")

        start_ideo = s["start_ideology"]
        intro_opts = [(f"Ставка на «{mname}»", mech(10) + "\n" + absurd(1))]
        if start_ideo == "fascism":
            intro_opts.append(("Тихо подключить ячейки НПТ", npt_fascist_branch(1) + "\nadd_stability = -0.02"))
        elif start_ideo == "communism":
            intro_opts.append(("Собрать советы на площадях", popularity("communism", 0.05) + "\nadd_war_support = 0.03"))
        elif start_ideo == "democratic":
            intro_opts.append(("Созвать парламент", "add_stability = 0.04\n" + votes(1)))
        else:
            intro_opts.append(("Укрепить аппарат", "add_stability = 0.03\nadd_political_power = 40"))
        out.append(event(1, *ev["intro"], intro_opts))

        for k, br in enumerate(POLITICAL):
            b = s[br]
            ideo = b["ideology"]
            opt_a = ("Вперёд, без оглядки",
                     popularity(ideo, 0.05) + "\nadd_political_power = 25\n" + absurd(2 if br != "keep" else 1))
            if ideo == "fascism":
                opt_b = ("Вплести код НПТ в курс", npt_fascist_branch(1) + "\nadd_war_support = 0.04")
            elif ideo == "communism":
                opt_b = ("Экспорт лозунгов соседям",
                         "every_neighbor_country = {\n\tlimit = { is_mk_country = yes }\n"
                         "\tadd_popularity = { ideology = communism popularity = 0.02 }\n}")
            elif ideo == "democratic":
                opt_b = ("Международные наблюдатели", votes(1) + "\nadd_stability = 0.03")
            else:
                opt_b = ("Тихая стабилизация", "add_stability = 0.04\n" + mech(-5))
            out.append(event(2 + k, b["event"][0], b["event"][1], [opt_a, opt_b],
                             picture="GFX_report_event_generic_rally2"))

        sec = s["secret"]
        out.append(event(6, sec["event"][0], sec["event"][1], [
            ("Открыть тайну миру", npt(2) + "\n" + absurd(5) + "\n" + votes(1)),
            ("Засекретить всё", tech("electronics", f"{t}_secret_ev_tech") + "\nadd_political_power = 50")],
            picture="GFX_report_event_generic_conference"))
        out.append(event(7, *ev["mech_high"], [
            ("Выжать максимум", "add_political_power = 150\n" + absurd(4)),
            ("Распределить выгоды", "add_stability = 0.05\n" + mech(-10)),
            ("Купить голос на Конгрессе", votes(1) + "\nadd_political_power = -30")]))
        out.append(event(8, *ev["mech_low"], [
            ("Чрезвычайные меры", "add_stability = -0.05\n" + mech(15) + "\n" + absurd(2)),
            ("Купить лояльность", "add_political_power = -50\n" + mech(10)),
            ("Свалить вину на соседей",
             "random_neighbor_country = {\n\tlimit = { is_mk_country = yes }\n"
             "\tadd_opinion_modifier = { target = ROOT modifier = mk_ideological_kin }\n}\n"
             "add_war_support = 0.03")],
            picture="GFX_report_event_generic_riot"))
        out.append(event(9, *ev["mech_peak"], [
            ("Использовать подъём", "add_war_support = 0.08\n" + absurd(3)),
            ("Сбросить напряжение", mech(-20) + "\nadd_stability = 0.04"),
            ("Объявить исторический момент", votes(1) + "\nadd_political_power = 40")],
            picture="GFX_report_event_generic_rally2"))
        out.append(event(10, *ev["eco"], [
            ("Новые заводы", build("capital_scope", "industrial_complex")),
            ("Инженерные бюро", tech("industry", f"{t}_eco_ev_tech")),
            ("Военный заказ", build("capital_scope", "arms_factory") + "\nadd_war_support = 0.02")],
            picture="GFX_news_event_generic_factory"))
        out.append(event(11, *ev["army"], [
            ("Подготовить повод к войне",
             "random_neighbor_country = {\n\tlimit = {\n\t\tis_mk_country = yes\n"
             "\t\tNOT = { is_in_faction_with = ROOT }\n\t}\n\tROOT = {\n"
             "\t\tcreate_wargoal = { type = topple_government target = PREV }\n\t}\n}\n"
             + absurd(5)),
            ("Только оборона", "add_manpower = 10000\nadd_stability = 0.02"),
            ("Показательные манёвры", "army_experience = 20\nadd_war_support = 0.04")],
            picture="GFX_report_event_generic_military_parade"))
        out.append(event(12, *ev["diplo"], [
            ("Голос на Конгрессе", votes(1) + "\nadd_political_power = 50"),
            ("Друзья по всей Казуалии",
             "every_other_country = {\n\tlimit = { is_mk_country = yes }\n"
             "\tadd_opinion_modifier = { target = ROOT modifier = mk_kazual_goodwill }\n}"),
            ("Сколотить идеологический блок",
             "if = {\n\tlimit = { is_in_faction = no }\n\tmk_form_ideology_faction_effect = yes\n"
             "\telse = {\n\t\tadd_political_power = 50\n\t}\n}")],
            picture="GFX_report_event_generic_sign_treaty1"))
        out.append(event(13, sec["news"][0], sec["news"][1], [(sec["news"][2], "")], news=True,
                         picture="GFX_news_event_generic_read_write"))
        out.append(event(14, "Новый союзник",
                         "В блок вступила держава с близкой идеологией. Карта альянсов Казуалии дрогнула.",
                         [("Укрепить договор", "add_political_power = 30\nadd_stability = 0.02"),
                          ("Сразу требовать большего", votes(1) + "\n" + absurd(2))],
                         picture="GFX_report_event_generic_sign_treaty1"))
        out.append(event(15, "Слух из кабинетов",
                         f"В коридорах {s['tree_name']} шепчутся о новом курсе. Народ ждёт сигнала.",
                         [("Разогнать слух", absurd(2) + "\nadd_political_power = 20"),
                          ("Официально опровергнуть", "add_stability = 0.03\n" + mech(-5)),
                          ("Подлить масла", popularity(start_ideo, 0.03) + "\n" + absurd(3))]))
        out.append(event(16, "Повод на столе генштаба",
                         "Офицеры принесли три версии одного и того же повода к войне. Выберите тон.",
                         [("Жёсткий ультиматум",
                           "random_neighbor_country = {\n\tlimit = { is_mk_country = yes "
                           "NOT = { is_in_faction_with = ROOT } }\n"
                           "\tROOT = { create_wargoal = { type = topple_government target = PREV } }\n}\n"
                           + absurd(4)),
                          ("Тихая подготовка", "army_experience = 15\nadd_war_support = 0.05"),
                          ("Отложить", "add_stability = 0.02\nadd_political_power = 25")],
                         picture="GFX_report_event_generic_military_parade"))
        out.append(event(17, "Тихий торг эпохи",
                         "Нейтральные кулуары предлагают сделку: стабильность взамен на голос и сырьё.",
                         [("Принять сделку", votes(1) + "\n"
                           "random_owned_controlled_state = {\n\tadd_resource = { type = steel amount = 5 }\n}"),
                          ("Торговаться жёстче", "add_political_power = 60\n" + absurd(2)),
                          ("Отказаться", "add_stability = 0.04")]))
        out.append(event(18, "Утечка из секретного архива",
                         "Кто-то вынес папку с грифом. Теперь все делают вид, что не читали.",
                         [("Засекретить обратно", npt(1) + "\nadd_political_power = 40"),
                          ("Опубликовать выборочно", votes(1) + "\n" + absurd(3)),
                          ("Обвинить соседей",
                           "random_neighbor_country = {\n\tlimit = { is_mk_country = yes }\n"
                           "\tadd_opinion_modifier = { target = ROOT modifier = mk_ideological_kin }\n}\n"
                           "add_war_support = 0.03")],
                         picture="GFX_report_event_generic_conference"))
        out.append(event(19, "Идеологический саммит",
                         "За одним столом — все, кто разделяет ваш курс. Кто-то уже готов к блоку.",
                         [("Сколотить альянс сейчас",
                           "if = {\n\tlimit = { is_in_faction = no has_war = no }\n"
                           "\tmk_form_ideology_faction_effect = yes\n}"),
                          ("Сначала мнения",
                           "every_other_country = {\n\tlimit = { is_mk_country = yes has_government = ROOT }\n"
                           "\tadd_opinion_modifier = { target = ROOT modifier = mk_ideological_kin }\n}"),
                          ("Только протокол", votes(1) + "\nadd_political_power = 40")],
                         picture="GFX_report_event_generic_sign_treaty1"))
        return "\n\n".join(out) + "\n"

    # ---------- mechanic glue
    def refresh_block(self) -> str:
        t = self.tag
        return (f"if = {{\n\tlimit = {{ original_tag = {t} }}\n"
                f"\tremove_ideas = {t}_mech_low\n\tremove_ideas = {t}_mech_mid\n\tremove_ideas = {t}_mech_high\n"
                f"\tif = {{\n\t\tlimit = {{ check_variable = {{ mk_mech < 34 }} }}\n\t\tadd_ideas = {t}_mech_low\n\t}}\n"
                f"\telse_if = {{\n\t\tlimit = {{ check_variable = {{ mk_mech < 67 }} }}\n\t\tadd_ideas = {t}_mech_mid\n\t}}\n"
                f"\telse = {{\n\t\tadd_ideas = {t}_mech_high\n\t}}\n}}")

    def init_block(self) -> str:
        return (f"if = {{\n\tlimit = {{ original_tag = {self.tag} }}\n"
                f"\tset_variable = {{ mk_mech = {self.s['mech']['start']} }}\n}}")

    def monthly_block(self) -> str:
        t = self.tag
        return (f"if = {{\n\tlimit = {{ original_tag = {t} }}\n"
                f"\tif = {{\n\t\tlimit = {{\n\t\t\tcheck_variable = {{ mk_mech < 15 }}\n"
                f"\t\t\tNOT = {{ has_country_flag = mk_mech_low_cd }}\n\t\t}}\n"
                f"\t\tset_country_flag = {{ flag = mk_mech_low_cd days = 180 }}\n"
                f"\t\tcountry_event = {{ id = {self.ev(8)} days = 2 }}\n\t}}\n"
                f"\tif = {{\n\t\tlimit = {{\n\t\t\tcheck_variable = {{ mk_mech > 85 }}\n"
                f"\t\t\tNOT = {{ has_country_flag = mk_mech_high_cd }}\n\t\t}}\n"
                f"\t\tset_country_flag = {{ flag = mk_mech_high_cd days = 180 }}\n"
                f"\t\tcountry_event = {{ id = {self.ev(9)} days = 2 }}\n\t}}\n"
                f"\tif = {{\n\t\tlimit = {{\n\t\t\tNOT = {{ has_country_flag = mk_flavor_cd }}\n"
                f"\t\t\tcheck_variable = {{ mk_mech > 25 }}\n\t\t}}\n"
                f"\t\tset_country_flag = {{ flag = mk_flavor_cd days = 90 }}\n"
                f"\t\trandom_list = {{\n"
                f"\t\t\t30 = {{ country_event = {{ id = {self.ev(15)} days = 5 }} }}\n"
                f"\t\t\t25 = {{ country_event = {{ id = {self.ev(17)} days = 8 }} }}\n"
                f"\t\t\t20 = {{ country_event = {{ id = {self.ev(19)} days = 10 }} }}\n"
                f"\t\t\t25 = {{ }}\n"
                f"\t\t}}\n\t}}\n}}")

    def loc_file(self) -> str:
        lines = ["l_russian:"]
        for k, v in self.loc:
            v = v.replace('"', "'")
            lines.append(f' {k}:0 "{v}"')
        return "\n".join(lines) + "\n"


def load_specs() -> dict:
    specs = {}
    for p in sorted(TOOLS.glob("country_data_*.py")):
        spec = importlib.util.spec_from_file_location(p.stem, p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for tag, raw in mod.COUNTRIES.items():
            specs[tag] = expand_spec(tag, raw)
    return specs


def validate(tag: str, s: dict) -> None:
    want = target_sizes(s["big"])
    for sec, n in want.items():
        got = len(s[sec]["names"])
        if got != n:
            raise SystemExit(f"{tag}.{sec}: {got} names, expected {n}")


def write(path: Path, text: str, bom: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))


def main() -> None:
    specs = load_specs()
    tags = sys.argv[1:] or list(specs)
    all_specs = specs  # glue covers every built country, not only the selected ones
    for tag in tags:
        s = specs[tag]
        validate(tag, s)
        c = Country(tag, s)
        write(ROOT / f"common/ideas/mk_{tag}_ideas.txt", c.ideas())
        write(ROOT / f"common/national_focus/mk_{tag}.txt", c.focus_tree())
        cat, dec = c.decisions()
        write(ROOT / f"common/decisions/categories/mk_{tag}_categories.txt", cat)
        write(ROOT / f"common/decisions/mk_{tag}_decisions.txt", dec)
        events_txt = c.events()
        write(ROOT / f"events/mk_{tag}_events.txt", events_txt)
        c.L(f"{tag}_focus_desc", s["tree_name"])
        generated = "\n".join(
            (ROOT / p).read_text(encoding="utf-8") for p in (f"common/national_focus/mk_{tag}.txt",)) + events_txt
        for bonus in sorted(set(re.findall(rf"\bname = ({tag}_\w*(?:tech|doc_bonus))\b", generated))):
            c.L(bonus, TECH_LABELS.get(bonus[len(tag) + 1:], s["tree_name"]))
        write(ROOT / f"localisation/russian/mk_{tag}_l_russian.yml", c.loc_file(), bom=True)
        nf = sum(len(s[k]["names"]) for k in ("start", "keep", "a", "b", "c", "secret", "eco", "army", "diplo", "absurd"))
        print(f"{tag}: {nf} focuses, 19 events, 8 decisions, 12 ideas, {len(c.loc)} loc keys")

    built = [Country(t, all_specs[t]) for t in all_specs]
    glue = ("# Generated by tools/build_countries.py — national mechanic variable mk_mech (0..100)\n\n"
            "mk_mech_add = {\n\tadd_to_variable = { mk_mech = mk_mech_delta }\n"
            "\tclamp_variable = { var = mk_mech min = 0 max = 100 }\n\tmk_mech_refresh = yes\n}\n\n"
            "mk_mech_sub = {\n\tsubtract_from_variable = { mk_mech = mk_mech_delta }\n"
            "\tclamp_variable = { var = mk_mech min = 0 max = 100 }\n\tmk_mech_refresh = yes\n}\n\n"
            "mk_mech_refresh = {\n" + "\n".join(ind(c.refresh_block(), 1) for c in built) + "\n}\n\n"
            "mk_mech_init = {\n" + "\n".join(ind(c.init_block(), 1) for c in built) +
            "\n\tif = {\n\t\tlimit = { has_variable = mk_mech }\n\t\tmk_mech_refresh = yes\n\t}\n}\n\n"
            "mk_mech_monthly = {\n\tif = {\n\t\tlimit = { has_variable = mk_mech }\n" +
            "\n".join(ind(c.monthly_block(), 2) for c in built) + "\n\t}\n}\n")
    write(ROOT / "common/scripted_effects/mk_mech_effects.txt", glue)
    print("glue for:", ", ".join(all_specs))


if __name__ == "__main__":
    main()
