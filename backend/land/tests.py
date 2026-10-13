from decimal import Decimal
from fractions import Fraction

from django.test import SimpleTestCase

from .units import share_to_ana


class ShareToAnaTests(SimpleTestCase):
    def test_whole_and_half(self):
        self.assertEqual(share_to_ana(1)["en"], "16 ana")
        self.assertEqual(share_to_ana(Decimal("0.5"))["bn"], "৮ আনা")

    def test_eighth_is_two_ana(self):
        self.assertEqual(share_to_ana(Fraction(1, 8))["en"], "2 ana")

    def test_third_uses_smaller_units(self):
        r = share_to_ana(Fraction(1, 3))
        self.assertEqual(r["en"], "5 ana 6 gonda 2 kora 2 kranti")
        self.assertTrue(r["exact"])

    def test_stored_six_decimal_third_is_treated_as_exact(self):
        self.assertTrue(share_to_ana(Decimal("0.333333"))["exact"])

    def test_inexact_share_is_marked_approximate(self):
        r = share_to_ana(Fraction(1, 7))
        self.assertTrue(r["en"].startswith("≈ "))
        self.assertFalse(r["exact"])
