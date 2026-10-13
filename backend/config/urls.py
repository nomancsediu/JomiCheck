from django.contrib import admin
from django.urls import include, path

from land import views as land_views
from reports import views as report_views
from verification import views as verification_views

api = [
    path("locations/", land_views.locations),
    path("mouzas/<int:mouza_id>/plots/", land_views.mouza_plots),
    path("demo-cases/", land_views.demo_cases),
    path("verify/", verification_views.verify_plot),
    path("inheritance/", verification_views.inheritance),
    path("reports/<str:public_id>/", report_views.report_detail),
    path("reports/<str:public_id>/verify/", report_views.report_verify),
    path("reports/<str:public_id>/ask/", report_views.report_ask),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api)),
]
