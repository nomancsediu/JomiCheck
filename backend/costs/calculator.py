from decimal import ROUND_HALF_UP, Decimal

from . import rates


def _taka(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _bn(value) -> str:
    return str(value).translate(str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯"))


def estimate(price_bdt: int, area_type: str, area_acre: Decimal | None = None,
             mouza_rate_per_acre: int | None = None) -> dict:
    if area_type not in rates.AREA_TYPES:
        raise ValueError(f"Unknown area type: {area_type}")
    zone = rates.AREA_TYPES[area_type]
    price = Decimal(price_bdt)

    minimum = None
    if area_acre is not None and mouza_rate_per_acre:
        minimum = _taka(Decimal(area_acre) * Decimal(mouza_rate_per_acre))
    below_minimum = minimum is not None and price < minimum
    deed_value = Decimal(minimum) if below_minimum else price

    registration = []
    for key, label, pct in [
        ("stamp_duty", {"en": "Stamp duty", "bn": "স্ট্যাম্প শুল্ক"}, rates.STAMP_DUTY),
        ("registration_fee", {"en": "Registration fee", "bn": "রেজিস্ট্রেশন ফি"}, rates.REGISTRATION_FEE),
        ("local_gov_tax", {"en": "Local government tax", "bn": "স্থানীয় সরকার কর"}, zone["local_gov_tax"]),
        ("source_tax", {"en": "Source tax (income tax)", "bn": "উৎস কর (আয়কর)"}, zone["source_tax"]),
    ]:
        registration.append({
            "key": key, "label": label, "rate_percent": str(pct),
            "amount": _taka(deed_value * pct / 100),
        })
    mutation = [{"key": key, "label": label, "rate_percent": None, "amount": fee}
                for key, label, fee in rates.MUTATION_FEES]

    registration_total = sum(r["amount"] for r in registration)
    mutation_total = sum(r["amount"] for r in mutation)

    notes = [{
        "en": "VAT does not normally apply to land; it applies to flats and commercial property.",
        "bn": "সাধারণ জমিতে ভ্যাট প্রযোজ্য নয়; ফ্ল্যাট ও বাণিজ্যিক সম্পত্তিতে প্রযোজ্য।",
    }, {
        "en": f"Indicative rates as of {rates.RATES_AS_OF}. Confirm with the sub-registry office before paying.",
        "bn": f"{_bn(rates.RATES_AS_OF)} অনুযায়ী আনুমানিক হার। টাকা দেওয়ার আগে সাব-রেজিস্ট্রি অফিসে নিশ্চিত হোন।",
    }]
    if below_minimum:
        notes.insert(0, {
            "en": f"The price is below the government minimum value of Tk {minimum:,}. "
                  "Fees are charged on the minimum value, and an under-valued deed is a fraud warning sign.",
            "bn": f"দাম সরকার নির্ধারিত সর্বনিম্ন মূল্য {_bn(f'{minimum:,}')} টাকার কম। "
                  "ফি সর্বনিম্ন মূল্যের উপর ধরা হবে, আর কম দাম দেখানো দলিল প্রতারণার লক্ষণ হতে পারে।",
        })

    return {
        "price_bdt": price_bdt,
        "area_type": area_type,
        "area_type_label": zone["label"],
        "mouza_minimum_bdt": minimum,
        "below_minimum": below_minimum,
        "deed_value_bdt": _taka(deed_value),
        "registration": registration,
        "registration_total": registration_total,
        "mutation": mutation,
        "mutation_total": mutation_total,
        "fees_total": registration_total + mutation_total,
        "grand_total": _taka(price) + registration_total + mutation_total,
        "rates_as_of": rates.RATES_AS_OF,
        "notes": notes,
    }
