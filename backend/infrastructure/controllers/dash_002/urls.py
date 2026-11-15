from django.urls import path

from infrastructure.controllers.dash_002.dash_002 import CardsAndGraph, ProcessOverview, OperationalStatus, DailyReport, \
    AreaFilter

urlpatterns = [
    # add url paths here
    path("section-one", CardsAndGraph.as_view(), name="cards-and-graph"),
    path("process-overview-data", ProcessOverview.as_view(), name="process-overview-data"),
    path("operational-status-data", OperationalStatus.as_view(), name="operational-status-data"),
    path("daily-report-data", DailyReport.as_view(), name="operational-status-data"),
    path("area-filter", AreaFilter.as_view(), name="area-filter"),
]