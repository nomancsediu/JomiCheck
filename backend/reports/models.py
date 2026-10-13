import uuid

from django.db import models


def _public_id():
    return uuid.uuid4().hex[:12].upper()


class Report(models.Model):
    public_id = models.CharField(max_length=12, unique=True, default=_public_id, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    plot_label = models.CharField(max_length=160)
    seller_name = models.CharField(max_length=120)
    score = models.PositiveSmallIntegerField()
    level = models.CharField(max_length=10)
    result = models.JSONField()
    sha256 = models.CharField(max_length=64, editable=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report {self.public_id} — {self.plot_label} — {self.level}"
