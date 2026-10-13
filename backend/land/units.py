"""Traditional khatian share notation.

A whole holding is 16 ana; 1 ana = 20 gonda, 1 gonda = 4 kora, 1 kora = 3 kranti,
so one whole is 3840 kranti.
"""
from decimal import Decimal
from fractions import Fraction

KRANTI_PER_WHOLE = 3840
_UNITS = (
    ("ana", "আনা", 240),
    ("gonda", "গণ্ডা", 12),
    ("kora", "কড়া", 3),
    ("kranti", "ক্রান্তি", 1),
)
_BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


def share_to_ana(share) -> dict:
    """Express a share (0..1) in ana-gonda-kora-kranti, rounded to the nearest kranti."""
    value = Fraction(str(share)) if isinstance(share, (Decimal, str, float)) else Fraction(share)
    exact_units = value * KRANTI_PER_WHOLE
    total = round(exact_units)
    exact = abs(exact_units - total) < Fraction(1, 100)

    parts_en, parts_bn = [], []
    remaining = total
    for en, bn, size in _UNITS:
        count, remaining = divmod(remaining, size)
        if count:
            parts_en.append(f"{count} {en}")
            parts_bn.append(f"{str(count).translate(_BN_DIGITS)} {bn}")

    en = " ".join(parts_en) or "0 ana"
    bn = " ".join(parts_bn) or "০ আনা"
    if not exact:
        en, bn = f"≈ {en}", f"≈ {bn}"
    return {"en": en, "bn": bn, "exact": exact}
