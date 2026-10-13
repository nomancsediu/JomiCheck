"""
Compare documents the buyer uploaded (as read by Gemma) with the official records.

A khatian, deed or tax receipt that disagrees with the record it claims to be a
copy of is the most common sign of a forged land document.
"""
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from fractions import Fraction

from land import models as m
from land.units import ana_to_share, share_to_ana
from verification.catalog import bn_num
from verification.matching import MATCH_THRESHOLD, name_score

AREA_TOLERANCE = Decimal("0.01")  # acre
SHARE_TOLERANCE = Fraction(1, 100)

DOC_LABELS = {
    "khatian": ("Khatian", "খতিয়ান"),
    "mutation_khatian": ("Mutation khatian", "নামজারি খতিয়ান"),
    "deed": ("Deed", "দলিল"),
    "tax_receipt": ("Land tax receipt (dakhila)", "ভূমি উন্নয়ন কর রসিদ (দাখিলা)"),
}


def _check(ok: bool, en: str, bn: str, critical: bool = True) -> dict:
    return {"ok": ok, "severity": "ok" if ok else ("critical" if critical else "major"), "en": en, "bn": bn}


def _names(people) -> tuple[str, str]:
    people = list(people)
    return ", ".join(p.name_en for p in people), ", ".join(p.name_bn for p in people)


def _matches(name: str, people) -> m.Person | None:
    best = max(people, key=lambda p: name_score(name, p), default=None)
    return best if best and name_score(name, best) >= MATCH_THRESHOLD else None


