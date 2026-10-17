"""Tamper-evidence for verification reports: canonical SHA-256 hash and QR code."""

import hashlib
import hmac
import json

import qrcode
import qrcode.image.svg
from django.conf import settings


def canonical_payload(public_id: str, created_at_iso: str, result: dict) -> bytes:
    body = {"id": public_id, "created_at": created_at_iso, "result": result}
    return json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def compute_hash(report) -> str:
    return hashlib.sha256(
        canonical_payload(report.public_id, report.created_at.isoformat(), report.result)
    ).hexdigest()


def seal(report) -> None:
    report.sha256 = compute_hash(report)
    report.save(update_fields=["sha256"])


def check(report, presented_hash: str) -> dict:
    stored_ok = hmac.compare_digest(compute_hash(report), report.sha256)
    presented_ok = bool(presented_hash) and hmac.compare_digest(presented_hash.lower(), report.sha256)
    if not stored_ok:
        return {"authentic": False, "reason": "registry_record_modified"}
    if not presented_ok:
        return {"authentic": False, "reason": "hash_mismatch"}
    return {"authentic": True, "reason": "match"}


def verify_url(report, request=None) -> str:
    base = settings.FRONTEND_URL or (request.build_absolute_uri("/") if request else "")
    return f"{base.rstrip('/')}/verify-report/{report.public_id}?h={report.sha256}"


def qr_svg(data: str) -> str:
    img = qrcode.make(data, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2)
    return img.to_string(encoding="unicode")
