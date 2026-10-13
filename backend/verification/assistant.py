"""
'Ask about this report' assistant.

With an OpenAI-compatible LLM configured (LLM_API_URL / LLM_API_KEY / LLM_MODEL),
answers are generated from the report facts only. Without one, a built-in
bilingual glossary and the report's own flags are used, so the feature works
offline.
"""

import json
import logging
import re
import time
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

RETRIES = 2
RETRY_DELAY = 2  # seconds; doubled on each retry

GLOSSARY = [
    {
        "keys": ["khatian", "porcha", "record of rights", "খতিয়ান", "পর্চা"],
        "en": "A khatian (record of rights) lists the owners of land in a mouza and each owner's share. Bangladesh has several survey generations (CS, SA, RS, BS); the latest one, or a mutation khatian, shows the current owner.",
        "bn": "খতিয়ান (স্বত্বের রেকর্ড) হলো মৌজার জমির মালিক ও তাঁদের অংশের তালিকা। বাংলাদেশে কয়েকটি জরিপ হয়েছে (সিএস, এসএ, আরএস, বিএস); সর্বশেষ খতিয়ান বা নামজারি খতিয়ানে বর্তমান মালিকের নাম থাকে।",
    },
    {
        "keys": ["mutation", "namjari", "dcr", "নামজারি", "জমাখারিজ", "ডিসিআর"],
        "en": "Mutation (namjari) updates the record of rights after a sale or inheritance. Under Registration Act s.52A, a seller's name should be in the latest record before a sale deed is registered.",
        "bn": "নামজারি হলো বিক্রি বা উত্তরাধিকারের পর খতিয়ানে নতুন মালিকের নাম তোলা। রেজিস্ট্রেশন আইনের ৫২ক ধারা অনুযায়ী বিক্রয় দলিল রেজিস্ট্রির আগে বিক্রেতার নাম সর্বশেষ রেকর্ডে থাকা উচিত।",
    },
    {
        "keys": ["dag", "plot", "দাগ"],
        "en": "A Dag is the plot number inside a mouza map. One khatian can include several Dags.",
        "bn": "দাগ হলো মৌজা ম্যাপে জমির প্লট নম্বর। একটি খতিয়ানে একাধিক দাগ থাকতে পারে।",
    },
    {
        "keys": ["shufa", "pre-emption", "preemption", "শুফা", "অগ্রক্রয়"],
        "en": "Pre-emption (Hak-e-Shufa, SAT Act s.96) lets a co-sharer ask the court to take over land sold to an outsider, by depositing the price plus compensation within the statutory period.",
        "bn": "অগ্রক্রয় (হক-শুফা, রাষ্ট্রীয় অধিগ্রহণ ও প্রজাস্বত্ব আইনের ৯৬ ধারা) অনুযায়ী বাইরের কাউকে জমি বিক্রি হলে শরিক নির্দিষ্ট সময়ের মধ্যে দাম ও ক্ষতিপূরণ জমা দিয়ে আদালতের মাধ্যমে জমিটি নিতে পারেন।",
    },
    {
        "keys": ["faraiz", "inheritance", "heir", "warish", "ফারায়েজ", "ওয়ারিশ", "উত্তরাধিকার"],
        "en": "Under Muslim Faraiz, a wife gets 1/8 if there are children, and sons take twice a daughter's share from the remainder. An heir can sell only his own share unless the other heirs join.",
        "bn": "মুসলিম ফারায়েজ অনুযায়ী সন্তান থাকলে স্ত্রী পান ১/৮, আর বাকি অংশে ছেলে মেয়ের দ্বিগুণ পান। অন্য ওয়ারিশরা যুক্ত না হলে একজন ওয়ারিশ শুধু নিজের অংশই বিক্রি করতে পারেন।",
    },
    {
        "keys": ["khas", "খাস"],
        "en": "Khas land belongs to the government. It cannot be bought or sold privately; it can only be leased or settled by the government.",
        "bn": "খাস জমি সরকারের সম্পত্তি। এটি ব্যক্তিগতভাবে কেনাবেচা করা যায় না; শুধু সরকার ইজারা বা বন্দোবস্ত দিতে পারে।",
    },
    {
        "keys": ["vested", "orpito", "অর্পিত"],
        "en": "Vested property (orpito sompotti) is governed by the Vested Property Return Act 2001 and cannot be sold freely.",
        "bn": "অর্পিত সম্পত্তি অর্পিত সম্পত্তি প্রত্যর্পণ আইন ২০০১ দ্বারা নিয়ন্ত্রিত এবং অবাধে বিক্রি করা যায় না।",
    },
    {
        "keys": ["bainanama", "agreement", "বায়না", "বায়নানামা"],
        "en": "A bainanama is an agreement for sale. It must be registered (Registration Act s.17A). An earlier buyer with a bainanama can sue to enforce it.",
        "bn": "বায়নানামা হলো বিক্রির চুক্তি। এটি নিবন্ধন করা বাধ্যতামূলক (রেজিস্ট্রেশন আইনের ১৭ক ধারা)। আগের বায়নাগ্রহীতা চুক্তি বাস্তবায়নের মামলা করতে পারেন।",
    },
    {
        "keys": ["tax", "dakhila", "khajna", "দাখিলা", "খাজনা", "কর"],
        "en": "Land development tax is paid yearly; the receipt (dakhila) is needed for mutation and registration.",
        "bn": "ভূমি উন্নয়ন কর প্রতি বছর দিতে হয়; নামজারি ও রেজিস্ট্রির জন্য দাখিলা লাগে।",
    },
    {
        "keys": ["power of attorney", "poa", "attorney", "আমমোক্তার"],
        "en": "A power of attorney for sale must be registered (Power of Attorney Act 2012). It ends if revoked or if the owner dies.",
        "bn": "বিক্রির আমমোক্তারনামা নিবন্ধিত হতে হয় (পাওয়ার অব অ্যাটর্নি আইন ২০১২)। বাতিল হলে বা মালিক মারা গেলে এটি অকার্যকর হয়।",
    },
    {
        "keys": ["injunction", "case", "suit", "court", "মামলা", "নিষেধাজ্ঞা", "আদালত"],
        "en": "If a suit is pending, the buyer is bound by the result. If the court has issued an injunction, a sale during it can be set aside.",
        "bn": "মামলা চলমান থাকলে রায় ক্রেতার ওপরও প্রযোজ্য হয়। আদালতের নিষেধাজ্ঞা থাকলে সেই সময়ের বিক্রি বাতিল হতে পারে।",
    },
    {
        "keys": ["mortgage", "loan", "bank", "বন্ধক", "ঋণ", "ব্যাংক"],
        "en": "A mortgage stays attached to the land after sale. Buy only after the lender issues a release letter.",
        "bn": "বিক্রির পরও বন্ধক জমির সাথে থাকে। ঋণদাতার দায়মুক্তি পত্র পাওয়ার পরই কিনুন।",
    },
]

