from fractions import Fraction as F

from django.test import SimpleTestCase

from verification.faraiz import Heir, calculate


def shares(result):
    return {s.key: s.share for s in result.shares}


class FaraizTests(SimpleTestCase):
    def test_wife_two_sons_one_daughter(self):
        r = calculate([
            Heir("w", "wife"), Heir("s1", "son"), Heir("s2", "son"), Heir("d", "daughter"),
        ])
        self.assertEqual(shares(r), {"w": F(1, 8), "s1": F(7, 20), "s2": F(7, 20), "d": F(7, 40)})

    def test_awl_husband_two_daughters_mother(self):
        r = calculate([
            Heir("h", "husband"), Heir("d1", "daughter"), Heir("d2", "daughter"), Heir("m", "mother"),
        ])
        self.assertEqual(shares(r), {"h": F(3, 13), "d1": F(4, 13), "d2": F(4, 13), "m": F(2, 13)})
        self.assertTrue(any("Awl" in n for n in r.notes))

    def test_radd_wife_and_one_daughter(self):
        r = calculate([Heir("w", "wife"), Heir("d", "daughter")])
        self.assertEqual(shares(r), {"w": F(1, 8), "d": F(7, 8)})

    def test_father_takes_fixed_plus_residue_with_daughter(self):
        r = calculate([Heir("d", "daughter"), Heir("f", "father")])
        self.assertEqual(shares(r), {"d": F(1, 2), "f": F(1, 2)})

    def test_umariyyatan(self):
        r = calculate([Heir("w", "wife"), Heir("f", "father"), Heir("m", "mother")])
        self.assertEqual(shares(r), {"w": F(1, 4), "m": F(1, 4), "f": F(1, 2)})

    def test_sons_only_split_equally(self):
        r = calculate([Heir("s1", "son"), Heir("s2", "son"), Heir("s3", "son")])
        self.assertEqual(set(shares(r).values()), {F(1, 3)})

    def test_rejects_unknown_relation(self):
        with self.assertRaises(ValueError):
            calculate([Heir("x", "brother")])
