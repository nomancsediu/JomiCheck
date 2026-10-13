"""
Read a khatian, porcha or deed image with the configured vision LLM (Gemma) and
turn it into structured fields the verification form can use.

Uploaded files are processed in memory and never stored.
"""
import base64
import io
import json
import re
from decimal import Decimal, InvalidOperation

from rapidfuzz import fuzz

from land.models import Mouza, Plot
from verification.assistant import chat

MAX_BYTES = 8 * 1024 * 1024
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

_BN_TO_ASCII = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

PROMPT = """You are reading a scanned Bangladeshi land document (khatian / porcha / mutation khatian / deed).
Extract the fields below and reply with ONLY one JSON object, no markdown, no explanation.
Write every number with English digits (convert Bangla digits). Use null when a field is not visible.
Do not guess: copy names exactly as written, in the script they are written in.

{
  "document_type": "khatian" | "mutation_khatian" | "deed" | "other",
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
  "warnings": [string]
}

Put anything unclear, damaged or hard to read in "warnings"."""


class ExtractionError(Exception):
    def __init__(self, message: str, message_bn: str):
        super().__init__(message)
        self.message_bn = message_bn


def to_image_data_url(data: bytes, content_type: str) -> str:
    """Return a JPEG/PNG data URL; PDFs are rendered from their first page."""
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
    return "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode("ascii")


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
    try:
        value = Decimal(_clean(area).replace(",", ""))
    except (InvalidOperation, ValueError):
        return None
    acre = value * UNIT_TO_ACRE.get((unit or "acre").lower(), Decimal("1"))
    return f"{acre.quantize(Decimal('0.0001')).normalize():f}"


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
    image = to_image_data_url(data, content_type)
    reply = chat(PROMPT, "Read this document.", image_data_url=image, temperature=0)
    return normalise(parse_json(reply))
