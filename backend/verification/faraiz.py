"""
Muslim inheritance (Faraiz) share calculator.

Covers the heirs that dominate Bangladeshi land disputes: spouse(s), sons,
daughters, father and mother. Handles 'awl (proportional reduction when fixed
shares exceed the estate) and radd (return of surplus to non-spouse sharers).
Other heirs (siblings, grandchildren, ...) are out of scope and must be
reviewed by a lawyer.
"""

from dataclasses import dataclass, field
from fractions import Fraction

RELATIONS = ("husband", "wife", "son", "daughter", "father", "mother")


@dataclass
class Heir:
    key: str
    relation: str
    name: str = ""


@dataclass
class HeirShare:
    key: str
    relation: str
    name: str
    share: Fraction
    basis: str


@dataclass
class FaraizResult:
    shares: list[HeirShare]
    notes: list[str] = field(default_factory=list)

    def share_of(self, key: str) -> Fraction:
        for s in self.shares:
            if s.key == key:
                return s.share
        return Fraction(0)


def calculate(heirs: list[Heir]) -> FaraizResult:
    for h in heirs:
        if h.relation not in RELATIONS:
            raise ValueError(f"Unsupported relation: {h.relation}")

    by_rel = {r: [h for h in heirs if h.relation == r] for r in RELATIONS}
    sons, daughters = by_rel["son"], by_rel["daughter"]
    husband, wives = by_rel["husband"], by_rel["wife"]
    father, mother = by_rel["father"], by_rel["mother"]
    if len(husband) > 1 or len(father) > 1 or len(mother) > 1:
        raise ValueError("Only one husband, father and mother are possible")
    if husband and wives:
        raise ValueError("Deceased cannot have both a husband and wives")

    has_children = bool(sons or daughters)
    notes: list[str] = []

    # Fixed (Quranic) shares, collectively per heir group.
    fixed: dict[str, Fraction] = {}
    basis: dict[str, str] = {}

    if husband:
        fixed["husband"] = Fraction(1, 4) if has_children else Fraction(1, 2)
        basis["husband"] = f"{fixed['husband']} (husband, {'with' if has_children else 'no'} children)"
    if wives:
        fixed["wife"] = Fraction(1, 8) if has_children else Fraction(1, 4)
        basis["wife"] = f"{fixed['wife']} shared by {len(wives)} wife/wives ({'with' if has_children else 'no'} children)"

    spouse_share = fixed.get("husband", Fraction(0)) + fixed.get("wife", Fraction(0))

    if mother:
        if has_children:
            fixed["mother"] = Fraction(1, 6)
            basis["mother"] = "1/6 (mother, with children)"
        elif father and spouse_share:
            fixed["mother"] = (1 - spouse_share) / 3
            basis["mother"] = "1/3 of remainder after spouse (Umariyyatan)"
        else:
            fixed["mother"] = Fraction(1, 3)
            basis["mother"] = "1/3 (mother, no children)"

    if father and has_children:
        fixed["father"] = Fraction(1, 6)
        basis["father"] = "1/6 (father, with children)"

    if daughters and not sons:
        fixed["daughter"] = Fraction(1, 2) if len(daughters) == 1 else Fraction(2, 3)
        basis["daughter"] = f"{fixed['daughter']} shared by {len(daughters)} daughter(s) (no son)"

    total_fixed = sum(fixed.values(), Fraction(0))

    if total_fixed > 1:
        notes.append(f"'Awl applied: fixed shares total {total_fixed}, reduced proportionally.")
        fixed = {k: v / total_fixed for k, v in fixed.items()}
        total_fixed = Fraction(1)

    residue = 1 - total_fixed
    group_share: dict[str, Fraction] = dict(fixed)

    if residue > 0:
        if sons:
            units = 2 * len(sons) + len(daughters)
            group_share["son"] = residue * 2 * len(sons) / units
            basis["son"] = "residuary (asaba), son takes double of daughter"
            if daughters:
                group_share["daughter"] = residue * len(daughters) / units
                basis["daughter"] = "residuary with son(s), half of a son's share"
        elif father:
            group_share["father"] = group_share.get("father", Fraction(0)) + residue
            basis["father"] = ("1/6 + residue" if "father" in fixed else "residuary") + " (father)"
        else:
            non_spouse = {k: v for k, v in fixed.items() if k not in ("husband", "wife")}
            pool = non_spouse or fixed
            if not non_spouse:
                notes.append("Radd to spouse: no other heir present (follow current court practice).")
            else:
                notes.append(f"Radd applied: surplus {residue} returned to non-spouse sharers.")
            pool_total = sum(pool.values(), Fraction(0))
            for k, v in pool.items():
                group_share[k] = group_share[k] + residue * v / pool_total

    shares: list[HeirShare] = []
    for rel in RELATIONS:
        members = by_rel[rel]
        if not members:
            continue
        each = group_share.get(rel, Fraction(0)) / len(members)
        for h in members:
            shares.append(HeirShare(h.key, rel, h.name, each, basis.get(rel, "")))

    assert sum((s.share for s in shares), Fraction(0)) == 1, "shares must total the estate"
    return FaraizResult(shares=shares, notes=notes)
