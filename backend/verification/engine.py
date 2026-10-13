"""
Pre-purchase verification engine.

Deterministic, explainable rules decide the risk. Every flag carries its
evidence, legal basis and a bilingual explanation.
"""

from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal
from fractions import Fraction

from django.utils import timezone

from anomaly import model as anomaly_model
from anomaly.features import deed_transfer, proposed_transfer
from documents.crosscheck import check_documents
from land import models as m
from land.units import share_to_ana

from . import faraiz, guidance
from .catalog import (
    CRITICAL, LEVEL_BANDS, LITIGATION_KINDS, POA_REASONS, RESTRICTED_KINDS, RULES, bn_num,
)
from .matching import best_match

RAPID_WINDOW_DAYS = 365
RAPID_MIN_SALES = 3
LOW_PRICE_RATIO = Decimal("0.5")
LOW_PRICE_LOOKBACK_YEARS = 10
INTENT_WINDOW_DAYS = 30
AREA_TOLERANCE = Decimal("0.0001")

LAND_CLASS_BN = {
    "agricultural": "কৃষি (নাল)",
    "homestead": "বসতভিটা (ভিটি)",
    "commercial": "বাণিজ্যিক",
    "pond": "ডোবা / পুকুর",
}


class _SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def _fmt(text: str, params: dict) -> str:
    return text.format_map(_SafeDict(params))


def _acre(value) -> str:
    return f"{Decimal(value).quantize(Decimal('0.0001')).normalize():f}"


def _names(people, lang="en") -> str:
    attr = "name_en" if lang == "en" else "name_bn"
    return ", ".join(getattr(p, attr) for p in people) or "-"


@dataclass
class Flag:
    code: str
    params: dict = field(default_factory=dict)
    evidence: list = field(default_factory=list)

    def render(self) -> dict:
        rule = RULES[self.code]
        params = dict(self.params)
        for key, value in list(params.items()):
            params.setdefault(f"{key}_bn", bn_num(value))
        return {
            "code": self.code,
            "tier": rule["tier"],
            "points": rule["points"],
            "law": _fmt(rule["law"], params),
            "title": {"en": _fmt(rule["title_en"], params), "bn": _fmt(rule["title_bn"], params)},
            "explanation": {"en": _fmt(rule["explain_en"], params), "bn": _fmt(rule["explain_bn"], params)},
            "action": {"en": _fmt(rule["action_en"], params), "bn": _fmt(rule["action_bn"], params)},
            "seller_question": {"en": _fmt(rule["question_en"], params), "bn": _fmt(rule["question_bn"], params)},
            "evidence": self.evidence,
        }


class PlotNotFound(Exception):
    pass


