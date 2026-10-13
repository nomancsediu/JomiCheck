"""
Read a khatian, porcha or deed image with the configured vision LLM (Gemma) and
turn it into structured fields the verification form can use.

Uploaded files are processed in memory and never stored.
"""
import io
import json
import re
from decimal import Decimal, InvalidOperation

from rapidfuzz import fuzz

from land.models import Mouza, Plot
from verification.assistant import chat

MAX_BYTES = 8 * 1024 * 1024
# About 10 s on Google AI Studio with minimal thinking; slower OpenAI-compatible servers need more.
EXTRACT_TIMEOUT = 90
MAX_SIDE = 2000
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
PDF_TYPE = "application/pdf"

UNIT_TO_ACRE = {
    "acre": Decimal("1"),
    "decimal": Decimal("0.01"),
    "shotangsho": Decimal("0.01"),
    "katha": Decimal("720") / Decimal("43560"),
    "bigha": Decimal("14400") / Decimal("43560"),
    "ojutangsho": Decimal("0.0001"),
}
# The model sometimes answers the unit in Bangla, occasionally misspelled (e.g. "শতংশ").
UNIT_ALIASES = {
    "একর": "acre", "শত": "decimal", "ডেসিমেল": "decimal", "কাঠা": "katha", "বিঘা": "bigha", "অযুত": "ojutangsho",
}

_BN_TO_ASCII = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

PROMPT = """You are reading a scanned Bangladeshi land document (khatian / porcha / mutation khatian / deed / land tax receipt).
Extract the fields below and reply with ONLY one JSON object, no markdown, no explanation.
Write every number with English digits (convert Bangla digits). Use null when a field is not visible.
Do not guess: copy names exactly as written, in the script they are written in.

{
  "document_type": "khatian" | "mutation_khatian" | "deed" | "tax_receipt" | "other",
  "survey": "CS" | "SA" | "RS" | "BS" | "NAMJARI" | null,
  "district": string | null,
  "upazila": string | null,
  "mouza": string | null,
  "jl_no": string | null,
  "khatian_no": string | null,
  "mutation_case_no": string | null,
  "owners": [{"name": string, "father_name": string | null, "share": string | null}],
  "plots": [{"dag_no": string, "land_class": string | null, "area": string | null,
             "area_unit": "acre" | "decimal" | "katha" | "bigha" | "ojutangsho" | null}],
  "deed": {"deed_no": string | null, "registration_date": string | null, "sub_registry_office": string | null,
           "sellers": [string], "buyers": [string], "price_bdt": string | null} | null,
  "tax_receipt": {"holding_no": string | null, "paid_upto_year": string | null, "owner_name": string | null} | null,
  "warnings": [string]
}

For a deed fill "deed" (sellers are the donors/transferors, buyers the recipients) and list the sold land in "plots".
Copy dates exactly as written on the document (e.g. 14-06-2015); do not reorder them.
Copy each area number exactly as written with the unit written next to it (e.g. "৩০ শতাংশ" gives area "30", area_unit "decimal"); never convert units yourself.
For a land development tax receipt (dakhila) fill "tax_receipt"; "paid_upto_year" is the last year the tax covers.
Leave "deed" and "tax_receipt" null for other documents.

Put anything unclear, damaged or hard to read in "warnings"."""


class ExtractionError(Exception):
    def __init__(self, message: str, message_bn: str):
        super().__init__(message)
        self.message_bn = message_bn


def to_jpeg(data: bytes, content_type: str) -> bytes:
    """Return the document as a JPEG; PDFs are rendered from their first page."""
    from PIL import Image

    if content_type == PDF_TYPE:
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(data)
        if len(pdf) == 0:
            raise ExtractionError("The PDF has no pages.", "PDF-এ কোনো পৃষ্ঠা নেই।")
        image = pdf[0].render(scale=2).to_pil()
    elif content_type in IMAGE_TYPES:
        try:
            image = Image.open(io.BytesIO(data))
            image.load()
        except Exception as exc:
            raise ExtractionError("The image could not be read.", "ছবিটি পড়া যায়নি।") from exc
    else:
        raise ExtractionError("Upload a JPG, PNG, WEBP or PDF file.", "JPG, PNG, WEBP বা PDF ফাইল দিন।")

    image = image.convert("RGB")
    image.thumbnail((MAX_SIDE, MAX_SIDE))
    out = io.BytesIO()
    image.save(out, format="JPEG", quality=88)
    return out.getvalue()


def parse_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ExtractionError("The model did not return structured data.", "মডেল থেকে কাঠামোবদ্ধ তথ্য পাওয়া যায়নি।")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ExtractionError("The model returned invalid data.", "মডেল থেকে ভুল ফরম্যাটের তথ্য এসেছে।") from exc


def _clean(value) -> str:
    return str(value).translate(_BN_TO_ASCII).strip() if value not in (None, "") else ""