def _parse_share(text: str) -> Fraction | None:
    text = (text or "").translate(str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")).strip()
    if not text:
        return None
    ana = ana_to_share(text)
    if ana is not None:
        return ana
    try:
        if "/" in text:
            a, b = text.split("/", 1)
            return Fraction(int(a), int(b))
        return Fraction(re.match(r"[\d.]+", text).group(0))
    except (ValueError, ZeroDivisionError, AttributeError):
        return None


def _parse_date(text: str) -> date | None:
    text = (text or "").translate(str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789"))
    nums = re.findall(r"\d+", text)
    if len(nums) < 3:
        return None
    a, b, c = (int(n) for n in nums[:3])
    try:
        return date(a, b, c) if a > 31 else date(c, b, a)
    except ValueError:
        return None


def _acre(value) -> Decimal | None:
    try:
        return Decimal(str(value)) if value not in (None, "") else None
    except InvalidOperation:
        return None


def _dag_check(doc_dags: set[str], dag_no: str | None) -> list[dict]:
    if not dag_no or not doc_dags or dag_no in doc_dags:
        return []
    shown = ", ".join(sorted(doc_dags))
    return [_check(False, f"This document is for dag {shown}, not dag {dag_no} being bought.",
                   f"এই ডকুমেন্ট দাগ {bn_num(shown)}-এর, কেনা হচ্ছে দাগ {bn_num(dag_no)}।", critical=False)]


def _check_khatian(doc: dict, mouza: m.Mouza, dag_no: str | None) -> list[dict]:
    no = doc.get("khatian_no") or ""
    if not no:
        return [_check(False, "The khatian number could not be read.", "খতিয়ান নম্বর পড়া যায়নি।", critical=False)]
    survey = doc.get("survey") or ("NAMJARI" if doc.get("document_type") == "mutation_khatian" else None)
    qs = m.Khatian.objects.filter(mouza=mouza, khatian_no=no)
    if survey:
        qs = qs.filter(survey=survey)
    khatian = qs.prefetch_related("owners__person", "plots").order_by("-record_year").first()
    label = f"{survey or ''} khatian {no}".strip()
    if not khatian:
        return [_check(False, f"No {label} exists in the records of {mouza.name_en} mouza. The document may be fake.",
                       f"{mouza.name_bn} মৌজার রেকর্ডে {survey or ''} খতিয়ান {bn_num(no)} নেই। ডকুমেন্টটি জাল হতে পারে।")]

    checks = [_check(True, f"{label} exists in the records.", f"রেকর্ডে {survey or ''} খতিয়ান {bn_num(no)} আছে।")]
    owners = list(khatian.owners.all())
    people = [o.person for o in owners]
    rec_en, rec_bn = _names(people)
    matched = set()
    for o in doc.get("owners") or []:
        person = _matches(o["name"], people)
        if not person:
            checks.append(_check(
                False, f"Owner '{o['name']}' on the document is not in the record. The record shows: {rec_en}.",
                f"ডকুমেন্টে মালিক '{o['name']}', কিন্তু রেকর্ডে নেই। রেকর্ডে মালিক: {rec_bn}।"))
            continue
        matched.add(person.id)
        doc_share = _parse_share(o.get("share", ""))
        rec_share = Fraction(next(x.share for x in owners if x.person_id == person.id))
        if doc_share is not None and abs(doc_share - rec_share) > SHARE_TOLERANCE:
            ana = share_to_ana(rec_share)
            checks.append(_check(
                False, f"{person.name_en}'s share is '{o['share']}' on the document but {ana['en']} in the record.",
                f"ডকুমেন্টে {person.name_bn}-এর অংশ '{o['share']}', রেকর্ডে {ana['bn']}।"))
    missing = [p for p in people if p.id not in matched]
    if doc.get("owners") and missing:
        en, bn = _names(missing)
        checks.append(_check(False, f"Recorded owner(s) missing from the document: {en}.",
                             f"রেকর্ডের মালিক ডকুমেন্টে নেই: {bn}।"))
    if doc.get("owners") and not missing and len(matched) == len(doc["owners"]):
        checks.append(_check(True, "Owner names match the record.", "মালিকের নাম রেকর্ডের সাথে মেলে।"))

    plots = {p.dag_no: p for p in khatian.plots.all()}
    total_share = sum(o.share for o in owners)
    for p in doc.get("plots") or []:
        plot = plots.get(p["dag_no"])
        if not plot:
            checks.append(_check(False, f"Dag {p['dag_no']} is not in {label} in the records.",
                                 f"রেকর্ডে খতিয়ান {bn_num(no)}-এ দাগ {bn_num(p['dag_no'])} নেই।"))
            continue
        area = _acre(p.get("area_acre"))
        expected = {plot.area_acre, plot.area_acre * total_share}
        if area is not None and all(abs(area - e) > AREA_TOLERANCE for e in expected):
            checks.append(_check(
                False, f"Dag {plot.dag_no} area is {area} acre on the document but {plot.area_acre} acre in the record.",
                f"ডকুমেন্টে দাগ {bn_num(plot.dag_no)}-এর জমি {bn_num(area)} একর, রেকর্ডে {bn_num(plot.area_acre)} একর।"))
    return checks + _dag_check({p["dag_no"] for p in doc.get("plots") or []}, dag_no)


def _check_deed(doc: dict, mouza: m.Mouza, dag_no: str | None) -> list[dict]:
    info = doc.get("deed") or {}
    no = info.get("deed_no") or ""
    if not no:
        return [_check(False, "The deed number could not be read.", "দলিল নম্বর পড়া যায়নি।", critical=False)]
    deed = (m.Deed.objects.filter(deed_no=no, plot__mouza=mouza)
            .select_related("plot").prefetch_related("sellers", "buyers").first())
    if not deed:
        return [_check(False, f"Deed {no} is not in the Sub-Registry records for {mouza.name_en}. It may be forged.",
                       f"{mouza.name_bn} মৌজার সাব-রেজিস্ট্রি রেকর্ডে দলিল {bn_num(no)} নেই। দলিলটি জাল হতে পারে।")]

    checks = [_check(True, f"Deed {no} exists in the records.", f"রেকর্ডে দলিল {bn_num(no)} আছে।")]
    if deed.status == m.Deed.Status.CANCELLED:
        checks.append(_check(False, f"Deed {no} was cancelled by a court.", f"দলিল {bn_num(no)} আদালত বাতিল করেছেন।"))
    for role, names, people in (("Seller", info.get("sellers"), deed.sellers.all()),
                                ("Buyer", info.get("buyers"), deed.buyers.all())):
        people = list(people)
        role_bn = "বিক্রেতা" if role == "Seller" else "ক্রেতা"
        rec_en, rec_bn = _names(people)
        for name in names or []:
            if not _matches(name, people):
                checks.append(_check(False, f"{role} '{name}' on the document differs from the record: {rec_en}.",
                                     f"ডকুমেন্টে {role_bn} '{name}', রেকর্ডে {role_bn}: {rec_bn}।"))
    when = _parse_date(info.get("registration_date"))
    if when and when != deed.registration_date:
        checks.append(_check(False, f"Registration date is {when} on the document but {deed.registration_date} in the record.",
                             f"ডকুমেন্টে নিবন্ধনের তারিখ {bn_num(when)}, রেকর্ডে {bn_num(deed.registration_date)}।",
                             critical=False))
    for p in doc.get("plots") or []:
        if p["dag_no"] != deed.plot.dag_no:
            checks.append(_check(False, f"The document names dag {p['dag_no']}, the registered deed is for dag {deed.plot.dag_no}.",
                                 f"ডকুমেন্টে দাগ {bn_num(p['dag_no'])}, নিবন্ধিত দলিল দাগ {bn_num(deed.plot.dag_no)}-এর।"))
        area = _acre(p.get("area_acre"))
        if area is not None and abs(area - deed.area_acre) > AREA_TOLERANCE:
            checks.append(_check(False, f"Area is {area} acre on the document but {deed.area_acre} acre in the record.",
                                 f"ডকুমেন্টে জমি {bn_num(area)} একর, রেকর্ডে {bn_num(deed.area_acre)} একর।"))
    if len(checks) == 1:
        checks.append(_check(True, "Sellers, buyers, date, dag and area match the record.",
                             "বিক্রেতা, ক্রেতা, তারিখ, দাগ ও জমির পরিমাণ রেকর্ডের সাথে মেলে।"))
    return checks + _dag_check({deed.plot.dag_no}, dag_no)


def _check_tax(doc: dict, mouza: m.Mouza, dag_no: str | None) -> list[dict]:
    info = doc.get("tax_receipt") or {}
    holding = info.get("holding_no") or ""
    if not holding:
        return [_check(False, "The holding number could not be read.", "হোল্ডিং নম্বর পড়া যায়নি।", critical=False)]
    record = m.TaxRecord.objects.filter(holding_no__iexact=holding, plot__mouza=mouza).select_related("plot").first()
    if not record:
        return [_check(False, f"Holding {holding} is not in the land tax records. The receipt may be fake.",
                       f"ভূমি উন্নয়ন কর রেকর্ডে হোল্ডিং {bn_num(holding)} নেই। রসিদটি জাল হতে পারে।")]
    checks = [_check(True, f"Holding {holding} exists in the records.", f"রেকর্ডে হোল্ডিং {bn_num(holding)} আছে।")]
    try:
        paid = int(str(info.get("paid_upto_year") or "").strip()[:4])
    except ValueError:
        paid = None
    if paid and paid > record.paid_upto_year:
        checks.append(_check(
            False, f"The receipt says tax is paid up to {paid}, but the records show {record.paid_upto_year} "
                   f"with {record.arrears_bdt} Tk unpaid. The receipt may be fake.",
            f"রসিদে {bn_num(paid)} সাল পর্যন্ত কর পরিশোধ দেখানো, কিন্তু রেকর্ডে {bn_num(record.paid_upto_year)} সাল পর্যন্ত, "
            f"বকেয়া {bn_num(record.arrears_bdt)} টাকা। রসিদটি জাল হতে পারে।"))
    elif paid:
        checks.append(_check(True, f"Paid up to {paid}, consistent with the records.",
                             f"{bn_num(paid)} সাল পর্যন্ত পরিশোধ, রেকর্ডের সাথে সামঞ্জস্যপূর্ণ।"))
    return checks + _dag_check({record.plot.dag_no}, dag_no)


CHECKERS = {
    "khatian": _check_khatian, "mutation_khatian": _check_khatian,
    "deed": _check_deed, "tax_receipt": _check_tax,
}


def check_documents(mouza_id: int, documents: list[dict], dag_no: str | None = None) -> dict:
    """Check each extracted document against the records of the mouza; `dag_no` is the plot being bought."""
    mouza = m.Mouza.objects.get(pk=mouza_id)
    results = []
    for i, doc in enumerate(documents):
        kind = doc.get("document_type") or "other"
        en, bn = DOC_LABELS.get(kind, ("Other document", "অন্যান্য ডকুমেন্ট"))
        checker = CHECKERS.get(kind)
        checks = checker(doc, mouza, dag_no) if checker else [
            _check(False, "This document type cannot be checked against the records.",
                   "এই ধরনের ডকুমেন্ট রেকর্ডের সাথে মেলানো যায় না।", critical=False)]
        worst = "critical" if any(c["severity"] == "critical" for c in checks) else (
            "major" if any(c["severity"] == "major" for c in checks) else "ok")
        results.append({"index": i, "type": kind, "label": {"en": en, "bn": bn}, "status": worst, "checks": checks})
    return {
        "documents": results,
        "critical": sum(1 for r in results for c in r["checks"] if c["severity"] == "critical"),
        "major": sum(1 for r in results for c in r["checks"] if c["severity"] == "major"),
    }