RISK_WORDS = ["risk", "why", "safe", "problem", "buy", "ঝুঁকি", "কেন", "নিরাপদ", "সমস্যা", "কিনব", "কিনতে"]


def _fallback(question: str, result: dict, lang: str) -> str:
    q = question.lower()
    parts = []

    for flag in result.get("flags", []):
        words = [w for w in (flag["title"]["en"] + " " + flag["code"]).lower().replace("_", " ").split() if len(w) > 4]
        if any(w in q for w in words) or flag["title"]["bn"] in question:
            parts.append(f"{flag['title'][lang]}: {flag['explanation'][lang]} ({flag['law']})")

    for entry in GLOSSARY:
        if any(k in q for k in entry["keys"]):
            parts.append(entry[lang])

    if not parts or any(w in q for w in RISK_WORDS):
        level = result.get("level")
        score = result.get("score")
        head = (f"Risk level: {level} ({score}/100). " if lang == "en" else f"ঝুঁকির মাত্রা: {level} ({score}/১০০)। ")
        parts.insert(0, head + result["summary"][lang])
        for flag in result.get("flags", [])[:3]:
            line = f"• {flag['title'][lang]} — {flag['action'][lang]}"
            if line not in parts:
                parts.append(line)

    disclaimer = ("This is decision support, not legal advice. Confirm with the land office and a lawyer."
                  if lang == "en" else "এটি সিদ্ধান্ত গ্রহণে সহায়তা, আইনি পরামর্শ নয়। ভূমি অফিস ও আইনজীবীর মাধ্যমে নিশ্চিত হন।")
    return "\n\n".join(dict.fromkeys(parts)) + "\n\n" + disclaimer


