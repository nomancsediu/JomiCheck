from django.test import TestCase

from land.models import Mouza
from land.seed import DEMO_CASES, seed
from verification.engine import PlotNotFound, verify

EXPECTED = {
    "clean": ("LOW", 6, {"TAX_ARREARS"}),
    "rahim_fraud": ("HIGH", 91, {"OWNERSHIP_MISMATCH", "DOUBLE_SELLING", "CONFLICTING_TRANSACTIONS", "TAX_ARREARS"}),
    "inheritance_oversell": ("MEDIUM", 55, {"OVER_SELLING", "MUTATION_MISSING", "PRE_EMPTION"}),
    "mutation_missing": ("MEDIUM", 34, {"MUTATION_MISSING", "PRICE_BELOW_RATE", "TAX_ARREARS"}),
    "khas_land": ("HIGH", 80, {"OWNERSHIP_MISMATCH", "RESTRICTED_LAND"}),
    "acquisition": ("HIGH", 40, {"ACQUISITION"}),
    "litigation": ("HIGH", 70, {"TRANSFER_INJUNCTION", "LITIGATION"}),
    "mortgage": ("MEDIUM", 31, {"MORTGAGE", "TAX_ARREARS"}),
    "revoked_poa": ("HIGH", 35, {"POA_INVALID"}),
    "bainanama": ("MEDIUM", 36, {"PRIOR_BAINANAMA", "PRE_EMPTION", "TAX_ARREARS"}),
    "survey_conflict": ("MEDIUM", 36, {"TITLE_CHAIN_BREAK", "TAX_ARREARS"}),
    "rapid_transfers": ("MEDIUM", 33, {"RAPID_TRANSFERS", "PRICE_BELOW_RATE"}),
    "minor_heir": ("HIGH", 80, {"OVER_SELLING", "MINOR_INTEREST", "MUTATION_MISSING", "PRE_EMPTION"}),
    "ml_broker": ("LOW", 20, {"TRANSFER_ANOMALY"}),
}


def run_case(case, **overrides):
    params = {**case, **overrides}
    mouza = Mouza.objects.get(name_en=params["mouza"])
    return verify(mouza.id, params["dag_no"], params["seller_name"], params["area_acre"], params["khatian_no"],
                  params.get("buyer_token", ""))


class DemoScenarioTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

    def test_every_demo_case_matches_expected_risk(self):
        self.assertEqual(set(EXPECTED), {c["key"] for c in DEMO_CASES})
        for case in DEMO_CASES:
            level, score, codes = EXPECTED[case["key"]]
            with self.subTest(case=case["key"]):
                result = run_case(case)
                self.assertEqual(result["level"], level)
                self.assertEqual(result["score"], score)
                self.assertEqual({f["code"] for f in result["flags"]}, codes)

    def test_inheritance_shares_for_heir(self):
        case = next(c for c in DEMO_CASES if c["key"] == "inheritance_oversell")
        result = run_case(case)
        shares = {h["name"]["en"]: h["share"] for h in result["inheritance"]["heirs"]}
        self.assertEqual(shares, {"Fatema Begum": "1/8", "Karim Mia": "7/20", "Hasan Mia": "7/20", "Rokeya Begum": "7/40"})
        self.assertEqual(result["seller"]["sellable_area_acre"], "0.35")

    def test_heir_buying_within_share_is_not_over_selling(self):
        case = next(c for c in DEMO_CASES if c["key"] == "inheritance_oversell")
        codes = {f["code"] for f in run_case(case, area_acre="0.30")["flags"]}
        self.assertNotIn("OVER_SELLING", codes)

    def test_bangla_seller_name_matches(self):
        case = next(c for c in DEMO_CASES if c["key"] == "clean")
        result = run_case(case, seller_name="মোঃ জামাল হোসেন")
        self.assertEqual(result["seller"]["role"], "owner")

    def test_record_of_rights_has_khatian_columns(self):
        case = next(c for c in DEMO_CASES if c["key"] == "clean")
        ror = run_case(case)["record_of_rights"]
        self.assertEqual(ror["survey"], "NAMJARI")
        self.assertTrue(ror["mutation_case_no"])
        self.assertEqual(ror["dag_no"], case["dag_no"])
        owner = ror["owners"][0]
        self.assertEqual(owner["serial"], 1)
        self.assertEqual(owner["father"]["en"], "Kashem Hossain")
        self.assertEqual(owner["share_ana"]["en"], "16 ana")

    def test_wrong_khatian_number_is_flagged(self):
        case = next(c for c in DEMO_CASES if c["key"] == "clean")
        codes = {f["code"] for f in run_case(case, khatian_no="9999")["flags"]}
        self.assertIn("KHATIAN_MISMATCH", codes)

    def test_old_survey_khatian_gives_note_not_flag(self):
        case = next(c for c in DEMO_CASES if c["key"] == "clean")
        result = run_case(case, khatian_no="88")
        self.assertNotIn("KHATIAN_MISMATCH", {f["code"] for f in result["flags"]})
        self.assertTrue(result["notes"])

    def test_ml_check_summary(self):
        clean = run_case(next(c for c in DEMO_CASES if c["key"] == "clean"))["ml_check"]
        self.assertGreaterEqual(clean["checked"], 1)
        self.assertEqual(clean["unusual"], 0)
        broker = run_case(next(c for c in DEMO_CASES if c["key"] == "ml_broker"))["ml_check"]
        self.assertGreaterEqual(broker["unusual"], 1)

    def test_concurrent_buyer_interest(self):
        case = next(c for c in DEMO_CASES if c["key"] == "clean")
        run_case(case, buyer_token="buyer-a")
        codes = {f["code"] for f in run_case(case, buyer_token="buyer-b")["flags"]}
        self.assertIn("CONCURRENT_INTEREST", codes)

    def test_unknown_plot(self):
        mouza = Mouza.objects.first()
        with self.assertRaises(PlotNotFound):
            verify(mouza.id, "99999", "Anyone", "0.1")

    def test_every_flag_has_law_and_bangla_text(self):
        for case in DEMO_CASES:
            for flag in run_case(case)["flags"]:
                with self.subTest(case=case["key"], flag=flag["code"]):
                    self.assertTrue(flag["law"])
                    self.assertNotIn("{", flag["explanation"]["bn"])
                    self.assertNotIn("{", flag["explanation"]["en"])
