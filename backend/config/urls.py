from django.contrib import admin
from django.urls import include, path

from costs import views as cost_views
from documents import views as document_views
from land import views as land_views
from reports import views as report_views
from verification import views as verification_views
from watch import views as watch_views

api = [
    path("locations/", land_views.locations),
    path("mouzas/<int:mouza_id>/plots/", land_views.mouza_plots),
    path("mouzas/<int:mouza_id>/map/", land_views.mouza_map),
    path("demo-cases/", land_views.demo_cases),
    path("verify/", verification_views.verify_plot),
    path("inheritance/", verification_views.inheritance),
    path("costs/estimate/", cost_views.cost_estimate),
    path("documents/extract/", document_views.extract_document),
    path("documents/check/", document_views.check_uploaded),
    path("watch/", watch_views.watches),
    path("watch/<int:watch_id>/", watch_views.stop_watching),
    path("reports/<str:public_id>/", report_views.report_detail),
    path("reports/<str:public_id>/verify/", report_views.report_verify),
    path("reports/<str:public_id>/ask/", report_views.report_ask),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api)),
]
