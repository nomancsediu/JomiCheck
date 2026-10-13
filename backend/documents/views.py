import logging

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, throttle_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from verification.assistant import llm_configured

from .extract import ExtractionError, extract

logger = logging.getLogger(__name__)


class ExtractThrottle(AnonRateThrottle):
    rate = "10/minute"


def _error(en, bn, code):
    return Response({"detail": en, "detail_bn": bn}, status=code)


@api_view(["POST"])
@parser_classes([MultiPartParser])
@throttle_classes([ExtractThrottle])
def extract_document(request):
    if not llm_configured():
        return _error("Document reading needs the AI model. Set LLM_* in backend/.env.",
                      "ডকুমেন্ট পড়তে AI মডেল লাগবে। backend/.env-এ LLM সেটিং দিন।",
                      status.HTTP_503_SERVICE_UNAVAILABLE)
    upload = request.FILES.get("file")
    if not upload:
        return _error("Choose a file to upload.", "আপলোডের জন্য একটি ফাইল বেছে নিন।", status.HTTP_400_BAD_REQUEST)
    try:
        return Response(extract(upload.read(), upload.content_type))
    except ExtractionError as exc:
        return _error(str(exc), exc.message_bn, status.HTTP_422_UNPROCESSABLE_ENTITY)
    except Exception:
        logger.exception("Document extraction failed")
        return _error("The AI model could not read the document. Try again or enter the details manually.",
                      "AI মডেল ডকুমেন্টটি পড়তে পারেনি। আবার চেষ্টা করুন বা নিজে তথ্য লিখুন।",
                      status.HTTP_502_BAD_GATEWAY)
