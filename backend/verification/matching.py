import re

from rapidfuzz import fuzz

MATCH_THRESHOLD = 85

_PREFIXES_EN = r"\b(md|mohammad|mohammed|muhammad|mohd|mst|mosammat|mrs|mr|haji|hazi|alhaj|sk)\b\.?"
_PREFIXES_BN = r"(মোঃ|মো:|মোহাম্মদ|মুহাম্মদ|মোছাঃ|মোসাম্মৎ|মোসাঃ|হাজী|আলহাজ্ব|আলহাজ)"


def normalize(name: str) -> str:
    name = (name or "").lower()
    name = re.sub(_PREFIXES_EN, " ", name)
    name = re.sub(_PREFIXES_BN, " ", name)
    # Explicit punctuation list: \W would also strip Bangla vowel signs.
    name = re.sub(r"[.,:;'\"()\[\]/\\\-_]", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def name_score(query: str, person) -> int:
    q = normalize(query)
    if not q:
        return 0
    return int(max(
        fuzz.token_sort_ratio(q, normalize(person.name_en)),
        fuzz.token_sort_ratio(q, normalize(person.name_bn)),
    ))


def best_match(query: str, people):
    best, best_score = None, 0
    for person in people:
        score = name_score(query, person)
        if score > best_score:
            best, best_score = person, score
    if best_score >= MATCH_THRESHOLD:
        return best, best_score
    return None, best_score
