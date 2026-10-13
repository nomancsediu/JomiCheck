from django.test import TestCase
from rest_framework.test import APIClient

from land.models import Deed, Mouza
from land.seed import seed
from verification.engine import verify

from .crosscheck import check_documents


def khatian(no, owners, dag="118", area="1", survey="BS"):
    return {"document_type": "khatian", "survey": survey, "khatian_no": no,
            "owners": [{"name": n, "father_name": "", "share": s} for n, s in owners],
            "plots": [{"dag_no": dag, "land_class": "", "area_acre": area}]}


def deed(no, sellers, buyers, dag, area, when):
    return {"document_type": "deed", "plots": [{"dag_no": dag, "land_class": "", "area_acre": area}],
            "deed": {"deed_no": no, "registration_date": when, "sellers": sellers, "buyers": buyers}}


def receipt(holding, paid):
    return {"document_type": "tax_receipt", "tax_receipt": {"holding_no": holding, "paid_upto_year": paid}}


class CrossCheckTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.rampur = Mouza.objects.get(name_en="Rampur").id

    def statuses(self, docs, dag=None):
        return [d["status"] for d in check_documents(self.rampur, docs, dag)["documents"]]

    def test_genuine_khatian_matches(self):
        out = check_documents(self.rampur, [khatian("300", [("আব্দুল মজিদ", "১৬ আনা")])], "118")
        self.assertEqual(out["documents"][0]["status"], "ok")
        self.assertEqual(out["critical"], 0)

    def test_forged_owner_on_khatian(self):
        out = check_documents(self.rampur, [khatian("300", [("করিম মিয়া", "১৬ আনা")])], "118")
        self.assertEqual(out["documents"][0]["status"], "critical")
        self.assertTrue(any("করিম মিয়া" in c["bn"] for c in out["documents"][0]["checks"]))

    def test_unknown_khatian_and_wrong_share(self):
        self.assertEqual(self.statuses([khatian("999", [("আব্দুল মজিদ", "১৬ আনা")])]), ["critical"])
        self.assertEqual(self.statuses([khatian("300", [("আব্দুল মজিদ", "৮ আনা")])]), ["critical"])

    def test_deed_genuine_and_forged(self):
        real = Deed.objects.get(plot__dag_no="101", plot__mouza_id=self.rampur)
        ok = deed(real.deed_no, ["Nurul Islam"], ["জামাল হোসেন"], "101", "0.33", real.registration_date.isoformat())
        fake = deed("2024-09999", ["Abdul Karim"], ["Rahim Uddin"], "125", "0.30", "2024-03-02")
        wrong_buyer = deed(real.deed_no, ["Nurul Islam"], ["Rahim Uddin"], "101", "0.33", real.registration_date.isoformat())
        self.assertEqual(self.statuses([ok, fake, wrong_buyer]), ["ok", "critical", "critical"])

    def test_tax_receipt_paid_further_than_records(self):
        self.assertEqual(self.statuses([receipt("H-101-125", "2026"), receipt("H-101-101", "2025")]), ["critical", "ok"])
        self.assertEqual(self.statuses([receipt("H-999-1", "2026")]), ["critical"])

    def test_document_for_another_dag(self):
        self.assertEqual(self.statuses([receipt("H-101-101", "2025")], dag="118"), ["major"])

    def test_verification_adds_document_mismatch_flag(self):
        result = verify(self.rampur, "118", "Karim Mia", "0.40", "300",
                        documents=[khatian("300", [("করিম মিয়া", "১৬ আনা")])])
        codes = {f["code"] for f in result["flags"]}
        self.assertIn("DOCUMENT_MISMATCH", codes)
        self.assertEqual(result["level"], "HIGH")
        self.assertEqual(result["document_check"]["critical"], 2)  # fake owner added, real owner missing

    def test_check_endpoint(self):
        res = APIClient().post("/api/documents/check/", {
            "mouza_id": self.rampur, "dag_no": "118",
            "documents": [khatian("300", [("আব্দুল মজিদ", "১৬ আনা")])],
        }, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["documents"][0]["status"], "ok")
        self.assertEqual(APIClient().post("/api/documents/check/", {"mouza_id": 1}, format="json").status_code, 400)
