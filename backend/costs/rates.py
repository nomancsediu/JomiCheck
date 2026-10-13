"""Indicative purchase-cost rates for a sale (saf-kobla) deed.

Compiled by the team from public sources in October 2026. Rates change through
finance acts and gazettes, so every estimate tells the user to confirm them at
the sub-registry office before paying.
"""
from decimal import Decimal

RATES_AS_OF = "2026-10"

STAMP_DUTY = Decimal("3")
REGISTRATION_FEE = Decimal("1")

AREA_TYPES = {
    "city_major": {
        "label": {"en": "Dhaka, Gazipur, Narayanganj or Chattogram City Corporation",
                  "bn": "ঢাকা, গাজীপুর, নারায়ণগঞ্জ বা চট্টগ্রাম সিটি কর্পোরেশন"},
        "local_gov_tax": Decimal("3"),
        "source_tax": Decimal("4"),
    },
    "city_other": {
        "label": {"en": "Other City Corporation", "bn": "অন্যান্য সিটি কর্পোরেশন"},
        "local_gov_tax": Decimal("3"),
        "source_tax": Decimal("3"),
    },
    "pourashava": {
        "label": {"en": "Pourashava (municipality)", "bn": "পৌরসভা"},
        "local_gov_tax": Decimal("2"),
        "source_tax": Decimal("2"),
    },
    "union": {
        "label": {"en": "Union Parishad", "bn": "ইউনিয়ন পরিষদ"},
        "local_gov_tax": Decimal("1"),
        "source_tax": Decimal("2"),
    },
}

MUTATION_FEES = [
    ("application", {"en": "Online application fee", "bn": "অনলাইন আবেদন ফি"}, 50),
    ("notice", {"en": "Notice service fee", "bn": "নোটিশ জারি ফি"}, 50),
    ("record_correction", {"en": "Record correction fee", "bn": "রেকর্ড সংশোধন ফি"}, 1000),
    ("khatian_copy", {"en": "Mutation khatian copy", "bn": "মিউটেশন খতিয়ান কপি"}, 100),
]
