from django.contrib import admin

from .models import PlotWatch


@admin.register(PlotWatch)
class PlotWatchAdmin(admin.ModelAdmin):
    list_display = ["plot", "buyer_token", "report_id", "created_at"]
    readonly_fields = ["snapshot"]
