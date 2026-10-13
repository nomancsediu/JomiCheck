import io
import json
import urllib.error
from unittest import mock

from django.test import SimpleTestCase, override_settings

from verification import assistant

RESULT = {
    "plot": {}, "seller": {}, "record_of_rights": None, "inheritance": None,
    "score": 6, "level": "LOW", "flags": [],
    "summary": {"en": "Low risk.", "bn": "কম ঝুঁকি।"},
}


def _reply(text):
    return io.BytesIO(json.dumps({"choices": [{"message": {"content": text}}]}).encode())


class AssistantTests(SimpleTestCase):
    @override_settings(LLM_API_URL="https://example.test/v1", LLM_API_KEY="k", LLM_MODEL="gemma-4-26b-it")
    def test_gemma_gets_instructions_in_user_turn(self):
        with mock.patch("urllib.request.urlopen", return_value=_reply("**নামজারি** হলো...")) as urlopen:
            out = assistant.answer("নামজারি কী?", RESULT, "bn")
        sent = json.loads(urlopen.call_args.args[0].data)
        self.assertEqual([m["role"] for m in sent["messages"]], ["user"])
        self.assertIn("Never invent records", sent["messages"][0]["content"])
        self.assertEqual(out, {"answer": "নামজারি হলো...", "source": "llm", "model": "gemma-4-26b-it"})

    @override_settings(LLM_API_URL="https://example.test/v1", LLM_API_KEY="k", LLM_MODEL="gemma-4-26b-a4b-it")
    def test_reasoning_is_removed(self):
        reply = "<thought>* Role: assistant? Yes. {draft}</thought>নামজারি হলো খতিয়ানে নাম তোলা।"
        with mock.patch("urllib.request.urlopen", return_value=_reply(reply)):
            out = assistant.answer("নামজারি কী?", RESULT, "bn")
        self.assertEqual(out["answer"], "নামজারি হলো খতিয়ানে নাম তোলা।")

    @override_settings(LLM_API_URL="https://example.test/v1", LLM_API_KEY="k", LLM_MODEL="gemma-4-26b-a4b-it")
    def test_overload_and_rate_limit_are_retried(self):
        overloaded = urllib.error.HTTPError("https://example.test", 503, "Unavailable", {}, io.BytesIO(b""))
        limited = urllib.error.HTTPError("https://example.test", 429, "Too Many", {}, io.BytesIO(b""))
        with mock.patch("urllib.request.urlopen", side_effect=[overloaded, limited, _reply("*সতর্কবার্তা: যাচাই করুন")]) as urlopen, \
                mock.patch("time.sleep") as sleep:
            out = assistant.answer("?", RESULT, "bn")
        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [2, 4])
        self.assertEqual(out["answer"], "সতর্কবার্তা: যাচাই করুন")

    @override_settings(LLM_API_URL="https://example.test/v1", LLM_API_KEY="k", LLM_MODEL="gemma-4-26b-a4b-it",
                       LLM_TIMEOUT=45)
    def test_retries_stay_within_the_time_budget(self):
        clock = iter([0, 0, 40])  # deadline set, first attempt starts, first attempt fails after 40 s
        timed_out = urllib.error.HTTPError("https://example.test", 504, "Deadline", {}, io.BytesIO(b""))
        with mock.patch("urllib.request.urlopen", side_effect=timed_out) as urlopen, \
                mock.patch("time.monotonic", side_effect=lambda: next(clock)), \
                mock.patch("time.sleep") as sleep, self.assertLogs(level="WARNING"):
            out = assistant.answer("?", RESULT, "bn")
        self.assertEqual(urlopen.call_count, 1)
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 45)
        sleep.assert_not_called()
        self.assertEqual(out["source"], "built-in")

    @override_settings(LLM_API_URL="https://example.test/v1", LLM_API_KEY="k", LLM_MODEL="gemma-4-26b-a4b-it")
    def test_bad_request_is_not_retried(self):
        bad = urllib.error.HTTPError("https://example.test", 400, "Bad Request", {}, io.BytesIO(b"bad"))
        with mock.patch("urllib.request.urlopen", side_effect=bad) as urlopen, self.assertLogs(level="WARNING"):
            out = assistant.answer("khatian?", RESULT, "en")
        self.assertEqual(urlopen.call_count, 1)
        self.assertEqual(out["source"], "built-in")

    @override_settings(LLM_API_URL="https://generativelanguage.googleapis.com/v1beta/openai", LLM_API_KEY="k",
                       LLM_MODEL="gemma-4-26b-a4b-it")
    def test_google_ai_studio_uses_sdk_with_image_first(self):
        with mock.patch("google.genai.Client") as client:
            client.return_value.models.generate_content.return_value.text = '{"khatian_no": "300"}'
            out = assistant.chat("Read it.", "Document:", image=(b"\xff\xd8jpeg", "image/jpeg"), json_output=True)
        call = client.return_value.models.generate_content.call_args.kwargs
        self.assertEqual(out, '{"khatian_no": "300"}')
        self.assertEqual(call["contents"][0].inline_data.mime_type, "image/jpeg")
        self.assertEqual(call["contents"][1], "Read it.\n\nDocument:")
        self.assertIsNone(call["config"].system_instruction)
        self.assertEqual(call["config"].response_mime_type, "application/json")
        self.assertEqual(call["config"].thinking_config.thinking_level.name, "MINIMAL")

    @override_settings(LLM_API_URL="https://example.test/v1", LLM_API_KEY="k", LLM_MODEL="other-model")
    def test_other_models_get_system_message(self):
        with mock.patch("urllib.request.urlopen", return_value=_reply("ok")) as urlopen:
            assistant.answer("What is mutation?", RESULT, "en")
        sent = json.loads(urlopen.call_args.args[0].data)
        self.assertEqual([m["role"] for m in sent["messages"]], ["system", "user"])

    @override_settings(LLM_API_URL="https://example.test/v1", LLM_API_KEY="k", LLM_MODEL="gemma-4-26b-it")
    def test_llm_failure_falls_back_to_built_in(self):
        with mock.patch("urllib.request.urlopen", side_effect=OSError("offline")), self.assertLogs(level="ERROR"):
            out = assistant.answer("What is mutation?", RESULT, "en")
        self.assertEqual(out["source"], "built-in")
        self.assertIn("Mutation", out["answer"])

    @override_settings(LLM_API_URL="", LLM_MODEL="")
    def test_without_llm_uses_built_in(self):
        self.assertEqual(assistant.answer("khatian?", RESULT, "en")["source"], "built-in")
