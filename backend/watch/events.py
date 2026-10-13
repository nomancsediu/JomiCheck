"""
Detect records added to a watched plot after the buyer started watching.

Between the bainanama and the registration, a seller can still sell, mortgage
or get the land tied up in a case; these alerts surface that in time.
"""
from land import models as m
from verification.catalog import RESTRICTED_KINDS, bn_num

LEGAL_BN = {
    "civil_suit": "দেওয়ানি মামলা", "tribunal": "ভূমি জরিপ ট্রাইব্যুনাল মামলা", "injunction": "হস্তান্তরে নিষেধাজ্ঞা",
    "section_144": "১৪৪ ধারার মামলা", "acquisition": "সরকারি অধিগ্রহণ",
    **{k: v[1] for k, v in RESTRICTED_KINDS.items()},
}
MUTATION_BN = {"approved": "মঞ্জুর", "pending": "চলমান", "rejected": "নামঞ্জুর"}


def _names(people) -> tuple[str, str]:
    people = list(people)
    return ", ".join(p.name_en for p in people), ", ".join(p.name_bn for p in people)


def _deed(d: m.Deed) -> dict:
    (s_en, s_bn), (b_en, b_bn) = _names(d.sellers.all()), _names(d.buyers.all())
    return {"severity": "critical", "date": d.registration_date,
            "en": f"New deed {d.deed_no} registered: {s_en} transferred {d.area_acre} acre to {b_en}.",
            "bn": f"নতুন দলিল {bn_num(d.deed_no)} নিবন্ধিত: {s_bn} {bn_num(d.area_acre)} একর {b_bn}-কে হস্তান্তর করেছেন।"}


def _mutation(x: m.Mutation) -> dict:
    return {"severity": "major", "date": x.application_date,
            "en": f"Mutation case {x.case_no} filed in the name of {x.new_owner.name_en} ({x.status}).",
            "bn": f"{x.new_owner.name_bn}-এর নামে নামজারি কেস {bn_num(x.case_no)} দায়ের ({MUTATION_BN.get(x.status, x.status)})।"}


def _legal(s: m.LegalStatus) -> dict:
    return {"severity": "critical", "date": s.since,
            "en": f"{s.get_status_type_display()} recorded: {s.reference_no}.",
            "bn": f"{LEGAL_BN.get(s.status_type, s.get_status_type_display())} রেকর্ড হয়েছে: {bn_num(s.reference_no)}।"}


def _mortgage(x: m.Mortgage) -> dict:
    return {"severity": "critical", "date": x.registered_on,
            "en": f"Mortgaged by {x.mortgagor.name_en} to {x.lender} for {x.amount_bdt:,} Tk.",
            "bn": f"{x.mortgagor.name_bn} জমিটি {x.lender}-এর কাছে {bn_num(f'{x.amount_bdt:,}')} টাকায় বন্ধক রেখেছেন।"}


def _bainanama(x: m.Bainanama) -> dict:
    return {"severity": "critical", "date": x.agreement_date,
            "en": f"Agreement for sale {x.agreement_no}: {x.seller.name_en} agreed to sell {x.area_acre} acre to {x.buyer.name_en}.",
            "bn": f"বায়নানামা {bn_num(x.agreement_no)}: {x.seller.name_bn} {bn_num(x.area_acre)} একর {x.buyer.name_bn}-এর কাছে বিক্রির চুক্তি করেছেন।"}


def _poa(x: m.PowerOfAttorney) -> dict:
    return {"severity": "major", "date": x.executed_on,
            "en": f"Power of attorney {x.poa_no}: {x.principal.name_en} authorised {x.attorney.name_en}.",
            "bn": f"আমমোক্তারনামা {bn_num(x.poa_no)}: {x.principal.name_bn} {x.attorney.name_bn}-কে ক্ষমতা দিয়েছেন।"}


TRACKED = {
    "deed": ("deeds", _deed),
    "mutation": ("mutations", _mutation),
    "legal": ("legal_statuses", _legal),
    "mortgage": ("mortgages", _mortgage),
    "bainanama": ("bainanamas", _bainanama),
    "poa": ("poas", _poa),
}


def snapshot(plot: m.Plot) -> dict:
    return {kind: list(getattr(plot, rel).values_list("id", flat=True)) for kind, (rel, _) in TRACKED.items()}


def alerts(watch) -> list[dict]:
    out = []
    for kind, (rel, describe) in TRACKED.items():
        seen = set(watch.snapshot.get(kind, []))
        for record in getattr(watch.plot, rel).exclude(id__in=seen):
            out.append({"kind": kind, **describe(record)})
    others = (watch.plot.purchase_intents.filter(created_at__gt=watch.created_at)
              .exclude(buyer_token=watch.buyer_token).values("buyer_token").distinct().count())
    if others:
        out.append({
            "kind": "buyer", "severity": "major", "date": None,
            "en": f"{others} other buyer(s) checked this plot after you started watching.",
            "bn": f"আপনি নজর রাখা শুরুর পর আরও {bn_num(others)} জন ক্রেতা এই জমি যাচাই করেছেন।",
        })
    out.sort(key=lambda a: (a["severity"] != "critical", str(a["date"] or "")))
    for a in out:
        a["date"] = a["date"].isoformat() if a["date"] else None
    return out