def _to_acre(area: str, unit: str | None) -> str | None:
    # The area may carry its own unit, e.g. "৩৩ শতাংশ"; a unit written there wins over area_unit.
    match = re.match(r"\s*([\d,]*\.?\d+)\s*(.*)", _clean(area))
    if not match:
        return None
    try:
        value = Decimal(match.group(1).replace(",", ""))
    except InvalidOperation:
        return None
    key = _unit_key(match.group(2) or unit)
    if key == "decimal" and value < 1:
        # No real plot is under one decimal (435 sq ft); the model has already converted to acres.
        key = "acre"
    acre = value * UNIT_TO_ACRE[key]
    return f"{acre.quantize(Decimal('0.0001')).normalize():f}"


def _unit_key(unit: str | None) -> str:
    unit = (unit or "").strip().lower()
    if unit in UNIT_TO_ACRE:
        return unit
    for prefix, key in UNIT_ALIASES.items():
        if unit.startswith(prefix):
            return key
    return "acre"


def _name_score(a: str, b_en: str, b_bn: str) -> float:
    a = a.lower().strip()
    return max(fuzz.ratio(a, b_en.lower()), fuzz.ratio(a, b_bn))


def match_location(fields: dict) -> dict | None:
    """Find the mouza in our records using the mouza name, JL number, upazila and district."""
    name = _clean(fields.get("mouza"))
    jl = _clean(fields.get("jl_no"))
    if not name and not jl:
        return None
    best, best_score = None, 0.0
    for mouza in Mouza.objects.select_related("upazila__district"):
        score = _name_score(name, mouza.name_en, mouza.name_bn) if name else 0
        if jl and jl == str(mouza.jl_no):
            score += 40
        if fields.get("upazila"):
            score += 0.2 * _name_score(_clean(fields["upazila"]), mouza.upazila.name_en, mouza.upazila.name_bn)
        if fields.get("district"):
            score += 0.1 * _name_score(_clean(fields["district"]), mouza.upazila.district.name_en,
                                       mouza.upazila.district.name_bn)
        if score > best_score:
            best, best_score = mouza, score
    if not best or best_score < 70:
        return None
    return {
        "district_id": best.upazila.district_id,
        "upazila_id": best.upazila_id,
        "mouza_id": best.id,
        "mouza": {"en": best.name_en, "bn": best.name_bn},
        "jl_no": best.jl_no,
    }


def normalise(raw: dict) -> dict:
    plots = []
    for p in raw.get("plots") or []:
        dag = _clean(p.get("dag_no"))
        if not dag:
            continue
        plots.append({
            "dag_no": dag,
            "land_class": p.get("land_class") or "",
            "area_acre": _to_acre(p.get("area"), p.get("area_unit")) if p.get("area") else None,
        })
    owners = [{
        "name": (o.get("name") or "").strip(),
        "father_name": (o.get("father_name") or "").strip(),
        "share": _clean(o.get("share")),
    } for o in raw.get("owners") or [] if (o.get("name") or "").strip()]

    deed = raw.get("deed") or None
    if deed:
        deed = {
            "deed_no": _clean(deed.get("deed_no")),
            "registration_date": _clean(deed.get("registration_date")),
            "sub_registry_office": (deed.get("sub_registry_office") or "").strip(),
            "sellers": [str(n).strip() for n in deed.get("sellers") or [] if str(n).strip()],
            "buyers": [str(n).strip() for n in deed.get("buyers") or [] if str(n).strip()],
            "price_bdt": re.sub(r"[^\d]", "", _clean(deed.get("price_bdt"))),
        }
    tax = raw.get("tax_receipt") or None
    if tax:
        tax = {
            "holding_no": _clean(tax.get("holding_no")),
            "paid_upto_year": _clean(tax.get("paid_upto_year")),
            "owner_name": (tax.get("owner_name") or "").strip(),
        }

    fields = {
        "document_type": raw.get("document_type") or "other",
        "survey": raw.get("survey"),
        "district": raw.get("district") or "",
        "upazila": raw.get("upazila") or "",
        "mouza": raw.get("mouza") or "",
        "jl_no": _clean(raw.get("jl_no")),
        "khatian_no": _clean(raw.get("khatian_no")),
        "mutation_case_no": _clean(raw.get("mutation_case_no")),
        "owners": owners,
        "plots": plots,
        "deed": deed,
        "tax_receipt": tax,
        "warnings": [str(w) for w in raw.get("warnings") or []],
    }
    location = match_location(fields)
    if location:
        known = set(Plot.objects.filter(mouza_id=location["mouza_id"]).values_list("dag_no", flat=True))
        for p in plots:
            p["found"] = p["dag_no"] in known
    return {"fields": fields, "location": location}


def extract(data: bytes, content_type: str) -> dict:
    if len(data) > MAX_BYTES:
        raise ExtractionError("The file is larger than 8 MB.", "ফাইলটি ৮ MB-এর বেশি।")
    image = (to_jpeg(data, content_type), "image/jpeg")
    reply = chat(PROMPT, "Read this document.", image=image, temperature=0, timeout=EXTRACT_TIMEOUT,
                 json_output=True)
    return normalise(parse_json(reply))
