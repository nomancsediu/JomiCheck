from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["public_id", "created_at", "plot_label", "seller_name", "score", "level"]
    list_filter = ["level"]
    search_fields = ["public_id", "plot_label", "seller_name"]
    readonly_fields = ["public_id", "created_at", "sha256", "result"]
