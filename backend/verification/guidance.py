"""Citizen guidance derived from the detected flags."""


def _t(en, bn):
    return {"en": en, "bn": bn}


BASE_DOCUMENTS = [
    _t("Certified copies of all khatians (CS, SA, RS, BS) for this Dag", "এই দাগের সকল খতিয়ানের (সিএস, এসএ, আরএস, বিএস) সার্টিফায়েড কপি"),
    _t("Seller's title deed and previous deeds (bia dolil) for at least 25 years", "বিক্রেতার মূল দলিল ও অন্তত ২৫ বছরের বায়া দলিল"),
    _t("Mutation (namjari) khatian and DCR in the seller's name", "বিক্রেতার নামে নামজারি খতিয়ান ও ডিসিআর"),
    _t("Latest land development tax receipt (dakhila)", "সর্বশেষ ভূমি উন্নয়ন কর পরিশোধের দাখিলা"),
    _t("Mouza map showing the plot and its boundaries", "দাগ ও সীমানা চিহ্নিত মৌজা ম্যাপ"),
    _t("Seller's National ID card", "বিক্রেতার জাতীয় পরিচয়পত্র"),
]

CONDITIONAL_DOCUMENTS = {
    "MUTATION_MISSING": _t("Succession (warish) certificate and mutation papers", "ওয়ারিশ সনদ ও নামজারির কাগজপত্র"),
    "OVER_SELLING": _t("Registered partition deed (bontonnama) or consent of all co-sharers", "নিবন্ধিত বণ্টননামা অথবা সকল শরিকের সম্মতি"),
    "PRE_EMPTION": _t("Written no-objection from co-sharers", "শরিকদের লিখিত অনাপত্তিপত্র"),
    "POA_SALE": _t("Original registered power of attorney", "মূল নিবন্ধিত আমমোক্তারনামা"),
    "POA_INVALID": _t("A fresh registered power of attorney, or the owner in person", "নতুন নিবন্ধিত আমমোক্তারনামা, অথবা মালিক নিজে"),
    "MORTGAGE": _t("Loan clearance and mortgage release letter from the lender", "ঋণ পরিশোধ ও বন্ধক মুক্তির পত্র"),
    "LITIGATION": _t("Certified copy of the case file and latest order", "মামলার নথি ও সর্বশেষ আদেশের সার্টিফায়েড কপি"),
    "TRANSFER_INJUNCTION": _t("Court order vacating the injunction", "নিষেধাজ্ঞা প্রত্যাহারের আদালত আদেশ"),
    "PRIOR_BAINANAMA": _t("Registered cancellation of the earlier bainanama", "আগের বায়নানামার নিবন্ধিত বাতিলনামা"),
    "MINOR_INTEREST": _t("Court permission order for sale of the minor's share", "নাবালকের অংশ বিক্রির আদালতের অনুমতি আদেশ"),
    "TITLE_CHAIN_BREAK": _t("Deed explaining the ownership change between surveys", "জরিপের মাঝে মালিকানা পরিবর্তনের দলিল"),
}

BASE_STEPS = [
    _t("Verify the khatian and mutation status at the AC Land office or the official e-porcha service.",
       "এসি ল্যান্ড অফিস বা সরকারি ই-পর্চা সেবায় খতিয়ান ও নামজারির অবস্থা যাচাই করুন।"),
    _t("Search the Sub-Registry Office records for all deeds on this Dag for the last 25 years.",
       "সাব-রেজিস্ট্রি অফিসে গত ২৫ বছরের এই দাগের সকল দলিল তল্লাশি করুন।"),
    _t("Visit the land and confirm who is in possession.", "সরেজমিনে জমি দেখে দখল কার তা নিশ্চিত হন।"),
    _t("Have a land lawyer review all documents before paying any advance.",
       "অগ্রিম টাকা দেওয়ার আগে একজন ভূমি আইনজীবী দিয়ে সব কাগজ যাচাই করান।"),
]

SITE_VISIT = [
    _t("Who is in physical possession? Is anyone living on or cultivating the land?", "জমি কার দখলে? কেউ কি বসবাস বা চাষাবাদ করছেন?"),
    _t("Do the boundaries (chouhoddi) match the deed and mouza map?", "চৌহদ্দি কি দলিল ও মৌজা ম্যাপের সাথে মেলে?"),
    _t("Ask neighbours about disputes, other buyers or pending cases.", "প্রতিবেশীদের কাছে বিরোধ, অন্য ক্রেতা বা মামলার কথা জিজ্ঞেস করুন।"),
    _t("Is there legal access (road or path) to the plot?", "জমিতে যাওয়ার বৈধ রাস্তা আছে কি?"),
    _t("Any signboard of a government project, bank or court on the land?", "জমিতে কোনো সরকারি প্রকল্প, ব্যাংক বা আদালতের সাইনবোর্ড আছে কি?"),
]

SUMMARY = {
    "LOW": _t("No serious problem was found in the available records. Complete the normal checks below before buying.",
              "প্রাপ্ত রেকর্ডে গুরুতর কোনো সমস্যা পাওয়া যায়নি। কেনার আগে নিচের সাধারণ যাচাইগুলো সম্পন্ন করুন।"),
    "MEDIUM": _t("Some risks were found. Resolve each issue below before paying any money.",
                 "কিছু ঝুঁকি পাওয়া গেছে। টাকা দেওয়ার আগে নিচের প্রতিটি সমস্যার সমাধান করুন।"),
    "HIGH": _t("Serious risks were found. Do not proceed without official verification and legal advice.",
               "গুরুতর ঝুঁকি পাওয়া গেছে। সরকারি যাচাই ও আইনি পরামর্শ ছাড়া এগোবেন না।"),
}


def build(flags: list[dict], role: str, level: str) -> dict:
    codes = [f["code"] for f in flags]
    documents = list(BASE_DOCUMENTS)
    for code in codes:
        doc = CONDITIONAL_DOCUMENTS.get(code)
        if doc and doc not in documents:
            documents.append(doc)

    steps = [f["action"] for f in flags] + BASE_STEPS
    questions = [f["seller_question"] for f in flags] or [
        _t("Can you show the original deed, mutation khatian and latest tax receipt?",
           "মূল দলিল, নামজারি খতিয়ান ও সর্বশেষ কর পরিশোধের দাখিলা দেখাতে পারবেন কি?"),
    ]

    top = [f["title"] for f in flags[:3]]
    if top:
        summary = _t(
            SUMMARY[level]["en"] + " Main issues: " + "; ".join(t["en"] for t in top) + ".",
            SUMMARY[level]["bn"] + " প্রধান সমস্যা: " + "; ".join(t["bn"] for t in top) + "।",
        )
    else:
        summary = SUMMARY[level]

    return {
        "summary": summary,
        "documents": documents,
        "next_steps": steps,
        "seller_questions": questions,
        "site_visit": SITE_VISIT,
    }
