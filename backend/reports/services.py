from . import integrity
from .models import Report


def create_report(result: dict) -> Report:
    plot = result["plot"]
    report = Report.objects.create(
        plot_label=f"Dag {plot['dag_no']}, {plot['mouza']['en']}, {plot['upazila']['en']}, {plot['district']['en']}",
        seller_name=result["input"]["seller_name"],
        score=result["score"],
        level=result["level"],
        result=result,
    )
    report.refresh_from_db()
    integrity.seal(report)
    return report


def serialize_report(report: Report, request=None) -> dict:
    url = integrity.verify_url(report, request)
    return {
        "id": report.public_id,
        "created_at": report.created_at.isoformat(),
        "sha256": report.sha256,
        "verify_url": url,
        "qr_svg": integrity.qr_svg(url),
        "result": report.result,
    }
