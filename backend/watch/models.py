from django.db import models

from land.models import Plot


class PlotWatch(models.Model):
    """A buyer asked to be alerted when anything new is recorded on a plot they checked."""
    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name="watches")
    buyer_token = models.CharField(max_length=64)
    report_id = models.CharField(max_length=12, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    snapshot = models.JSONField(help_text="IDs of the records that existed when watching started")

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("plot", "buyer_token")]

    def __str__(self):
        return f"Watch on {self.plot}"