def _compact_facts(result: dict) -> dict:
    return {
        "plot": result["plot"],
        "seller": result["seller"],
        "record_of_rights": result["record_of_rights"],
        "score": result["score"],
        "level": result["level"],
        "flags": [{k: f[k] for k in ("code", "tier", "law", "title", "explanation", "action")} for f in result["flags"]],
        "inheritance": result.get("inheritance"),
    }


def _llm(question: str, result: dict, lang: str) -> str:
    language = "Bangla" if lang == "bn" else "English"
    system = (
        "You are a careful Bangladeshi land-law assistant inside the JomiCheck pre-purchase verification tool. "
        f"Answer in simple {language}, in at most 150 words. Use ONLY the facts in the provided report JSON and "
        "general land-law knowledge. Never invent records, names or case numbers. Always end by reminding the user "
        "that this is decision support and official verification at the land office and a lawyer's advice are needed."
    )
    user = f"Report JSON:\n{json.dumps(_compact_facts(result), ensure_ascii=False)}\n\nQuestion: {question}"
    return _plain_text(chat(system, user))


def _plain_text(text: str) -> str:
    """The chat panel shows plain text, so drop markdown emphasis and turn list markers into bullets."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"^\s*[*-]\s+", "• ", text, flags=re.MULTILINE)
    text = text.replace("*", "")
    return re.sub(r"^#+\s*", "", text, flags=re.MULTILINE).strip()


def llm_configured() -> bool:
    return bool(settings.LLM_API_URL and settings.LLM_MODEL)


def chat(system: str, user: str, image_data_url: str | None = None, temperature: float = 0.2,
         timeout: int | None = None) -> str:
    """Call the configured OpenAI-compatible chat endpoint and return the reply text."""
    if settings.LLM_MODEL.lower().startswith("gemma"):
        # Gemma on the Gemini API rejects system instructions, so they go in the user turn.
        messages = [{"role": "user", "content": f"{system}\n\n{user}"}]
    else:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    if image_data_url:
        messages[-1]["content"] = [
            {"type": "text", "text": messages[-1]["content"]},
            {"type": "image_url", "image_url": {"url": image_data_url}},
        ]
    body = json.dumps({"model": settings.LLM_MODEL, "temperature": temperature, "messages": messages}).encode("utf-8")
    req = urllib.request.Request(
        settings.LLM_API_URL.rstrip("/") + "/chat/completions", data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {settings.LLM_API_KEY}"},
    )
    for attempt in range(RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout or settings.LLM_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            # The hosted API often answers "overloaded" (503) or "rate limited" (429) for a few seconds.
            if (exc.code != 429 and exc.code < 500) or attempt == RETRIES:
                logger.warning("LLM HTTP %s: %s", exc.code, exc.read()[:300])
                raise
            time.sleep(RETRY_DELAY * 2 ** attempt)
    return strip_reasoning(data["choices"][0]["message"]["content"])


def strip_reasoning(text: str) -> str:
    """Gemma 4 can prepend its reasoning, closed by </thought> (or </think>); keep only the final answer."""
    return re.split(r"</(?:thought|think)>", text)[-1].strip()


def answer(question: str, result: dict, lang: str = "bn") -> dict:
    lang = "en" if lang == "en" else "bn"
    if llm_configured():
        try:
            return {"answer": _llm(question, result, lang), "source": "llm", "model": settings.LLM_MODEL}
        except Exception:  # network/LLM failure must not break the report
            logger.exception("LLM call failed; using built-in assistant")
    return {"answer": _fallback(question, result, lang), "source": "built-in", "model": None}