class Verifier:
    def __init__(self, plot: m.Plot, seller_name: str, area_acre: Decimal,
                 khatian_no: str = "", buyer_token: str = "", documents: list[dict] | None = None):
        self.plot = plot
        self.documents = documents or []
        self.document_check = None
        self.seller_name = seller_name.strip()
        self.area = Decimal(area_acre)
        self.khatian_no = (khatian_no or "").strip()
        self.buyer_token = (buyer_token or "").strip()

        self.flags: list[Flag] = []
        self.ml_check = {"model": "Isolation Forest", "checked": 0, "unusual": 0}
        self.notes: list[dict] = []

        self.khatians = sorted(
            plot.khatians.prefetch_related("owners__person"), key=lambda k: k.order,
        )
        self.latest = self.khatians[-1] if self.khatians else None
        self.latest_owners = list(self.latest.owners.select_related("person")) if self.latest else []
        self.deeds = list(
            plot.deeds.filter(status=m.Deed.Status.REGISTERED)
            .prefetch_related("sellers", "buyers").order_by("registration_date")
        )
        self.heir_links = {}
        for link in m.HeirLink.objects.select_related("deceased", "heir"):
            self.heir_links.setdefault(link.deceased_id, []).append(link)
        self.poas = list(plot.poas.select_related("principal", "attorney"))

    # ------------------------------------------------------------------ helpers
    def _heirs_of(self, person_id):
        return self.heir_links.get(person_id, [])

    def _expand_entitled(self, seed_ids: set[int]) -> set[int]:
        """Everyone who can trace a right from seed_ids via inheritance, deed or valid POA."""
        entitled = set(seed_ids)
        changed = True
        while changed:
            changed = False
            for pid in list(entitled):
                for link in self._heirs_of(pid):
                    if link.heir_id not in entitled:
                        entitled.add(link.heir_id)
                        changed = True
            for deed in self.deeds:
                if {p.id for p in deed.sellers.all()} & entitled:
                    for b in deed.buyers.all():
                        if b.id not in entitled:
                            entitled.add(b.id)
                            changed = True
        return entitled

    def _add(self, code, evidence=None, **params):
        self.flags.append(Flag(code, params, evidence or []))

    # ------------------------------------------------------------------ seller
    def _resolve_seller(self):
        candidates: dict[int, m.Person] = {}
        for ko in self.latest_owners:
            candidates[ko.person_id] = ko.person
            if ko.person.is_deceased:
                for link in self._heirs_of(ko.person_id):
                    candidates[link.heir_id] = link.heir
        for poa in self.poas:
            candidates[poa.attorney_id] = poa.attorney
        for deed in self.deeds:
            for p in list(deed.sellers.all()) + list(deed.buyers.all()):
                candidates[p.id] = p

        person, score = best_match(self.seller_name, candidates.values())
        role, detail = "none", {}
        if person:
            owner_row = next((ko for ko in self.latest_owners if ko.person_id == person.id), None)
            deceased_owner_links = [
                (ko, link) for ko in self.latest_owners if ko.person.is_deceased
                for link in self._heirs_of(ko.person_id) if link.heir_id == person.id
            ]
            poa = next((p for p in self.poas if p.attorney_id == person.id), None)
            bought = [d for d in self.deeds if person in d.buyers.all()]
            if owner_row and not person.is_deceased:
                role, detail = "owner", {"share": owner_row.share}
            elif owner_row:
                role = "deceased_owner"
            elif deceased_owner_links:
                role, detail = "heir", {"links": deceased_owner_links}
            elif bought:
                role, detail = "deed_buyer", {"deeds": bought}
            elif poa:
                role, detail = "attorney", {"poa": poa}
        return person, score, role, detail

    # ------------------------------------------------------------------ inheritance
    def _inheritance_for(self, deceased: m.Person, owner_share: Decimal):
        links = self._heirs_of(deceased.id)
        if deceased.religion != m.Person.Religion.MUSLIM:
            return None
        result = faraiz.calculate([
            faraiz.Heir(key=str(l.heir_id), relation=l.relation, name=l.heir.name_en) for l in links
        ])
        plot_area = Fraction(str(self.plot.area_acre)) * Fraction(str(owner_share))
        heirs = []
        for s in result.shares:
            link = next(l for l in links if str(l.heir_id) == s.key)
            heirs.append({
                "person_id": link.heir_id,
                "name": {"en": link.heir.name_en, "bn": link.heir.name_bn},
                "relation": s.relation,
                "is_minor": link.heir.is_minor,
                "share": f"{s.share.numerator}/{s.share.denominator}",
                "share_decimal": round(float(s.share), 6),
                "area_acre": _acre(Decimal(float(s.share * plot_area))),
                "basis": s.basis,
            })
        return {
            "deceased": {"en": deceased.name_en, "bn": deceased.name_bn},
            "date_of_death": deceased.date_of_death.isoformat() if deceased.date_of_death else None,
            "owner_share": _acre(owner_share),
            "estate_area_acre": _acre(Decimal(float(plot_area))),
            "heirs": heirs,
            "notes": result.notes,
            "law": "Muslim personal law (Faraiz)",
        }

    # ------------------------------------------------------------------ rules
    def run(self) -> dict:
        plot = self.plot
        person, score, role, detail = self._resolve_seller()
        seller_display = person.name_en if person else self.seller_name
        sellable = None
        inheritance = None
        co_sharers: list[m.Person] = []

        latest_label = f"{self.latest.survey} {self.latest.khatian_no}" if self.latest else "-"
        owners_people = [ko.person for ko in self.latest_owners]

        if role == "owner":
            sellable = Decimal(detail["share"]) * plot.area_acre
            co_sharers = [p for p in owners_people if p.id != person.id and not p.is_deceased]
        elif role == "deceased_owner":
            self._add("OWNER_DECEASED", owner=person.name_en,
                      died=person.date_of_death.isoformat() if person.date_of_death else "unknown")
        elif role == "heir":
            sellable = Decimal(0)
            for ko, link in detail["links"]:
                info = self._inheritance_for(ko.person, ko.share)
                if info is None:
                    sellable = None
                    self._add("INHERITANCE_REVIEW", owner=ko.person.name_en)
                    break
                inheritance = info
                mine = next(h for h in info["heirs"] if h["person_id"] == person.id)
                sellable += Decimal(mine["area_acre"])
                co_sharers += [l.heir for l in self._heirs_of(ko.person_id) if l.heir_id != person.id]
            deceased_names = _names([ko.person for ko, _ in detail["links"]])
            deceased_names_bn = _names([ko.person for ko, _ in detail["links"]], "bn")
            self._add(
                "MUTATION_MISSING",
                detail=f"The land is still recorded in the name of the deceased owner ({deceased_names}) in {latest_label}. Mutation in the heirs' names has not been done.",
                detail_bn=f"জমিটি এখনও মৃত মালিকের ({deceased_names_bn}) নামে {latest_label} খতিয়ানে রেকর্ডভুক্ত। ওয়ারিশদের নামে নামজারি হয়নি।",
            )
        elif role == "deed_buyer":
            sellable = sum((d.area_acre for d in detail["deeds"]), Decimal(0))
            muts = list(plot.mutations.filter(new_owner=person).order_by("-application_date"))
            status = muts[0].status if muts else "not applied"
            deed_nos = ", ".join(d.deed_no for d in detail["deeds"])
            self._add(
                "MUTATION_MISSING",
                evidence=[f"Mutation {mu.case_no}: {mu.status}" for mu in muts],
                detail=f"The seller bought by deed {deed_nos}, but mutation in his name is '{status}'. The latest record ({latest_label}) still shows {_names(owners_people)}.",
                detail_bn=f"বিক্রেতা দলিল {deed_nos} দিয়ে কিনেছেন, কিন্তু তাঁর নামে নামজারির অবস্থা '{status}'। সর্বশেষ রেকর্ডে ({latest_label}) এখনও আছেন {_names(owners_people, 'bn')}।",
            )
        elif role == "attorney":
            poa = detail["poa"]
            principal_row = next((ko for ko in self.latest_owners if ko.person_id == poa.principal_id), None)
            reasons = []
            if poa.is_revoked:
                reasons.append("revoked")
            if not poa.is_registered:
                reasons.append("unregistered")
            if poa.scope != m.PowerOfAttorney.Scope.SALE:
                reasons.append("scope")
            if poa.principal.is_deceased:
                reasons.append("principal_deceased")
            if reasons:
                self._add(
                    "POA_INVALID", principal=poa.principal.name_en, poa=poa.poa_no,
                    reasons=", ".join(POA_REASONS[r][0] for r in reasons),
                    reasons_bn=", ".join(POA_REASONS[r][1] for r in reasons),
                )
            else:
                self._add("POA_SALE", principal=poa.principal.name_en, poa=poa.poa_no)
                if principal_row:
                    sellable = Decimal(principal_row.share) * plot.area_acre
                    co_sharers = [p for p in owners_people if p.id != poa.principal_id and not p.is_deceased]
        else:
            self._add(
                "OWNERSHIP_MISMATCH", khatian=latest_label, khatian_bn=bn_num(latest_label),
                owners=_names(owners_people), owners_bn=_names(owners_people, "bn"),
                seller=self.seller_name,
            )

        # Prior sales by the same person that the record has not caught up with.
        prior_deeds = []
        if person:
            since_year = self.latest.record_year if role in ("owner", "heir") and self.latest else 0
            for d in self.deeds:
                if d.deed_type == m.Deed.DeedType.SALE and person in d.sellers.all() \
                        and d.registration_date.year >= since_year:
                    prior_deeds.append(d)
        prior_sold = sum((d.area_acre for d in prior_deeds), Decimal(0))
        remaining = None if sellable is None else max(sellable - prior_sold, Decimal(0))

        if prior_deeds and (role == "none" or remaining is None or self.area > remaining + AREA_TOLERANCE):
            self._add(
                "DOUBLE_SELLING",
                evidence=[f"Deed {d.deed_no} ({d.registration_date}): {_names(d.sellers.all())} -> {_names(d.buyers.all())}, {_acre(d.area_acre)} acre" for d in prior_deeds],
                sold=_acre(prior_sold), area=_acre(self.area),
                remaining=_acre(remaining or 0), deeds=", ".join(d.deed_no for d in prior_deeds),
            )
        elif remaining is not None and role in ("owner", "heir", "deed_buyer", "attorney") \
                and self.area > remaining + AREA_TOLERANCE:
            if role == "heir":
                basis_en, basis_bn = "Faraiz share as heir", "ওয়ারিশ হিসেবে ফারায়েজ অনুযায়ী অংশ"
            elif role == "deed_buyer":
                basis_en, basis_bn = "area bought by deed", "দলিলে কেনা জমি"
            else:
                basis_en, basis_bn = "share in the record of rights", "খতিয়ানে রেকর্ডভুক্ত অংশ"
            self._add("OVER_SELLING", share=_acre(remaining), area=_acre(self.area),
                      basis=basis_en, basis_bn=basis_bn)

        # Minors
        if person and person.is_minor:
            self._add("MINOR_INTEREST", who=f"The seller ({person.name_en})", who_bn=f"বিক্রেতা ({person.name_bn})")
        elif remaining is not None and self.area > remaining + AREA_TOLERANCE:
            minors = [p for p in co_sharers if p.is_minor]
            if minors:
                self._add("MINOR_INTEREST", who=f"Co-sharer {_names(minors)}", who_bn=f"শরিক {_names(minors, 'bn')}")

        if co_sharers and role in ("owner", "heir", "attorney"):
            self._add("PRE_EMPTION", names=_names(co_sharers), names_bn=_names(co_sharers, "bn"))

        self._legal_status_rules()
        self._encumbrance_rules()
        lineage = self._lineage_rule()
        self._transaction_pattern_rules()
        self._anomaly_rule(person, role)
        self._tax_rule()
        self._khatian_input_rule()
        self._document_rule()
        self._intent_rule()

        rendered = sorted((f.render() for f in self.flags), key=lambda f: -f["points"])
        total = min(sum(f["points"] for f in rendered), 100)
        level = next(lvl for upper, lvl in LEVEL_BANDS if total <= upper)
        if any(f["tier"] == CRITICAL for f in rendered):
            level = "HIGH"

        return {
            "plot": self._plot_info(),
            "input": {
                "seller_name": self.seller_name, "area_acre": _acre(self.area),
                "khatian_no": self.khatian_no,
            },
            "seller": {
                "matched": bool(person),
                "match_score": score,
                "name": {"en": person.name_en, "bn": person.name_bn} if person else {"en": self.seller_name, "bn": self.seller_name},
                "role": role,
                "sellable_area_acre": None if remaining is None else _acre(remaining),
                "prior_sold_acre": _acre(prior_sold),
            },
            "record_of_rights": self._record_info(),
            "flags": rendered,
            "score": total,
            "level": level,
            "inheritance": inheritance,
            "lineage": lineage,
            "timeline": self._timeline(),
            "notes": self.notes,
            "ml_check": self.ml_check,
            "document_check": self.document_check,
            **guidance.build(rendered, role, level),
        }

    def _legal_status_rules(self):
        active = list(self.plot.legal_statuses.filter(is_active=True))
        restricted = [s for s in active if s.status_type in RESTRICTED_KINDS]
        if restricted:
            kinds = [RESTRICTED_KINDS[s.status_type] for s in restricted]
            self._add(
                "RESTRICTED_LAND", evidence=[f"{s.reference_no}: {s.description}" for s in restricted],
                kinds=", ".join(k[0] for k in kinds), kinds_bn=", ".join(k[1] for k in kinds),
                law="; ".join(sorted({k[2] for k in kinds})), refs=", ".join(s.reference_no for s in restricted),
            )
        acq = [s for s in active if s.status_type == "acquisition"]
        if acq:
            self._add("ACQUISITION", evidence=[f"{s.reference_no}: {s.description}" for s in acq],
                      refs=", ".join(s.reference_no for s in acq))
        inj = [s for s in active if s.status_type == "injunction"]
        if inj:
            self._add("TRANSFER_INJUNCTION", evidence=[f"{s.reference_no}: {s.description}" for s in inj],
                      refs=", ".join(s.reference_no for s in inj))
        lit = [s for s in active if s.status_type in LITIGATION_KINDS]
        if lit:
            self._add("LITIGATION", evidence=[f"{s.reference_no}: {s.description}" for s in lit],
                      refs=", ".join(s.reference_no for s in lit))

    def _encumbrance_rules(self):
        for mg in self.plot.mortgages.filter(is_active=True):
            self._add("MORTGAGE", evidence=[f"Registered {mg.registered_on}, mortgagor {mg.mortgagor.name_en}"],
                      lender=mg.lender, amount=f"{mg.amount_bdt:,}")
        for bn in self.plot.bainanamas.filter(status=m.Bainanama.Status.ACTIVE).select_related("seller", "buyer"):
            self._add("PRIOR_BAINANAMA", seller=bn.seller.name_en, buyer=bn.buyer.name_en, ref=bn.agreement_no,
                      date=bn.agreement_date.isoformat(), area=_acre(bn.area_acre))

    def _lineage_rule(self):
        lineage = []
        prev = None
        for k in self.khatians:
            owners = [ko.person for ko in k.owners.all()]
            explained = True
            if prev is not None:
                prev_owners = [ko.person for ko in prev.owners.all()]
                ok = self._expand_entitled({p.id for p in prev_owners})
                unexplained = [p for p in owners if p.id not in ok and not p.is_government]
                if unexplained:
                    explained = False
                    self._add(
                        "TITLE_CHAIN_BREAK",
                        evidence=[f"{prev.survey} {prev.khatian_no}: {_names(prev_owners)}", f"{k.survey} {k.khatian_no}: {_names(owners)}"],
                        from_survey=prev.survey, to_survey=k.survey,
                        from_owners=_names(prev_owners), from_owners_bn=_names(prev_owners, "bn"),
                        owners=_names(unexplained), owners_bn=_names(unexplained, "bn"),
                    )
            lineage.append({
                "survey": k.survey, "khatian_no": k.khatian_no, "record_year": k.record_year,
                "owners": [{"en": ko.person.name_en, "bn": ko.person.name_bn, "share": _acre(ko.share)} for ko in k.owners.all()],
                "consistent": explained,
            })
            prev = k
        return lineage

    def _transaction_pattern_rules(self):
        seed = {ko.person_id for k in self.khatians for ko in k.owners.all()}
        entitled = self._expand_entitled(seed)
        conflicting = [d for d in self.deeds if not ({p.id for p in d.sellers.all()} & entitled)]
        if conflicting:
            self._add("CONFLICTING_TRANSACTIONS",
                      evidence=[f"Deed {d.deed_no}: {_names(d.sellers.all())} -> {_names(d.buyers.all())}" for d in conflicting],
                      deeds=", ".join(d.deed_no for d in conflicting))

        sales = [d for d in self.deeds if d.deed_type == m.Deed.DeedType.SALE]
        for i in range(len(sales) - RAPID_MIN_SALES + 1):
            window = sales[i:i + RAPID_MIN_SALES]
            days = (window[-1].registration_date - window[0].registration_date).days
            if days <= RAPID_WINDOW_DAYS:
                self._add("RAPID_TRANSFERS", count=len(window), days=days,
                          deeds=", ".join(d.deed_no for d in window))
                break

        cutoff = timezone.localdate().year - LOW_PRICE_LOOKBACK_YEARS
        rate = Decimal(self.plot.mouza_rate_per_acre)
        low = [d for d in sales if d.registration_date.year >= cutoff
               and Decimal(d.price_bdt) < LOW_PRICE_RATIO * rate * d.area_acre]
        if low:
            self._add("PRICE_BELOW_RATE",
                      evidence=[f"Deed {d.deed_no}: BDT {d.price_bdt:,} vs mouza value BDT {int(rate * d.area_acre):,}" for d in low],
                      deeds=", ".join(d.deed_no for d in low))

    def _anomaly_rule(self, person, role):
        today = timezone.localdate()
        cutoff = today - timedelta(days=365 * LOW_PRICE_LOOKBACK_YEARS)
        transfers = [deed_transfer(d) for d in self.deeds
                     if d.deed_type == m.Deed.DeedType.SALE and d.registration_date >= cutoff]
        if person and role in ("owner", "heir", "deed_buyer"):
            transfers.append(proposed_transfer(person, self.plot, self.area, today))
        unusual = sorted((r for r in anomaly_model.score(transfers) if r["is_anomaly"]), key=lambda r: r["score"])
        self.ml_check.update(checked=len(transfers), unusual=len(unusual))
        if not unusual:
            return

        def describe(r, lang):
            reasons = "; ".join(x[lang] for x in r["reasons"])
            return reasons or ("several factors together" if lang == "en" else "কয়েকটি বিষয় একসাথে")

        evidence = [f"{r['transfer'].label}: {describe(r, 'en')} (anomaly score {r['score']})" for r in unusual]
        rule_flags = [f for f in self.flags if f.code in ("RAPID_TRANSFERS", "PRICE_BELOW_RATE")]
        if rule_flags:
            # The rules already explain this pattern; the model only adds supporting evidence.
            for f in rule_flags:
                f.evidence.extend(f"ML model also marks as unusual: {line}" for line in evidence)
            return

        top = unusual[0]["transfer"]
        is_proposed = top.label == "Proposed sale"
        self._add(
            "TRANSFER_ANOMALY", evidence=evidence,
            label="proposed sale" if is_proposed else top.label.lower(),
            label_bn="প্রস্তাবিত বিক্রি" if is_proposed else top.label.replace("Deed", "দলিল"),
            reasons=describe(unusual[0], "en"), reasons_bn=describe(unusual[0], "bn"),
        )

    def _tax_rule(self):
        tax = getattr(self.plot, "tax_record", None)
        if tax and tax.arrears_bdt > 0:
            self._add("TAX_ARREARS", year=tax.paid_upto_year, amount=f"{tax.arrears_bdt:,}")

    def _khatian_input_rule(self):
        if not self.khatian_no:
            return
        known = [k for k in self.khatians]
        if not any(k.khatian_no == self.khatian_no for k in known):
            self._add("KHATIAN_MISMATCH", given=self.khatian_no, dag=self.plot.dag_no,
                      known=", ".join(f"{k.survey} {k.khatian_no}" for k in known))
        elif self.latest and self.khatian_no != self.latest.khatian_no:
            old = next(k for k in known if k.khatian_no == self.khatian_no)
            self.notes.append({
                "en": f"You entered {old.survey} khatian {old.khatian_no}. The latest record is {self.latest.survey} khatian {self.latest.khatian_no}.",
                "bn": f"আপনি {old.survey} খতিয়ান {bn_num(old.khatian_no)} দিয়েছেন। সর্বশেষ রেকর্ড {self.latest.survey} খতিয়ান {bn_num(self.latest.khatian_no)}।",
            })

    def _document_rule(self):
        if not self.documents:
            return
        self.document_check = check_documents(self.plot.mouza_id, self.documents, self.plot.dag_no)
        problems = [c for d in self.document_check["documents"] for c in d["checks"] if c["severity"] == "critical"]
        if problems:
            self._add(
                "DOCUMENT_MISMATCH", evidence=[c["en"] for c in problems], count=len(problems),
                details=" ".join(c["en"] for c in problems), details_bn=" ".join(c["bn"] for c in problems),
            )

    def _intent_rule(self):
        since = timezone.now() - timedelta(days=INTENT_WINDOW_DAYS)
        others = (self.plot.purchase_intents.filter(created_at__gte=since)
                  .exclude(buyer_token=self.buyer_token).values("buyer_token").distinct().count())
        if others:
            self._add("CONCURRENT_INTEREST", count=others)
        if self.buyer_token:
            m.PurchaseIntent.objects.get_or_create(plot=self.plot, buyer_token=self.buyer_token)

    # ------------------------------------------------------------------ output
    def _plot_info(self):
        p = self.plot
        mz = p.mouza
        return {
            "id": p.id, "dag_no": p.dag_no, "area_acre": _acre(p.area_acre),
            "land_class": p.get_land_class_display(),
            "land_class_bn": LAND_CLASS_BN.get(p.land_class, p.get_land_class_display()),
            "mouza_rate_per_acre": p.mouza_rate_per_acre,
            "mouza": {"id": mz.id, "en": mz.name_en, "bn": mz.name_bn, "jl_no": mz.jl_no},
            "upazila": {"en": mz.upazila.name_en, "bn": mz.upazila.name_bn},
            "district": {"en": mz.upazila.district.name_en, "bn": mz.upazila.district.name_bn},
        }

    def _record_info(self):
        if not self.latest:
            return None
        mutation = (
            m.Mutation.objects.filter(resulting_khatian=self.latest).order_by("-application_date").first()
            if self.latest.survey == m.Khatian.Survey.NAMJARI else None
        )
        return {
            "survey": self.latest.survey, "khatian_no": self.latest.khatian_no,
            "record_year": self.latest.record_year,
            "mutation_case_no": mutation.case_no if mutation else None,
            "dag_no": self.plot.dag_no,
            "land_class": {"en": self.plot.get_land_class_display(),
                           "bn": LAND_CLASS_BN.get(self.plot.land_class, self.plot.get_land_class_display())},
            "plot_area_acre": _acre(self.plot.area_acre),
            "owners": [{
                "serial": i,
                "name": {"en": ko.person.name_en, "bn": ko.person.name_bn},
                "father": {"en": ko.person.father_name_en, "bn": ko.person.father_name_bn}
                if ko.person.father_name_en else None,
                "share": _acre(ko.share),
                "share_ana": share_to_ana(ko.share),
                "area_acre": _acre(ko.share * self.plot.area_acre),
                "is_deceased": ko.person.is_deceased, "is_minor": ko.person.is_minor,
                "is_government": ko.person.is_government,
                "death_year": ko.person.date_of_death.year if ko.person.date_of_death else None,
            } for i, ko in enumerate(self.latest_owners, start=1)],
        }

    def _timeline(self):
        seed = {ko.person_id for k in self.khatians for ko in k.owners.all()}
        entitled = self._expand_entitled(seed)
        events = []
        for k in self.khatians:
            events.append({
                "date": f"{k.record_year}-01-01", "year_only": True, "kind": "record", "status": "ok",
                "title": {"en": f"{k.get_survey_display()} — khatian {k.khatian_no}",
                          "bn": f"{k.survey} খতিয়ান {bn_num(k.khatian_no)}"},
                "detail": {"en": "Owners: " + _names([ko.person for ko in k.owners.all()]),
                           "bn": "মালিক: " + _names([ko.person for ko in k.owners.all()], "bn")},
            })
        people = {ko.person for k in self.khatians for ko in k.owners.all()}
        for person in people:
            if person.is_deceased and person.date_of_death:
                heirs = [l.heir for l in self._heirs_of(person.id)]
                events.append({
                    "date": person.date_of_death.isoformat(), "year_only": False, "kind": "inheritance", "status": "ok",
                    "title": {"en": f"Death of {person.name_en}", "bn": f"{person.name_bn}-এর মৃত্যু"},
                    "detail": {"en": "Heirs: " + _names(heirs), "bn": "ওয়ারিশ: " + _names(heirs, "bn")},
                })
        for d in self.deeds:
            ok = bool({p.id for p in d.sellers.all()} & entitled)
            events.append({
                "date": d.registration_date.isoformat(), "year_only": False, "kind": "deed",
                "status": "ok" if ok else "danger",
                "title": {"en": f"{d.get_deed_type_display()} deed {d.deed_no}", "bn": f"দলিল {d.deed_no}"},
                "detail": {
                    "en": f"{_names(d.sellers.all())} → {_names(d.buyers.all())}, {_acre(d.area_acre)} acre, BDT {d.price_bdt:,}",
                    "bn": f"{_names(d.sellers.all(), 'bn')} → {_names(d.buyers.all(), 'bn')}, {bn_num(_acre(d.area_acre))} একর, {bn_num(f'{d.price_bdt:,}')} টাকা",
                },
            })
        for mu in self.plot.mutations.select_related("new_owner"):
            events.append({
                "date": mu.application_date.isoformat(), "year_only": False, "kind": "mutation",
                "status": "ok" if mu.status == "approved" else "warning",
                "title": {"en": f"Mutation {mu.case_no} — {mu.status}", "bn": f"নামজারি {mu.case_no} — {mu.get_status_display()}"},
                "detail": {"en": f"In favour of {mu.new_owner.name_en}", "bn": f"{mu.new_owner.name_bn}-এর নামে"},
            })
        for s in self.plot.legal_statuses.all():
            events.append({
                "date": s.since.isoformat(), "year_only": False, "kind": "legal",
                "status": "danger" if s.is_active else "ok",
                "title": {"en": s.get_status_type_display(), "bn": s.get_status_type_display()},
                "detail": {"en": f"{s.reference_no} — {s.description}", "bn": f"{s.reference_no} — {s.description}"},
            })
        for mg in self.plot.mortgages.all():
            events.append({
                "date": mg.registered_on.isoformat(), "year_only": False, "kind": "mortgage",
                "status": "warning" if mg.is_active else "ok",
                "title": {"en": f"Mortgage to {mg.lender}", "bn": f"{mg.lender}-এ বন্ধক"},
                "detail": {"en": f"BDT {mg.amount_bdt:,}", "bn": f"{bn_num(f'{mg.amount_bdt:,}')} টাকা"},
            })
        for bn in self.plot.bainanamas.select_related("seller", "buyer"):
            events.append({
                "date": bn.agreement_date.isoformat(), "year_only": False, "kind": "agreement",
                "status": "warning" if bn.status == "active" else "ok",
                "title": {"en": f"Bainanama {bn.agreement_no}", "bn": f"বায়নানামা {bn.agreement_no}"},
                "detail": {"en": f"{bn.seller.name_en} → {bn.buyer.name_en}, {_acre(bn.area_acre)} acre",
                           "bn": f"{bn.seller.name_bn} → {bn.buyer.name_bn}, {bn_num(_acre(bn.area_acre))} একর"},
            })
        for poa in self.poas:
            events.append({
                "date": poa.executed_on.isoformat(), "year_only": False, "kind": "poa",
                "status": "danger" if poa.is_revoked else "ok",
                "title": {"en": f"Power of attorney {poa.poa_no}" + (" (revoked)" if poa.is_revoked else ""),
                          "bn": f"আমমোক্তারনামা {poa.poa_no}" + (" (বাতিল)" if poa.is_revoked else "")},
                "detail": {"en": f"{poa.principal.name_en} → {poa.attorney.name_en}",
                           "bn": f"{poa.principal.name_bn} → {poa.attorney.name_bn}"},
            })
        return sorted(events, key=lambda e: e["date"])


def find_plot(mouza_id: int, dag_no: str) -> m.Plot:
    try:
        return m.Plot.objects.select_related("mouza__upazila__district").get(mouza_id=mouza_id, dag_no=str(dag_no).strip())
    except m.Plot.DoesNotExist as exc:
        raise PlotNotFound(f"Dag {dag_no} not found in this mouza") from exc


def verify(mouza_id: int, dag_no: str, seller_name: str, area_acre, khatian_no: str = "", buyer_token: str = "",
           documents: list[dict] | None = None) -> dict:
    plot = find_plot(mouza_id, dag_no)
    return Verifier(plot, seller_name, Decimal(str(area_acre)), khatian_no, buyer_token, documents).run()
