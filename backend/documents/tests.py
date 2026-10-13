import io
import json
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from land.seed import seed

from .extract import _to_acre, parse_json

LLM = dict(LLM_API_URL="https://example.test/v1", LLM_API_KEY="k", LLM_MODEL="gemma-4-26b-it")

MODEL_REPLY = {
    "document_type": "mutation_khatian", "survey": "NAMJARI",
    "district": "ঢাকা", "upazila": "সাভার", "mouza": "রামপুর", "jl_no": "১০১",
    "khatian_no": "১০২১", "mutation_case_no": "NJ-2015-0001",
    "owners": [{"name": "জামাল হোসেন", "father_name": "কাশেম হোসেন", "share": "১৬ আনা"}],
    "plots": [{"dag_no": "১০১", "land_class": "ভিটি", "area": "৩৩", "area_unit": "decimal"}],
    "warnings": [],
}


def _png() -> SimpleUploadedFile:
    buf = io.BytesIO()
    Image.new("RGB", (40, 30), "white").save(buf, format="PNG")
    return SimpleUploadedFile("khatian.png", buf.getvalue(), content_type="image/png")


class ParseJsonTests(TestCase):
    def test_strips_code_fences(self):
        self.assertEqual(parse_json('```json\n{"a": 1}\n```'), {"a": 1})

    def test_bangla_area_units(self):
        self.assertEqual(_to_acre("৩৩", "শতাংশ"), "0.33")
        self.assertEqual(_to_acre("৩৩", "শতংশ"), "0.33")
        self.assertEqual(_to_acre("1.5", "একর"), "1.5")
        self.assertEqual(_to_acre("2", None), "2")
        self.assertEqual(_to_acre("৩৩ শতাংশ", "decimal"), "0.33")
        self.assertEqual(_to_acre("10 katha", None), "0.1653")
        self.assertIsNone(_to_acre("unclear", "acre"))
        self.assertEqual(_to_acre("0.30", "decimal"), "0.3")


@override_settings(**LLM)
class ExtractApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

    def post(self, file):
        return APIClient().post("/api/documents/extract/", {"file": file}, format="multipart")

    def test_extracts_and_matches_mouza_and_dag(self):
        with mock.patch("documents.extract.chat", return_value=json.dumps(MODEL_REPLY, ensure_ascii=False)) as chat:
            res = self.post(_png())
        self.assertEqual(res.status_code, 200)
        image, mime = chat.call_args.kwargs["image"]
        self.assertEqual((image[:2], mime), (b"\xff\xd8", "image/jpeg"))
        self.assertTrue(chat.call_args.kwargs["json_output"])
        body = res.json()
        self.assertEqual(body["fields"]["khatian_no"], "1021")
        self.assertEqual(body["fields"]["plots"][0], {"dag_no": "101", "land_class": "ভিটি", "area_acre": "0.33", "found": True})
        self.assertEqual(body["location"]["mouza"]["en"], "Rampur")

    def test_rejects_unsupported_file(self):
        res = self.post(SimpleUploadedFile("notes.txt", b"hello", content_type="text/plain"))
        self.assertEqual(res.status_code, 422)
        self.assertIn("detail_bn", res.json())

    def test_model_failure_returns_502(self):
        with mock.patch("documents.extract.chat", side_effect=OSError("down")), self.assertLogs(level="ERROR"):
            self.assertEqual(self.post(_png()).status_code, 502)

    @override_settings(LLM_API_URL="", LLM_MODEL="")
    def test_needs_llm(self):
        self.assertEqual(self.post(_png()).status_code, 503)
