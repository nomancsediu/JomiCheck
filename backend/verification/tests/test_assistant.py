import io
import json
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
